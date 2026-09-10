"""
Coordinator Configuration.
Defines configurable combination weights, synergy multipliers, and decision thresholds
for decentralized multi-bank risk sharing.
"""

from typing import Dict, Any

# Decision Thresholds (0 to 100) per Section 12 & 25 Specs
DECISION_THRESHOLDS = {
    "ALLOW": {"min_score": 0.0, "max_score": 30.0, "color": "#10B981", "badge_class": "badge-ALLOW"},
    "MONITOR": {"min_score": 30.01, "max_score": 50.0, "color": "#F59E0B", "badge_class": "badge-MONITOR"},
    "REVIEW": {"min_score": 50.01, "max_score": 85.0, "color": "#C084FC", "badge_class": "badge-REVIEW"},
    "CONTROLLED_ACTION": {"min_score": 85.01, "max_score": 95.0, "color": "#EF4444", "badge_class": "badge-CONTROLLED_ACTION"},
    "FREEZE": {"min_score": 95.01, "max_score": 100.0, "color": "#DC2626", "badge_class": "badge-FREEZE"},
}

# Combination Weights (Base linear weighting)
COORDINATOR_WEIGHTS = {
    "sender_weight": 0.50,
    "receiver_weight": 0.50,
}

# Non-linear Cross-Bank Synergy Multipliers
# When both banks independently detect elevated risk, coordinated risk is amplified
SYNERGY_RULES = {
    "both_critical": {"min_sender": 80.0, "min_receiver": 80.0, "boost_multiplier": 1.25, "reason": "Severe multi-bank correlation: Both sender and receiver banks independently flagged critical behavioural anomalies"},
    "both_high": {"min_sender": 60.0, "min_receiver": 60.0, "boost_multiplier": 1.18, "reason": "Dual-bank risk correlation: Both participating institutions report elevated behavioural risk"},
    "sender_critical_receiver_elevated": {"min_sender": 80.0, "min_receiver": 40.0, "boost_multiplier": 1.12, "reason": "Asymmetric critical outflow: Sender exhibits extreme balance drain and velocity with an active receiver"},
    "receiver_critical_sender_elevated": {"min_sender": 40.0, "min_receiver": 80.0, "boost_multiplier": 1.12, "reason": "Asymmetric critical inflow: Receiver exhibits immediate pass-through/short-dwell forwarding behavior"},
    "one_high_one_low": {"reason": "Isolated single-bank anomaly: One institution reports elevated risk while counterparty reports baseline behavior"},
    "both_low": {"reason": "Consistent low-risk consensus: Both participating banks confirm normal behavioural baselines"},
}

# Risk Level Mappings
RISK_LEVEL_MAP = {
    (0.0, 30.0): "LOW",
    (30.01, 60.0): "MEDIUM",
    (60.01, 80.0): "HIGH",
    (80.01, 100.0): "CRITICAL",
}


def score_to_risk_level(score: float) -> str:
    s = min(100.0, max(0.0, float(score)))
    if s <= 30.0:
        return "LOW"
    elif s <= 60.0:
        return "MEDIUM"
    elif s <= 80.0:
        return "HIGH"
    else:
        return "CRITICAL"


def score_to_decision(score: float) -> str:
    s = min(100.0, max(0.0, float(score)))
    if s <= 30.0:
        return "ALLOW"
    elif s <= 50.0:
        return "MONITOR"
    elif s <= 85.0:
        return "REVIEW"
    elif s <= 95.0:
        return "CONTROLLED_ACTION"
    else:
        return "FREEZE"
