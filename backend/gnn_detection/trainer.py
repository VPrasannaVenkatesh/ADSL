"""
GNN Training Pipeline.
Trains the GATv2 money mule detector on the live transaction graph.

Usage (from backend/):
    python -m gnn_detection.trainer

Features:
  - Early stopping (patience=18 epochs)
  - L2 weight decay
  - Class-weighted cross-entropy (MULE is rare → upweighted)
  - LR scheduler (StepLR)
  - Saves best model to backend/models/gnn_mule_detector.pt
  - Full classification report (per-class precision/recall/F1)
  - Saves gnn_model_metadata.json
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim.lr_scheduler import StepLR
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_recall_fscore_support,
    f1_score,
)

from .config import (
    MODEL_PATH,
    METADATA_PATH,
    GNN_MODEL_TYPE,
    GNN_MODEL_VERSION,
    GNN_HYPERPARAMS,
    NODE_FEATURE_NAMES,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_DIM,
    NUM_CLASSES,
    LABEL_NAMES,
    LABEL_NORMAL,
    LABEL_SUSPICIOUS,
    LABEL_MULE,
    DATASET_SPLITS,
)
from .model import build_model
from .dataset_builder import build_dataset


def _compute_class_weights(labels_tensor: torch.Tensor, num_classes: int = NUM_CLASSES) -> torch.Tensor:
    """Computes inverse-frequency class weights for imbalanced datasets."""
    counts = torch.bincount(labels_tensor, minlength=num_classes).float()
    counts = torch.clamp(counts, min=1.0)
    total  = counts.sum()
    weights = total / (num_classes * counts)
    return weights


def _evaluate(
    model:       nn.Module,
    data,
    device:      torch.device,
) -> Tuple[float, float, List[int], List[int]]:
    """
    Runs model evaluation on a Data object.
    Returns (loss, accuracy, y_true, y_pred).
    """
    model.eval()
    with torch.no_grad():
        x          = data.x.to(device)
        edge_index = data.edge_index.to(device)
        y          = data.y.to(device)

        logits = model(x, edge_index)
        loss   = F.cross_entropy(logits, y)
        preds  = logits.argmax(dim=-1)

        y_true = y.cpu().tolist()
        y_pred = preds.cpu().tolist()
        acc    = accuracy_score(y_true, y_pred)

    return float(loss.item()), acc, y_true, y_pred


def train_gnn(
    graph=None,
    model_type: str = GNN_MODEL_TYPE,
    epochs: int     = GNN_HYPERPARAMS["epochs"],
    patience: int   = GNN_HYPERPARAMS["early_stop_patience"],
    lr: float       = GNN_HYPERPARAMS["learning_rate"],
    weight_decay: float = GNN_HYPERPARAMS["weight_decay"],
    verbose: bool   = True,
) -> Dict[str, Any]:
    """
    Full GNN training pipeline.

    1. Builds dataset from live NetworkX graph.
    2. Trains GATv2 with early stopping.
    3. Evaluates on validation + test sets.
    4. Saves model checkpoint and metadata.

    Returns:
        Dict with training metrics, validation metrics, and test metrics.
    """
    device = torch.device("cpu")   # CPU-only for now

    print("=" * 68)
    print("  GNN Mule Detector — Training Pipeline")
    print(f"  Model: {model_type} | Device: {device}")
    print("=" * 68)

    # ── Step 1: Build Dataset ────────────────────────────────────────────────
    t0 = time.time()
    dataset = build_dataset(graph)

    if dataset["train_data"] is None:
        print("[ERROR] Training data unavailable — run the simulator first to generate transactions.")
        return {"error": "Insufficient training data. Run simulator first."}

    train_data = dataset["train_data"]
    val_data   = dataset["val_data"]   or train_data
    test_data  = dataset["test_data"]  or train_data
    aug_data   = dataset["aug_data"]

    print(f"[Dataset] Train nodes: {train_data.num_nodes} | Val: {val_data.num_nodes} | Test: {test_data.num_nodes}")
    print(f"[Dataset] Augmented subgraphs: {len(aug_data)}")
    print(f"[Dataset] Label distribution: {dataset['label_dist']}")

    # ── Step 2: Build Model ──────────────────────────────────────────────────
    model = build_model(model_type).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[Model] {model_type} | Parameters: {total_params:,}")

    # Compute class weights from training labels
    class_weights = _compute_class_weights(train_data.y)
    print(f"[Model] Class weights: NORMAL={class_weights[0]:.3f}, SUSPICIOUS={class_weights[1]:.3f}, MULE={class_weights[2]:.3f}")

    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = StepLR(optimizer, step_size=GNN_HYPERPARAMS["scheduler_step"], gamma=GNN_HYPERPARAMS["scheduler_gamma"])

    # ── Step 3: Training Loop ────────────────────────────────────────────────
    best_val_loss  = float("inf")
    best_val_f1    = 0.0
    best_state     = None
    patience_count = 0

    train_losses = []
    val_losses   = []
    val_f1s      = []

    x_train = train_data.x.to(device)
    ei_train = train_data.edge_index.to(device)
    y_train = train_data.y.to(device)

    # All augmented data
    aug_pairs = [(d.x.to(device), d.edge_index.to(device), d.y.to(device)) for d in aug_data if d is not None]

    print(f"\n{'Epoch':>6}  {'Train Loss':>11}  {'Val Loss':>9}  {'Val Acc':>8}  {'Val F1':>8}  {'LR':>10}")
    print("-" * 65)

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()

        # Main training graph
        logits = model(x_train, ei_train)
        loss   = criterion(logits, y_train)

        # Add augmented subgraph losses
        aug_loss_total = torch.tensor(0.0, device=device)
        if aug_pairs:
            aug_sample = aug_pairs[:8]   # Use first 8 augmented graphs per epoch
            for ax, aei, ay in aug_sample:
                al = model(ax, aei)
                aug_loss_total = aug_loss_total + F.cross_entropy(al, ay, weight=class_weights.to(device))
            loss = loss + (aug_loss_total / len(aug_sample)) * 0.4   # Weighted augmentation

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        train_losses.append(float(loss.item()))

        # ── Validation ────────────────────────────────────────────────────
        val_loss, val_acc, vyt, vyp = _evaluate(model, val_data, device)
        val_f1 = f1_score(vyt, vyp, average="macro", zero_division=0)
        val_losses.append(val_loss)
        val_f1s.append(val_f1)

        current_lr = optimizer.param_groups[0]["lr"]

        if verbose and (epoch % 10 == 0 or epoch == 1):
            print(f"{epoch:>6}  {loss.item():>11.5f}  {val_loss:>9.5f}  {val_acc:>8.4f}  {val_f1:>8.4f}  {current_lr:>10.6f}")

        # Early stopping: track best val F1 (more informative than val loss for imbalanced data)
        if val_f1 > best_val_f1:
            best_val_f1   = val_f1
            best_val_loss = val_loss
            best_state    = {k: v.clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
            if patience_count >= patience:
                print(f"\n  [Early Stop] Epoch {epoch}: no improvement for {patience} epochs.")
                break

    print("-" * 65)
    print(f"  Best Val F1:   {best_val_f1:.4f}")
    print(f"  Best Val Loss: {best_val_loss:.5f}")

    # ── Step 4: Load Best Model + Final Evaluation ───────────────────────────
    if best_state:
        model.load_state_dict(best_state)

    # Test set evaluation
    _, test_acc, y_true_test, y_pred_test = _evaluate(model, test_data, device)
    test_f1 = f1_score(y_true_test, y_pred_test, average="macro", zero_division=0)

    prec_per, rec_per, f1_per, sup_per = precision_recall_fscore_support(
        y_true_test, y_pred_test, average=None, labels=[0, 1, 2], zero_division=0
    )

    report = classification_report(
        y_true_test, y_pred_test,
        target_names=["NORMAL", "SUSPICIOUS", "MULE"],
        zero_division=0,
    )
    print("\n  [Test Set Classification Report]")
    print(report)

    # Val set metrics
    _, val_acc_final, y_true_val, y_pred_val = _evaluate(model, val_data, device)
    val_f1_final = f1_score(y_true_val, y_pred_val, average="macro", zero_division=0)
    val_prec, val_rec, _, _ = precision_recall_fscore_support(
        y_true_val, y_pred_val, average="macro", zero_division=0
    )

    elapsed = time.time() - t0

    # ── Step 5: Save Model ───────────────────────────────────────────────────
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    torch.save({
        "model_state_dict": best_state or model.state_dict(),
        "model_type":       model_type,
        "node_feature_dim": NODE_FEATURE_DIM,
        "edge_feature_dim": EDGE_FEATURE_DIM,
        "num_classes":      NUM_CLASSES,
        "hyperparams":      GNN_HYPERPARAMS,
        "version":          GNN_MODEL_VERSION,
    }, MODEL_PATH)
    print(f"\n  [Saved] Model -> {MODEL_PATH}")

    # ── Step 6: Save Metadata ─────────────────────────────────────────────────
    per_class_metrics = {}
    for i, class_name in enumerate(["NORMAL", "SUSPICIOUS", "MULE"]):
        per_class_metrics[class_name] = {
            "precision": float(prec_per[i]) if len(prec_per) > i else 0.0,
            "recall":    float(rec_per[i])  if len(rec_per)  > i else 0.0,
            "f1_score":  float(f1_per[i])   if len(f1_per)   > i else 0.0,
            "support":   int(sup_per[i])    if len(sup_per)   > i else 0,
        }

    metadata = {
        "model_version":    GNN_MODEL_VERSION,
        "model_type":       model_type,
        "architecture":     "GATv2Conv x 3 + Linear x 2",
        "feature_names":    NODE_FEATURE_NAMES,
        "node_feature_dim": NODE_FEATURE_DIM,
        "edge_feature_dim": EDGE_FEATURE_DIM,
        "num_classes":      NUM_CLASSES,
        "class_names":      ["NORMAL", "SUSPICIOUS", "MULE"],
        "training_date":    datetime.now().isoformat(),
        "training_time_sec": round(elapsed, 2),
        "training_samples": int(train_data.num_nodes),
        "val_samples":      int(val_data.num_nodes),
        "test_samples":     int(test_data.num_nodes),
        "augmented_subgraphs": len(aug_data),
        "hyperparams":      GNN_HYPERPARAMS,
        "label_distribution": dataset["label_dist"],
        "training_metrics": {
            "final_train_loss": float(train_losses[-1]) if train_losses else 0.0,
        },
        "validation_metrics": {
            "accuracy":  round(float(val_acc_final), 4),
            "f1_score":  round(float(val_f1_final), 4),
            "precision": round(float(val_prec), 4),
            "recall":    round(float(val_rec), 4),
        },
        "test_metrics": {
            "accuracy":  round(float(test_acc), 4),
            "f1_score":  round(float(test_f1), 4),
            "per_class": per_class_metrics,
        },
        "status": "TRAINED",
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  [Saved] Metadata -> {METADATA_PATH}")
    print("=" * 68)

    return metadata


if __name__ == "__main__":
    # Allow running as: python -m gnn_detection.trainer
    # from the backend/ directory
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = train_gnn(verbose=True)
    if "error" not in result:
        print(f"\nTraining complete!")
        print(f"  Test Accuracy:  {result['test_metrics']['accuracy']:.1%}")
        print(f"  Test F1 (macro): {result['test_metrics']['f1_score']:.4f}")
        print(f"  MULE F1:        {result['test_metrics']['per_class']['MULE']['f1_score']:.4f}")
