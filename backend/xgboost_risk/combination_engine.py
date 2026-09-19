"""
Risk Combination Engine (Module 4).
Aligns Module 2 Bank-Level Behavioural Risk Scores and Module 4 Continuous XGBoost Risk Score.
Ensures the XGBoost risk score serves as the primary transaction risk score (0.0 to 100.0)
and maps strictly to the 3 agreed tiers:
  - LOW (0 - 30.0)    -> ALLOW -> COMPLETED
  - MEDIUM (30.1 - 60.0) -> MONITOR -> MONITORING
  - HIGH (60.1 - 100.0)  -> HONEYPOT -> HONEYPOT + LIEN APPLIED
"""

from typing import Dict, Any, List
from .config import (
    FLAG_THRESHOLDS,
    score_to_risk_level,
    score_to_decision,
)


def combine_risk_assessments(
    sender_risk_score: float,
    receiver_risk_score: float,
    xgboost_prediction: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Combines behavioural risk and XGBoost ML continuous prediction.
    
    Returns:
        - combined_risk_score: float (0.0 to 100.0)
        - transaction_risk_score: float (0.0 to 100.0)
        - risk_level: str ('LOW', 'MEDIUM', 'HIGH')
        - decision_status: str ('ALLOW', 'MONITOR', 'HONEYPOT')
        - flagged: bool
        - top_risk_factors: list of explainable factors
    """
    s_score = float(sender_risk_score or 0.0)
    r_score = float(receiver_risk_score or 0.0)
    xgb_score = float(xgboost_prediction.get("xgboost_risk_score", 0.0) or 0.0)

    # Establish XGBoost ML prediction as the primary transaction-level risk score.
    # Feature vector already ingests sender and receiver behavioural metrics directly.
    transaction_risk_score = round(float(xgb_score), 1)
    transaction_risk_score = min(100.0, max(0.0, transaction_risk_score))

    # Evaluate transaction flagging (>= 60.1)
    xgb_flag_thresh = FLAG_THRESHOLDS.get("xgboost_risk_flag_threshold", 60.1)
    is_flagged = bool(transaction_risk_score >= xgb_flag_thresh)

    risk_level = score_to_risk_level(transaction_risk_score)
    decision_status = score_to_decision(transaction_risk_score, is_flagged=is_flagged)

    # Merge explainable factors
    top_factors: List[str] = list(xgboost_prediction.get("top_risk_factors", []))
    if is_flagged and not any("HONEYPOT:" in f or "HIGH RISK:" in f for f in top_factors):
        top_factors.insert(0, f"HIGH RISK: Transaction risk score ({transaction_risk_score:.1f}) routed to Honeypot + Lien")

    return {
        "combined_risk_score": transaction_risk_score,
        "transaction_risk_score": transaction_risk_score,
        "risk_level": risk_level,
        "decision_status": decision_status,
        "flagged": is_flagged,
        "top_risk_factors": top_factors[:5],
        "sender_risk_score": round(s_score, 1),
        "receiver_risk_score": round(r_score, 1),
        "xgboost_risk_score": round(xgb_score, 1),
        "prediction_probability": xgboost_prediction.get("prediction_probability", 0.90),
        "model_version": xgboost_prediction.get("model_version", "v3.0.0-xgb"),
    }
