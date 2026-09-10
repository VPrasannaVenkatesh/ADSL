"""
Configuration for GNN-Based Money Mule Network Detection Module.
All thresholds, model hyperparameters, and integration weights are configurable here.
"""

import os
from typing import Dict, Any, List

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "gnn_mule_detector.pt")
METADATA_PATH = os.path.join(MODELS_DIR, "gnn_model_metadata.json")

os.makedirs(MODELS_DIR, exist_ok=True)

# ── Model Version ──────────────────────────────────────────────────────────────
GNN_MODEL_VERSION = "v1.0.0-gatv2"
GNN_MODEL_TYPE = "GATv2"

# ── Feature Dimensions ─────────────────────────────────────────────────────────
NODE_FEATURE_DIM = 22   # 22 node features (see graph_features.py)
EDGE_FEATURE_DIM = 10   # 10 edge features (extended from existing 7)

# ── Node Feature Names (canonical order for training & inference) ──────────────
NODE_FEATURE_NAMES: List[str] = [
    "behavioural_risk_score",       # [0]  Account behavioural risk (0–1 normalised)
    "avg_tx_amount",                # [1]  Mean transaction amount (log-normalised)
    "total_tx_count",               # [2]  Total in+out degree count (normalised)
    "sent_count",                   # [3]  Out-degree count (normalised)
    "received_count",               # [4]  In-degree count (normalised)
    "unique_sender_count",          # [5]  Unique predecessor nodes (normalised)
    "unique_recipient_count",       # [6]  Unique successor nodes (normalised)
    "fan_in_score",                 # [7]  In-degree normalised by max_in_degree
    "fan_out_score",                # [8]  Out-degree normalised by max_out_degree
    "short_dwell_count",            # [9]  Count of edges with dwell_time < 120s
    "amount_split_flag",            # [10] Binary: received large inflow + multiple outflows
    "cross_bank_tx_count",          # [11] Cross-bank edge count (normalised)
    "is_monitored",                 # [12] Binary: is_monitored flag from NetworkX graph
    "degree_centrality",            # [13] NetworkX degree centrality
    "in_degree",                    # [14] Raw in-degree (normalised)
    "out_degree",                   # [15] Raw out-degree (normalised)
    "pagerank_score",               # [16] PageRank centrality (normalised)
    "risk_propagation_score",       # [17] Network contextual risk (0–1)
    "bank_sbi",                     # [18] One-hot: is SBI account
    "bank_axis",                    # [19] One-hot: is AXIS account
    "bank_iob",                     # [20] One-hot: is IOB account
    "has_cycle",                    # [21] Binary: participates in nx.simple_cycles
]

# ── Class Labels ───────────────────────────────────────────────────────────────
LABEL_NORMAL = 0
LABEL_SUSPICIOUS = 1
LABEL_MULE = 2

LABEL_NAMES = {
    LABEL_NORMAL: "NORMAL",
    LABEL_SUSPICIOUS: "SUSPICIOUS",
    LABEL_MULE: "MULE",
}

NUM_CLASSES = 3

# ── GNN Risk Thresholds (0–100) ────────────────────────────────────────────────
GNN_RISK_THRESHOLDS = {
    "LOW":      {"min": 0.0,  "max": 30.0},
    "MEDIUM":   {"min": 31.0, "max": 60.0},
    "HIGH":     {"min": 61.0, "max": 80.0},
    "CRITICAL": {"min": 81.0, "max": 100.0},
}

def mule_prob_to_risk_score(mule_prob: float) -> float:
    """Converts mule probability [0.0–1.0] to GNN risk score [0.0–100.0]."""
    return round(min(100.0, max(0.0, mule_prob * 100.0)), 2)

def risk_score_to_level(score: float) -> str:
    if score >= 81.0:
        return "CRITICAL"
    if score >= 61.0:
        return "HIGH"
    if score >= 31.0:
        return "MEDIUM"
    return "LOW"

# ── Combined Risk Weights ──────────────────────────────────────────────────────
# Final combined score = w_behav * Behavioural + w_xgb * XGBoost + w_gnn * GNN
COMBINED_RISK_WEIGHTS = {
    "behavioural_weight": 0.30,
    "xgboost_weight":     0.40,
    "gnn_weight":         0.30,
}

# ── GNN Activation Trigger (which risk levels trigger GNN analysis) ───────────
GNN_TRIGGER_LEVELS = {"MEDIUM", "HIGH", "CRITICAL"}
GNN_TRIGGER_SCORE_THRESHOLD = 31.0  # Combined score threshold to trigger GNN

# ── Auto-Label Thresholds (topology-based labelling from graph) ───────────────
LABEL_THRESHOLDS = {
    # MULE: high fan-in AND fan-out AND short dwell, or participates in cycle
    "mule_min_in_degree":     3,
    "mule_min_out_degree":    2,
    "mule_min_short_dwell":   1,
    # SUSPICIOUS: elevated connectivity
    "suspicious_min_in":      2,
    "suspicious_min_out":     2,
    "suspicious_min_degree":  4,
    # Short dwell seconds threshold
    "short_dwell_seconds":    120,
}

# ── GNN Model Hyperparameters ─────────────────────────────────────────────────
GNN_HYPERPARAMS: Dict[str, Any] = {
    "hidden_dim":      64,
    "heads_layer1":    4,
    "heads_layer2":    2,
    "heads_layer3":    1,
    "dropout":         0.35,
    "learning_rate":   0.003,
    "weight_decay":    5e-4,
    "epochs":          120,
    "early_stop_patience": 18,
    "scheduler_step":  40,
    "scheduler_gamma": 0.5,
}

# ── Subgraph Analysis Limits ──────────────────────────────────────────────────
SUBGRAPH_CONFIG = {
    "max_hops":        3,
    "max_nodes":       150,   # Limit subgraph to prevent slow inference
}

# ── Dataset Split Ratios ──────────────────────────────────────────────────────
DATASET_SPLITS = {
    "train": 0.70,
    "val":   0.15,
    "test":  0.15,
}

# ── Network Pattern Labels ────────────────────────────────────────────────────
NETWORK_PATTERNS = [
    "FAN_IN_HUB",
    "FAN_OUT_HUB",
    "FAN_IN_FAN_OUT_HUB",
    "MULTI_HOP_CHAIN",
    "CIRCULAR_FLOW",
    "RAPID_FORWARDING",
    "AMOUNT_SPLITTING",
    "CROSS_BANK_MULE_NETWORK",
    "ISOLATED_ACCOUNT",
    "UNKNOWN",
]
