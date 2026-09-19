"""
Configuration settings for XGBoost Transaction Risk Prediction Engine (Module 4).
Continuous risk scoring (0 to 100) with 3-tier risk classification:
  - LOW:    0.0  to 30.0 -> ALLOW / COMPLETED
  - MEDIUM: 30.1 to 60.0 -> MONITORING
  - HIGH:   60.1 to 100.0 -> HONEYPOT + LIEN APPLIED
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
MODEL_VERSION = "v3.0.0-continuous-regressor"

# Strict 3-Tier Risk Categories (No CRITICAL level at transaction flow)
RISK_LEVELS: List[str] = ["LOW", "MEDIUM", "HIGH"]

# Risk Thresholds
LOW_MAX = 30.0
MEDIUM_MAX = 60.0
HIGH_MIN = 60.1

XGBOOST_RISK_THRESHOLDS = {
    "LOW": {"min": 0.0, "max": 30.0},
    "MEDIUM": {"min": 30.1, "max": 60.0},
    "HIGH": {"min": 60.1, "max": 100.0},
}

# Transaction Flagging Threshold
FLAG_THRESHOLDS = {
    "xgboost_risk_flag_threshold": 60.1,  # High risk >= 60.1 triggers flag / honeypot
}

# Combination Weights (Reference supporting context)
COMBINATION_WEIGHTS = {
    "sender_weight": 0.30,
    "receiver_weight": 0.30,
    "xgboost_weight": 0.40,
}

def score_to_risk_level(score: float) -> str:
    """
    Classifies a continuous risk score (0 to 100) into exactly three levels:
    0 - 30   -> LOW
    31 - 60  -> MEDIUM
    61 - 100 -> HIGH
    """
    s = float(score)
    if s > 60.0:
        return "HIGH"
    if s > 30.0:
        return "MEDIUM"
    return "LOW"

def score_to_decision(score: float, is_flagged: bool = False) -> str:
    """
    Maps continuous risk score to transaction action:
    - score <= 30.0: ALLOW -> COMPLETED
    - 30.0 < score <= 60.0: MONITOR -> MONITORING
    - score > 60.0 or is_flagged: HONEYPOT -> HONEYPOT + LIEN APPLIED
    """
    s = float(score)
    if s > 60.0 or is_flagged:
        return "HONEYPOT"
    if s > 30.0:
        return "MONITOR"
    return "ALLOW"

# XGBoost Model Hyperparameters for Continuous Regression
XGBOOST_HYPERPARAMS = {
    "n_estimators": 300,
    "max_depth": 5,
    "learning_rate": 0.04,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "min_child_weight": 3,
    "gamma": 0.05,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "random_state": 42,
    "n_jobs": -1,
}

# List of all feature names in canonical order for training and inference
FEATURE_NAMES: List[str] = [
    # 1. Transaction attributes
    "amount",
    "is_cross_bank",
    "recipient_is_new",
    "beneficiary_usage_frequency",
    "is_night",
    "hour_of_day",
    "is_unusual_hour",
    "tx_type_upi",
    "tx_type_imps",
    "tx_type_neft",
    "tx_type_bank_transfer",
    
    # 2. Device information
    "device_is_mobile",
    "device_is_laptop",
    "device_is_tablet",
    "device_is_other",
    "is_new_device",
    "sender_device_changes",
    
    # 3. Location information
    "is_location_deviation",
    "sender_location_changes",
    "device_location_anomaly",
    
    # 4. Account Profile Context & Amount Analysis
    "is_business",
    "expected_turnover_or_volume",
    "amount_vs_turnover_ratio",
    "is_within_operating_hours",
    "sender_balance",
    "transfer_percentage_of_balance",
    "sender_amount_vs_avg_ratio",
    "sender_amount_vs_max_ratio",
    
    # 5. Sender behavioural metrics & Velocity
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
    "sender_burst_ratio",
    "sender_velocity_ratio",
    "sender_night_tx_count",
    "sender_fan_out",
    "sender_fan_in",
    "sender_forwarded_amount",
    "sender_short_dwell_count",
    "sender_amount_split_count",
    "sender_behavioural_risk_score",
    
    # 6. Receiver behavioural metrics
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
    
    # 7. Graph & Topological Mule Indicators
    "network_rapid_forwarding",
    "network_short_dwell_flag",
    "network_amount_splitting",
    "network_cycle_detected",
    "mule_multihop_signal",
    "sudden_in_out_surge",
]
