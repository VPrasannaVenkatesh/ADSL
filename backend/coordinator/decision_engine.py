"""
Coordinator Decision Engine.
Synthesizes sender-side and receiver-side risk reports using configurable weights,
dual-institution synergy multipliers, and policy thresholds.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Tuple
from .models import BankRiskShareResponse, CoordinatedDecisionResult
from .config import (
    COORDINATOR_WEIGHTS,
    SYNERGY_RULES,
    score_to_risk_level,
    score_to_decision,
)


def synthesize_coordinated_decision(
    transaction_id: str,
    sender_report: BankRiskShareResponse,
    receiver_report: BankRiskShareResponse,
) -> CoordinatedDecisionResult:
    """
    Combines sender and receiver bank risk responses into a final coordinated transaction-level decision.
    """
    s_score = sender_report.local_risk_score
    r_score = receiver_report.local_risk_score

    # 1. Base Weighted Score
    w_sender = COORDINATOR_WEIGHTS["sender_weight"]
    w_receiver = COORDINATOR_WEIGHTS["receiver_weight"]
    base_score = (s_score * w_sender) + (r_score * w_receiver)

    # 2. Cross-Bank Synergy Evaluation
    multiplier = 1.0
    synergy_reasons: List[str] = []

    if s_score >= 80.0 and r_score >= 80.0:
        multiplier = SYNERGY_RULES["both_critical"]["boost_multiplier"]
        synergy_reasons.append(SYNERGY_RULES["both_critical"]["reason"])
    elif s_score >= 60.0 and r_score >= 60.0:
        multiplier = SYNERGY_RULES["both_high"]["boost_multiplier"]
        synergy_reasons.append(SYNERGY_RULES["both_high"]["reason"])
    elif s_score >= 80.0 and r_score >= 40.0:
        multiplier = SYNERGY_RULES["sender_critical_receiver_elevated"]["boost_multiplier"]
        synergy_reasons.append(SYNERGY_RULES["sender_critical_receiver_elevated"]["reason"])
    elif r_score >= 80.0 and s_score >= 40.0:
        multiplier = SYNERGY_RULES["receiver_critical_sender_elevated"]["boost_multiplier"]
        synergy_reasons.append(SYNERGY_RULES["receiver_critical_sender_elevated"]["reason"])
    elif (s_score >= 60.0 and r_score <= 30.0) or (r_score >= 60.0 and s_score <= 30.0):
        synergy_reasons.append(SYNERGY_RULES["one_high_one_low"]["reason"])
    elif s_score <= 30.0 and r_score <= 30.0:
        synergy_reasons.append(SYNERGY_RULES["both_low"]["reason"])

    final_score = round(min(100.0, max(0.0, base_score * multiplier)), 2)
    final_level = score_to_risk_level(final_score)
    final_decision = score_to_decision(final_score)

    # 3. Explainable Decision Reasons Synthesis
    reasons: List[str] = []

    # Add primary synergy/consensus explanation
    if synergy_reasons:
        reasons.extend(synergy_reasons)

    # Add Sender bank's specific risk signals
    if sender_report.top_risk_indicators:
        for ind in sender_report.top_risk_indicators[:3]:
            if "No anomalous patterns" not in ind:
                reasons.append(f"[{sender_report.bank_name} Sender]: {ind}")

    # Add Receiver bank's specific risk signals
    if receiver_report.top_risk_indicators:
        for ind in receiver_report.top_risk_indicators[:3]:
            if "No anomalous patterns" not in ind:
                reasons.append(f"[{receiver_report.bank_name} Receiver]: {ind}")

    # 4. Integrate Abstract XGBoost Risk Assessment if present
    xgb_score = sender_report.xgboost_risk_score or receiver_report.xgboost_risk_score
    comb_score = sender_report.combined_risk_score or receiver_report.combined_risk_score
    is_flagged = bool(sender_report.flagged or receiver_report.flagged)

    if is_flagged:
        final_decision = "CONTROLLED_ACTION"
        reasons.insert(0, "[XGBoost ML Consensus]: Transaction flagged as anomalous by predictive ML model.")
    elif xgb_score is not None and xgb_score >= 65.0:
        if final_decision == "ALLOW":
            final_decision = "MONITOR"
        reasons.insert(0, f"[XGBoost ML Risk]: Predictive model flagged elevated risk score ({xgb_score:.1f}/100).")

    if not reasons or len(reasons) == 1 and "consistent" in reasons[0].lower():
        reasons = ["Both participating institutions confirm normal behavioural baselines with no anomalous signals."]

    # Participating banks list (unique)
    participating = list(dict.fromkeys([sender_report.bank_name, receiver_report.bank_name]))

    coord_id = f"COORD_{uuid.uuid4().hex[:14].upper()}"

    return CoordinatedDecisionResult(
        coordination_id=coord_id,
        transaction_id=transaction_id,
        participating_banks=participating,
        sender_bank=sender_report.bank_name,
        sender_masked_account=sender_report.masked_account_id,
        sender_risk_score=sender_report.local_risk_score,
        sender_risk_level=sender_report.risk_level,
        sender_indicators=sender_report.top_risk_indicators,
        receiver_bank=receiver_report.bank_name,
        receiver_masked_account=receiver_report.masked_account_id,
        receiver_risk_score=receiver_report.local_risk_score,
        receiver_risk_level=receiver_report.risk_level,
        receiver_indicators=receiver_report.top_risk_indicators,
        final_risk_score=comb_score if comb_score is not None else final_score,
        final_risk_level=final_level,
        final_decision=final_decision,
        decision_reasons=reasons[:7],
        xgboost_risk_score=xgb_score,
        combined_risk_score=comb_score,
        flagged=is_flagged,
        coordination_timestamp=datetime.now(),
    )
