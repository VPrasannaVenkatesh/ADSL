"""
GNN Inference Engine — Money Mule Account Predictor.
Loads the trained GATv2 model and runs real-time account-level and
network-level mule probability scoring on the live transaction graph.

Provides:
  - predict_account(account_id): single account GNN risk profile
  - predict_network(transaction_id): network around a transaction
  - GLOBAL_GNN_PREDICTOR: singleton for lifecycle pipeline integration
"""

import os
import json
import threading
from typing import Dict, Any, Optional, List

import torch
import torch.nn.functional as F
import networkx as nx

from .config import (
    MODEL_PATH,
    METADATA_PATH,
    GNN_MODEL_TYPE,
    GNN_MODEL_VERSION,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_DIM,
    NUM_CLASSES,
    LABEL_NORMAL,
    LABEL_SUSPICIOUS,
    LABEL_MULE,
    LABEL_NAMES,
    GNN_HYPERPARAMS,
    SUBGRAPH_CONFIG,
    mule_prob_to_risk_score,
    risk_score_to_level,
    GNN_TRIGGER_LEVELS,
)
from .model import build_model, GATv2MuleDetector
from .graph_features import build_pyg_tensors_from_graph
from .labels import get_network_pattern
from .explainability import generate_explanation


class GNNPredictor:
    """
    Singleton GNN inference engine.

    Thread-safe: All predictions are protected by a read lock.
    The model runs in evaluation mode (no gradient computation).
    """

    def __init__(self):
        self._model: Optional[torch.nn.Module] = None
        self._metadata: Dict[str, Any] = {}
        self._device = torch.device("cpu")
        self._lock   = threading.RLock()
        self._loaded = False

        # Try loading model at startup
        self._try_load_model()

    def _try_load_model(self) -> bool:
        """Loads model checkpoint if it exists. Returns True on success."""
        if not os.path.exists(MODEL_PATH):
            print(f"[GNN Predictor] Model not found at {MODEL_PATH}. Train first.")
            return False

        try:
            checkpoint = torch.load(MODEL_PATH, map_location=self._device, weights_only=False)
            model_type = checkpoint.get("model_type", GNN_MODEL_TYPE)
            model = build_model(model_type)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()
            model = model.to(self._device)

            with self._lock:
                self._model    = model
                self._loaded   = True

            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r") as f:
                    self._metadata = json.load(f)

            print(f"[GNN Predictor] Loaded {model_type} model from {MODEL_PATH}")
            return True

        except Exception as e:
            print(f"[GNN Predictor] Failed to load model: {e}")
            return False

    def reload_model(self) -> bool:
        """Reloads the model from disk (called after retraining)."""
        return self._try_load_model()

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._model is not None

    @property
    def model_metadata(self) -> Dict[str, Any]:
        return self._metadata

    def _subgraph_to_data(self, subgraph: nx.DiGraph):
        """Converts a NetworkX subgraph to PyG tensors."""
        tensors = build_pyg_tensors_from_graph(subgraph)
        if tensors["num_nodes"] < 1:
            return None, None

        x = torch.tensor(tensors["x"], dtype=torch.float, device=self._device)
        ei = tensors["edge_index"]
        if not ei[0]:
            n = tensors["num_nodes"]
            idx_list = list(range(n))
            edge_index = torch.tensor([idx_list, idx_list], dtype=torch.long, device=self._device)
        else:
            edge_index = torch.tensor(ei, dtype=torch.long, device=self._device)

        return x, edge_index, tensors["node_mapping"]

    def predict_account(
        self,
        account_id: str,
        graph_instance=None,
        depth: int = SUBGRAPH_CONFIG["max_hops"],
    ) -> Dict[str, Any]:
        """
        Runs GNN inference on the ego-subgraph around an account.

        Returns:
            {
                "account_id":          str,
                "classification":      "NORMAL" | "SUSPICIOUS" | "MULE",
                "mule_probability":    float [0.0–1.0],
                "suspicious_probability": float,
                "normal_probability":  float,
                "gnn_risk_score":      float [0–100],
                "risk_level":          str,
                "network_pattern":     str,
                "connected_accounts":  List[str],
                "confidence":          float,
                "explanation":         List[str],
                "model_loaded":        bool,
            }
        """
        if not self.is_loaded:
            return self._fallback_response(account_id, "Model not trained yet.")

        if graph_instance is None:
            from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
            graph_instance = GLOBAL_NETWORK_GRAPH

        with graph_instance._lock:
            if not graph_instance.graph.has_node(account_id):
                return self._fallback_response(account_id, "Account not in live graph.")

            # Extract ego-subgraph
            subgraph = graph_instance.get_connected_subgraph(
                account_id,
                depth=min(depth, SUBGRAPH_CONFIG["max_hops"])
            )

            # Limit subgraph size
            if subgraph.number_of_nodes() > SUBGRAPH_CONFIG["max_nodes"]:
                keep = list(subgraph.nodes())[:SUBGRAPH_CONFIG["max_nodes"]]
                subgraph = subgraph.subgraph(keep).copy()

            if subgraph.number_of_nodes() < 1:
                return self._fallback_response(account_id, "Empty subgraph.")

        # Build tensors
        result = self._subgraph_to_data(subgraph)
        if result[0] is None:
            return self._fallback_response(account_id, "Feature extraction failed.")

        x, edge_index, node_mapping = result

        # Run GNN inference
        with self._lock:
            with torch.no_grad():
                logits = self._model(x, edge_index)
                probs  = F.softmax(logits, dim=-1)   # [N, 3]

        # Find the index of the target account
        idx_to_account = {v: k for k, v in {i: node_mapping[i] for i in range(len(node_mapping))}.items()}
        account_idx = None
        for idx, acc in node_mapping.items():
            if acc == account_id:
                account_idx = idx
                break

        if account_idx is None:
            return self._fallback_response(account_id, "Account not found in tensor mapping.")

        # Extract probabilities for target account
        account_probs = probs[account_idx].cpu().tolist()   # [p_normal, p_suspicious, p_mule]
        p_normal  = float(account_probs[LABEL_NORMAL])
        p_susp    = float(account_probs[LABEL_SUSPICIOUS])
        p_mule    = float(account_probs[LABEL_MULE])

        # Classification
        class_idx      = int(torch.argmax(probs[account_idx]).item())
        classification = LABEL_NAMES[class_idx]
        confidence     = float(max(account_probs))

        # GNN Risk Score
        gnn_risk_score = mule_prob_to_risk_score(p_mule)
        risk_level     = risk_score_to_level(gnn_risk_score)

        # Network pattern
        label_int      = class_idx
        net_pattern    = get_network_pattern(subgraph, account_id, label_int)

        # Connected accounts
        connected = [n for n in subgraph.nodes() if n != account_id][:20]

        # Explanations
        explanation = generate_explanation(
            graph=subgraph,
            account_id=account_id,
            classification=classification,
            mule_probability=p_mule,
            gnn_risk_score=gnn_risk_score,
        )

        return {
            "account_id":              account_id,
            "classification":          classification,
            "mule_probability":        round(p_mule, 4),
            "suspicious_probability":  round(p_susp, 4),
            "normal_probability":      round(p_normal, 4),
            "gnn_risk_score":          gnn_risk_score,
            "risk_level":              risk_level,
            "network_pattern":         net_pattern,
            "connected_accounts":      connected,
            "connected_account_count": len(connected),
            "confidence":              round(confidence, 4),
            "explanation":             explanation,
            "model_loaded":            True,
            "model_version":           self._metadata.get("model_version", GNN_MODEL_VERSION),
        }

    def predict_network(
        self,
        transaction_id: str,
        graph_instance=None,
    ) -> Dict[str, Any]:
        """
        Runs GNN on the combined subgraph around both endpoints of a transaction.

        Returns:
            {
                "transaction_id":        str,
                "node_count":            int,
                "edge_count":            int,
                "node_classifications":  {account_id: {classification, gnn_risk_score, ...}},
                "mule_accounts":         List[str],
                "suspicious_accounts":   List[str],
                "network_pattern":       str,
                "network_risk_score":    float,
                "model_loaded":          bool,
            }
        """
        if not self.is_loaded:
            return {
                "transaction_id": transaction_id,
                "model_loaded": False,
                "error": "Model not trained yet."
            }

        if graph_instance is None:
            from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
            graph_instance = GLOBAL_NETWORK_GRAPH

        # Find the transaction edge in the graph
        sender_id   = None
        receiver_id = None
        with graph_instance._lock:
            if transaction_id in graph_instance.transactions_by_id:
                edge = graph_instance.transactions_by_id[transaction_id]
                sender_id   = edge.get("sender_account_id") or edge.get("sender")
                receiver_id = edge.get("receiver_account_id") or edge.get("receiver")

            if not sender_id or not receiver_id:
                # Search edges
                for u, v, d in graph_instance.graph.edges(data=True):
                    if d.get("transaction_id") == transaction_id:
                        sender_id   = u
                        receiver_id = v
                        break

        if not sender_id:
            return {
                "transaction_id": transaction_id,
                "model_loaded": True,
                "error": "Transaction not found in live graph."
            }

        # Build merged subgraph from both endpoints
        with graph_instance._lock:
            sender_sub   = graph_instance.get_connected_subgraph(sender_id,   depth=2)
            receiver_sub = graph_instance.get_connected_subgraph(receiver_id, depth=2)
            all_nodes    = set(sender_sub.nodes()) | set(receiver_sub.nodes())

            if len(all_nodes) > SUBGRAPH_CONFIG["max_nodes"]:
                all_nodes = set(list(all_nodes)[:SUBGRAPH_CONFIG["max_nodes"]])

            merged_sub = graph_instance.graph.subgraph(all_nodes).copy()

        if merged_sub.number_of_nodes() < 2:
            return {
                "transaction_id": transaction_id,
                "model_loaded": True,
                "node_count": 0, "edge_count": 0,
                "mule_accounts": [], "suspicious_accounts": [],
                "node_classifications": {}, "network_risk_score": 0.0,
                "network_pattern": "UNKNOWN",
            }

        # Build tensors
        tensors = build_pyg_tensors_from_graph(merged_sub)
        x = torch.tensor(tensors["x"], dtype=torch.float, device=self._device)
        ei = tensors["edge_index"]
        if not ei[0]:
            n = tensors["num_nodes"]
            edge_index = torch.tensor([list(range(n)), list(range(n))], dtype=torch.long, device=self._device)
        else:
            edge_index = torch.tensor(ei, dtype=torch.long, device=self._device)

        node_mapping = tensors["node_mapping"]

        # Run GNN
        with self._lock:
            with torch.no_grad():
                logits = self._model(x, edge_index)
                probs  = F.softmax(logits, dim=-1)

        # Build per-node results
        mule_accounts       = []
        suspicious_accounts = []
        node_classifications = {}
        max_mule_prob = 0.0

        for idx, account_id in node_mapping.items():
            p = probs[idx].cpu().tolist()
            p_normal, p_susp, p_mule = p[0], p[1], p[2]
            class_idx = int(torch.argmax(probs[idx]).item())
            classification = LABEL_NAMES[class_idx]
            gnn_score = mule_prob_to_risk_score(p_mule)

            node_classifications[account_id] = {
                "classification":     classification,
                "mule_probability":   round(p_mule, 4),
                "gnn_risk_score":     gnn_score,
                "risk_level":         risk_score_to_level(gnn_score),
                "confidence":         round(max(p), 4),
            }

            if classification == "MULE":
                mule_accounts.append(account_id)
                max_mule_prob = max(max_mule_prob, p_mule)
            elif classification == "SUSPICIOUS":
                suspicious_accounts.append(account_id)

        # Network-level pattern from sender/receiver
        sender_class   = node_classifications.get(sender_id, {}).get("classification", "NORMAL")
        receiver_class = node_classifications.get(receiver_id, {}).get("classification", "NORMAL")

        if mule_accounts:
            network_pattern = "MULE_NETWORK_DETECTED"
        elif suspicious_accounts:
            network_pattern = "SUSPICIOUS_NETWORK"
        else:
            network_pattern = "NORMAL_NETWORK"

        network_risk_score = mule_prob_to_risk_score(max_mule_prob)

        return {
            "transaction_id":       transaction_id,
            "node_count":           merged_sub.number_of_nodes(),
            "edge_count":           merged_sub.number_of_edges(),
            "node_classifications": node_classifications,
            "mule_accounts":        mule_accounts,
            "suspicious_accounts":  suspicious_accounts,
            "network_pattern":      network_pattern,
            "network_risk_score":   network_risk_score,
            "sender_id":            sender_id,
            "receiver_id":          receiver_id,
            "sender_classification": sender_class,
            "receiver_classification": receiver_class,
            "model_loaded":         True,
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns model status for the /api/gnn/status endpoint."""
        meta = self._metadata
        return {
            "model_loaded":     self._loaded,
            "model_type":       meta.get("model_type", GNN_MODEL_TYPE),
            "model_version":    meta.get("model_version", GNN_MODEL_VERSION),
            "architecture":     meta.get("architecture", "GATv2Conv × 3 + Linear × 2"),
            "node_feature_dim": meta.get("node_feature_dim", NODE_FEATURE_DIM),
            "edge_feature_dim": meta.get("edge_feature_dim", EDGE_FEATURE_DIM),
            "num_classes":      meta.get("num_classes", NUM_CLASSES),
            "class_names":      meta.get("class_names", ["NORMAL", "SUSPICIOUS", "MULE"]),
            "training_date":    meta.get("training_date"),
            "training_time_sec": meta.get("training_time_sec"),
            "training_samples": meta.get("training_samples", 0),
            "status":           "ACTIVE" if self._loaded else "NOT_TRAINED",
            "accuracy":         meta.get("test_metrics", {}).get("accuracy", 0.0),
            "f1_score":         meta.get("test_metrics", {}).get("f1_score", 0.0),
            "validation_metrics": meta.get("validation_metrics", {}),
            "test_metrics":     meta.get("test_metrics", {}),
            "label_distribution": meta.get("label_distribution", {}),
        }

    @staticmethod
    def _fallback_response(account_id: str, reason: str) -> Dict[str, Any]:
        return {
            "account_id":              account_id,
            "classification":          "UNKNOWN",
            "mule_probability":        0.0,
            "suspicious_probability":  0.0,
            "normal_probability":      1.0,
            "gnn_risk_score":          0.0,
            "risk_level":              "LOW",
            "network_pattern":         "UNKNOWN",
            "connected_accounts":      [],
            "connected_account_count": 0,
            "confidence":              0.0,
            "explanation":             [reason],
            "model_loaded":            False,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
GLOBAL_GNN_PREDICTOR = GNNPredictor()
