"""
Multi-Class XGBoost Model Trainer and Evaluator.
Trains an XGBClassifier on 4 granular risk classes:
  0: NORMAL, 1: SUSPICIOUS, 2: MULE_FLOW, 3: CRITICAL_FRAUD
Computes multi-class metrics, per-class F1, ranks feature importances, and persists artifacts.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    log_loss,
)
import xgboost as xgb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .config import (
    MODEL_PATH,
    METADATA_PATH,
    MODEL_VERSION,
    FEATURE_NAMES,
    RISK_CLASSES,
    NUM_CLASSES,
    XGBOOST_HYPERPARAMS,
)
from .dataset_generator import generate_training_dataset


def train_xgboost_model(sample_limit: int = 24000) -> Dict[str, Any]:
    """
    Orchestrates 4-class multi-category dataset generation, model training,
    multi-class evaluation, and artifact saving.
    """
    print("=" * 72)
    print(f"  Training High-Accuracy Multi-Class XGBoost Model [{MODEL_VERSION}]")
    print(f"  Target Classes ({NUM_CLASSES}): {', '.join(RISK_CLASSES)}")
    print("=" * 72)

    # 1. Generate Multi-Class Dataset
    X_df, y_arr = generate_training_dataset(sample_limit=sample_limit)

    # 2. Stratified Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y_arr, test_size=0.20, random_state=42, stratify=y_arr
    )

    hyperparams = dict(XGBOOST_HYPERPARAMS)

    print(f"[Trainer] Fitting XGBClassifier ({NUM_CLASSES} classes) on {len(X_train)} samples...")
    model = xgb.XGBClassifier(**hyperparams)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 3. Evaluate Multi-Class Performance
    y_pred_proba = model.predict_proba(X_test)
    y_pred = np.argmax(y_pred_proba, axis=1)

    acc = float(accuracy_score(y_test, y_pred))
    macro_prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    m_loss = float(log_loss(y_test, y_pred_proba))

    per_class_f1 = f1_score(y_test, y_pred, average=None, zero_division=0)
    per_class_metrics = {}
    for idx, name in enumerate(RISK_CLASSES):
        per_class_metrics[name] = {
            "class_id": idx,
            "f1_score": round(float(per_class_f1[idx]), 4),
            "test_support": int(np.sum(y_test == idx)),
        }

    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n[Trainer] Multi-Class Model Evaluation Results:")
    print(f"  Overall Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"  Macro F1 Score   : {macro_f1:.4f}")
    print(f"  Weighted F1      : {weighted_f1:.4f}")
    print(f"  Multi-Class Loss : {m_loss:.4f}")
    print("\n  Per-Class F1 Breakdown:")
    for name, pcm in per_class_metrics.items():
        print(f"    • {name:15}: F1={pcm['f1_score']:.4f} (Test samples: {pcm['test_support']})")

    # 4. Feature Importances
    importances = model.feature_importances_
    feat_importance_list = []
    for name, imp in zip(FEATURE_NAMES, importances):
        feat_importance_list.append({
            "feature": name,
            "importance": float(round(imp, 5))
        })
    feat_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    print("\n[Trainer] Top 8 Contributing Features:")
    for item in feat_importance_list[:8]:
        print(f"  - {item['feature']:30}: {item['importance']:.4f}")

    # 5. Persist Model & Metadata
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save_model(MODEL_PATH)
    print(f"\n[Trainer] Multi-Class Model saved successfully to {MODEL_PATH}")

    metadata = {
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now().isoformat(),
        "total_dataset_size": len(X_df),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "num_classes": NUM_CLASSES,
        "class_names": RISK_CLASSES,
        "metrics": {
            "accuracy": round(acc, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "log_loss": round(m_loss, 4),
            "per_class": per_class_metrics,
            "confusion_matrix": cm,
        },
        "top_features": feat_importance_list[:12],
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[Trainer] Metadata saved to {METADATA_PATH}")

    return metadata


if __name__ == "__main__":
    train_xgboost_model()
