"""
Risk Engine Orchestrator.
Called after every transaction is stored. Runs feature extraction and risk scoring
for sender bank (SENDER role) and receiver bank (RECEIVER role) independently.
No cross-bank customer data is shared.
"""

from typing import Dict, Optional
import psycopg2

from .feature_extractor import extract_account_features
from .aggregator import run_risk_assessment
from .storage import store_risk_assessment


def assess_transaction_risk(
    conns: Dict[str, psycopg2.extensions.connection],
    transaction_id: str,
    sender_bank: str,
    sender_account_id: str,
    receiver_bank: str,
    receiver_account_id: str,
    amount: int,
    tx_type: str,
    timestamp,
    device_ip: str,
    location: str,
    recipient_is_new: bool,
) -> Dict[str, Optional[str]]:
    """
    Runs independent bank-level risk assessment for sender (in sender's DB) and
    receiver (in receiver's DB). Returns assessment_ids for both sides.

    For cross-bank transfers:
      - Sender bank assesses SENDER role using only sbi_db / axis_db / iob_db.
      - Receiver bank assesses RECEIVER role using only its own database.
      - No full customer records are shared between banks.
    """
    results = {
        "sender_assessment_id": None,
        "receiver_assessment_id": None,
        "sender_risk_score": 0.0,
        "receiver_risk_score": 0.0,
    }

    # ── 1. Sender-Side Risk Assessment ──────────────────────────────────────
    try:
        sender_conn = conns[sender_bank]
        sender_features = extract_account_features(
            conn=sender_conn,
            bank=sender_bank,
            account_id=sender_account_id,
            txn_timestamp=timestamp,
            txn_amount=amount,
            txn_type=tx_type,
            device_ip=device_ip,
            location=location,
            recipient_is_new=recipient_is_new,
            role="SENDER",
        )
        if sender_features:
            sender_result = run_risk_assessment(
                transaction_id=transaction_id,
                features=sender_features,
                role="SENDER",
            )
            if sender_result:
                results["sender_assessment_id"] = store_risk_assessment(sender_conn, sender_result)
                results["sender_risk_score"] = sender_result.final_risk_score
    except Exception as e:
        print(f"[RISK ENGINE] Sender risk error ({sender_bank}/{sender_account_id}): {e}")

    # ── 2. Receiver-Side Risk Assessment ────────────────────────────────────
    try:
        receiver_conn = conns[receiver_bank]
        receiver_features = extract_account_features(
            conn=receiver_conn,
            bank=receiver_bank,
            account_id=receiver_account_id,
            txn_timestamp=timestamp,
            txn_amount=amount,
            txn_type=tx_type,
            device_ip=device_ip,
            location=location,
            recipient_is_new=False,  # recipient_is_new is a sender-side signal
            role="RECEIVER",
        )
        if receiver_features:
            receiver_result = run_risk_assessment(
                transaction_id=transaction_id,
                features=receiver_features,
                role="RECEIVER",
            )
            if receiver_result:
                results["receiver_assessment_id"] = store_risk_assessment(receiver_conn, receiver_result)
                results["receiver_risk_score"] = receiver_result.final_risk_score
    except Exception as e:
        print(f"[RISK ENGINE] Receiver risk error ({receiver_bank}/{receiver_account_id}): {e}")

    return results
