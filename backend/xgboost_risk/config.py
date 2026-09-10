"""
Configuration settings for XGBoost Transaction Risk Prediction Engine (Module 4).
"""

import os
from typing import Dict, Any, List

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_risk_model.json")
METADATA_PATH = os.path.join(MODELS_DIR, "feature_metadata.json")

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Model Version
MODEL_VERSION = "v2.0.0-multiclass-autonomous"

# 4-Class Granular Risk Categories (Replaces binary 2-type classification)
RISK_CLASSES: List[str] = [
    "NORMAL",           # Class 0: Legitimate everyday banking
    "SUSPICIOUS",       # Class 1: Behavioural anomaly, unusual velocity/hour
    "MULE_FLOW",        # Class 2: Mule topologies: Rapid Forwarding, Smurfing, Fan-In/Fan-Out
    "CRITICAL_FRAUD",   # Class 3: High-value account drain, device hijack, hostile activity
]
NUM_CLASSES = len(RISK_CLASSES)

# Risk Level Thresholds (0 to 100) - Configurable
XGBOOST_RISK_THRESHOLDS = {
    "LOW": {"min": 0.0, "max": 30.0},
    "MEDIUM": {"min": 31.0, "max": 60.0},
    "HIGH": {"min": 61.0, "max": 80.0},
    "CRITICAL": {"min": 81.0, "max": 100.0},
}

# Combination Engine Weights (Must sum to 1.0)
COMBINATION_WEIGHTS = {
    "sender_weight": 0.30,        # Weight of Sender behavioural risk score (Module 2)
    "receiver_weight": 0.30,      # Weight of Receiver behavioural risk score (Module 2)
    "xgboost_weight": 0.40,       # Weight of XGBoost transaction risk score (Module 4)
}

# Transaction Flagging Thresholds
FLAG_THRESHOLDS = {
    "combined_risk_flag_threshold": 61.0,  # Combined risk score >= 61 (HIGH/CRITICAL) triggers FLAGGED
    "xgboost_risk_flag_threshold": 65.0,   # XGBoost risk score >= 65 triggers FLAGGED
}

# Decision Mapping from Combined Risk Score
def score_to_risk_level(score: float) -> str:
    if score > 80.0:
        return "CRITICAL"
    if score > 60.0:
        return "HIGH"
    if score > 30.0:
        return "MEDIUM"
    return "LOW"

def score_to_decision(score: float, is_flagged: bool = False) -> str:
    """
    Maps combined risk score & flag status to policy action:
    - ALLOW -> COMPLETED
    - MONITOR -> MONITORING
    - CONTROLLED_ACTION -> RESTRICTED (Honeypot / Lien Layer)
    """
    if score >= 65.0 or is_flagged:
        return "CONTROLLED_ACTION"
    if score >= 35.0:
        return "MONITOR"
    return "ALLOW"

# XGBoost Model Hyperparameters (Fine-tuned for accurate multi-class prediction)
XGBOOST_HYPERPARAMS = {
    "n_estimators": 250,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "min_child_weight": 2,
    "gamma": 0.1,
    "objective": "multi:softprob",
    "num_class": NUM_CLASSES,
    "eval_metric": "mlogloss",
    "random_state": 42,
    "n_jobs": -1,
}

# List of all feature names in canonical order for training and inference
FEATURE_NAMES: List[str] = [
    # Transaction attributes
    "amount",
    "is_cross_bank",
    "recipient_is_new",
    "is_night",
    "hour_of_day",
    "tx_type_upi",
    "tx_type_imps",
    "tx_type_neft",
    "tx_type_bank_transfer",
    "device_is_mobile",
    "device_is_laptop",
    "device_is_tablet",
    "device_is_other",
    
    # Sender behavioural metrics
    "sender_sent_count",
    "sender_received_count",
    "sender_total_amount_sent",
    "sender_total_amount_received",
    "sender_avg_tx_amount",
    "sender_max_tx_amount",
    "sender_unique_recipients",
    "sender_unique_senders",
    "sender_tx_1h",
    "sender_tx_6h",
    "sender_tx_24h",
    "sender_avg_interval_sec",
    "sender_min_interval_sec",
    "sender_night_tx_count",
    "sender_device_changes",
    "sender_location_changes",
    "sender_fan_in",
    "sender_fan_out",
    "sender_forwarded_amount",
    "sender_short_dwell_count",
    "sender_amount_split_count",
    "sender_behavioural_risk_score",
    "sender_amount_vs_avg_ratio",
    "sender_velocity_ratio",
    
    # Receiver behavioural metrics
    "receiver_received_count",
    "receiver_sent_count",
    "receiver_total_amount_received",
    "receiver_avg_tx_amount",
    "receiver_max_tx_amount",
    "receiver_unique_senders",
    "receiver_tx_1h",
    "receiver_tx_24h",
    "receiver_fan_in",
    "receiver_fan_out",
    "receiver_short_dwell_count",
    "receiver_behavioural_risk_score",
    
    # Graph & topological indicators
    "network_rapid_forwarding",
    "network_short_dwell_flag",
    "network_amount_splitting",
    "network_cycle_detected",

    # Account Context & Profile Features
    "is_business",
    "expected_turnover_or_volume",
    "amount_vs_turnover_ratio",
    "is_within_operating_hours",
]
