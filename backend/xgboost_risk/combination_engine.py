"""
Risk Combination Engine (Module 4).
Combines Module 2 Bank-Level Behavioural Risk Scores and Module 4 XGBoost Risk Score
using configurable weights. Determines overall transaction risk level, flagging,
and recommended policy decision.
"""

from typing import Dict, Any, List
from .config import (
    COMBINATION_WEIGHTS,
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
    Combines behavioural risk and XGBoost ML prediction.
    
    Returns:
        - combined_risk_score (0.0 to 100.0)
        - risk_level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        - decision_status ('ALLOW', 'MONITOR', 'CONTROLLED_ACTION')
        - flagged (bool)
        - top_risk_factors (list of merged unique factors)
    """
    w_sender = COMBINATION_WEIGHTS.get("sender_weight", 0.30)
    w_receiver = COMBINATION_WEIGHTS.get("receiver_weight", 0.30)
    w_xgb = COMBINATION_WEIGHTS.get("xgboost_weight", 0.40)

    s_score = float(sender_risk_score or 0.0)
    r_score = float(receiver_risk_score or 0.0)
    xgb_score = float(xgboost_prediction.get("xgboost_risk_score", 0.0) or 0.0)

    # Establish XGBoost ML prediction as the primary transaction-level risk score.
    # Since sender and receiver behavioural scores are already ingested directly as XGBoost input features,
    # we do NOT artificially add them again in a heavy re-weighting formula that inflates transaction risk.
    # Sender and receiver scores serve as supporting account-level indicators.
    transaction_risk_score = round(xgb_score, 2)
    transaction_risk_score = min(100.0, max(0.0, transaction_risk_score))

    # Evaluate transaction flagging
    xgb_flag_thresh = FLAG_THRESHOLDS.get("xgboost_risk_flag_threshold", 60.0)
    is_flagged = bool(transaction_risk_score >= xgb_flag_thresh)

    risk_level = score_to_risk_level(transaction_risk_score)
    decision_status = score_to_decision(transaction_risk_score, is_flagged=is_flagged)

    # Merge explainable factors
    top_factors: List[str] = list(xgboost_prediction.get("top_risk_factors", []))
    if is_flagged and not any("FLAGGED:" in f for f in top_factors):
        top_factors.insert(0, f"FLAGGED: Transaction risk score ({transaction_risk_score:.1f}) exceeds policy threshold ({xgb_flag_thresh:.0f})")

    return {
        "combined_risk_score": transaction_risk_score,
        "transaction_risk_score": transaction_risk_score,
        "risk_level": risk_level,
        "decision_status": decision_status,
        "flagged": is_flagged,
        "top_risk_factors": top_factors[:5],
        "sender_risk_score": round(s_score, 2),
        "receiver_risk_score": round(r_score, 2),
        "xgboost_risk_score": round(xgb_score, 2),
        "prediction_probability": xgboost_prediction.get("prediction_probability", 0.0),
        "model_version": xgboost_prediction.get("model_version", "v1.0.0-xgb"),
    }
