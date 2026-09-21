"""
Risk Score Aggregator.
Combines 8 component scores with configurable weights into a final 0-100 risk score.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from .calculators import (
    calculate_amount_risk,
    calculate_velocity_risk,
    calculate_behaviour_deviation_risk,
    calculate_device_risk,
    calculate_location_risk,
    calculate_counterparty_risk,
    calculate_timing_risk,
    calculate_network_pattern_risk,
)

# Configurable weights (must sum to 1.0)
RISK_WEIGHTS = {
    "amount_risk":              0.18,
    "velocity_risk":            0.18,
    "behaviour_deviation_risk": 0.14,
    "network_pattern_risk":     0.17,
    "counterparty_risk":        0.12,
    "device_risk":              0.08,
    "location_risk":            0.08,
    "timing_risk":              0.05,
}

assert abs(sum(RISK_WEIGHTS.values()) - 1.0) < 1e-6, "Risk weights must sum to 1.0"


def score_to_level(score: float) -> str:
    if score <= 30.0:
        return "LOW"
    elif score <= 55.0:
        return "MEDIUM"
    elif score <= 75.0:
        return "HIGH"
    else:
        return "CRITICAL"


@dataclass
class RiskAssessmentResult:
    transaction_id: str
    account_id: str
    bank_name: str
    role: str  # 'SENDER' or 'RECEIVER'
    amount: int
    transaction_type: str
    assessment_timestamp: Any  # datetime

    amount_risk: float
    velocity_risk: float
    behaviour_deviation_risk: float
    device_risk: float
    location_risk: float
    counterparty_risk: float
    timing_risk: float
    network_pattern_risk: float

    final_risk_score: float
    risk_level: str
    risk_reasons: List[str]


def run_risk_assessment(
    transaction_id: str,
    features: Dict[str, Any],
    role: str = "SENDER",
) -> RiskAssessmentResult:
    """
    Runs all 8 risk component calculators, applies weights with non-linear multi-anomaly boosting,
    and returns a full assessment.
    """
    if not features:
        return None

    account = features["account"]
    curr_tx = features["current_tx"]

    amt_score,  amt_reasons  = calculate_amount_risk(features)
    vel_score,  vel_reasons  = calculate_velocity_risk(features)
    beh_score,  beh_reasons  = calculate_behaviour_deviation_risk(features)
    dev_score,  dev_reasons  = calculate_device_risk(features)
    loc_score,  loc_reasons  = calculate_location_risk(features)
    ctp_score,  ctp_reasons  = calculate_counterparty_risk(features)
    tim_score,  tim_reasons  = calculate_timing_risk(features)
    net_score,  net_reasons  = calculate_network_pattern_risk(features)

    scores = [amt_score, vel_score, beh_score, dev_score, loc_score, ctp_score, tim_score, net_score]

    # Base weighted linear sum
    base_score = (
        amt_score  * RISK_WEIGHTS["amount_risk"]              +
        vel_score  * RISK_WEIGHTS["velocity_risk"]            +
        beh_score  * RISK_WEIGHTS["behaviour_deviation_risk"] +
        dev_score  * RISK_WEIGHTS["device_risk"]              +
        loc_score  * RISK_WEIGHTS["location_risk"]            +
        ctp_score  * RISK_WEIGHTS["counterparty_risk"]        +
        tim_score  * RISK_WEIGHTS["timing_risk"]              +
        net_score  * RISK_WEIGHTS["network_pattern_risk"]
    )

    # Multi-anomaly synergy booster: In banking security, compounding anomalies
    # (e.g. high velocity + high amount + network anomaly) represent acute fraud risk.
    severe_count = sum(1 for s in scores if s >= 50.0)
    critical_count = sum(1 for s in scores if s >= 70.0)
    peak_score = max(scores) if scores else 0.0

    if critical_count >= 2:
        # Multiple critical signals compound risk to HIGH or CRITICAL
        boosted = max(base_score * 1.5, base_score * 0.45 + peak_score * 0.55)
        final = boosted + 10.0 * (critical_count - 1)
    elif severe_count >= 2:
        # Compound warning
        final = max(base_score * 1.25, base_score * 0.6 + peak_score * 0.4)
    elif peak_score >= 80.0:
        # Single acute outlier
        final = max(base_score, peak_score * 0.75)
    else:
        final = base_score

    final = round(min(100.0, max(0.0, final)), 2)

    # Collect non-trivial reasons only (max 8 most informative)
    all_reasons = amt_reasons + vel_reasons + beh_reasons + dev_reasons + loc_reasons + ctp_reasons + tim_reasons + net_reasons
    all_reasons = all_reasons[:8] if all_reasons else ["No anomalous patterns detected for this transaction."]

    return RiskAssessmentResult(
        transaction_id=transaction_id,
        account_id=account["account_id"],
        bank_name=features["bank"],
        role=role,
        amount=curr_tx["amount"],
        transaction_type=curr_tx["tx_type"],
        assessment_timestamp=curr_tx["timestamp"],
        amount_risk=round(amt_score, 2),
        velocity_risk=round(vel_score, 2),
        behaviour_deviation_risk=round(beh_score, 2),
        device_risk=round(dev_score, 2),
        location_risk=round(loc_score, 2),
        counterparty_risk=round(ctp_score, 2),
        timing_risk=round(tim_score, 2),
        network_pattern_risk=round(net_score, 2),
        final_risk_score=final,
        risk_level=score_to_level(final),
        risk_reasons=all_reasons,
    )
