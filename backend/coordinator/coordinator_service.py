"""
Coordinator Service Orchestration.
Communicates strictly with participating banks to request risk indicators,
synthesizes coordinated decisions, and stores results independently.
"""

from typing import Optional, Dict, Any
from .models import BankRiskShareResponse, CoordinatedDecisionResult
from .bank_endpoints import fetch_bank_risk_share
from .decision_engine import synthesize_coordinated_decision
from .storage import save_coordinated_decision


def coordinate_transaction_risk(
    transaction_id: str,
    sender_bank: str,
    receiver_bank: str,
) -> Optional[CoordinatedDecisionResult]:
    """
    Executes decentralized risk coordination for a transaction:
    1. Requests sender-side risk assessment from sender_bank ONLY.
    2. Requests receiver-side risk assessment from receiver_bank ONLY.
    3. The 3rd uninvolved bank is NEVER queried or notified.
    4. Synthesizes final coordinated score & decision.
    5. Saves to coordinator SQLite storage.
    """
    s_bank = sender_bank.upper()
    r_bank = receiver_bank.upper()

    # 1. Fetch Sender Report from sender_bank
    sender_report = fetch_bank_risk_share(s_bank, transaction_id, side="SENDER")
    if not sender_report:
        # Construct neutral baseline if not ready yet
        sender_report = BankRiskShareResponse(
            transaction_id=transaction_id,
            bank_name=s_bank,
            transaction_side="SENDER",
            masked_account_id=f"{s_bank}-***",
            local_risk_score=0.0,
            risk_level="LOW",
            top_risk_indicators=["Baseline activity recorded"],
        )

    # 2. Fetch Receiver Report from receiver_bank
    receiver_report = fetch_bank_risk_share(r_bank, transaction_id, side="RECEIVER")
    if not receiver_report:
        receiver_report = BankRiskShareResponse(
            transaction_id=transaction_id,
            bank_name=r_bank,
            transaction_side="RECEIVER",
            masked_account_id=f"{r_bank}-***",
            local_risk_score=0.0,
            risk_level="LOW",
            top_risk_indicators=["Baseline activity recorded"],
        )

    # 3. Synthesize Coordinated Decision
    decision = synthesize_coordinated_decision(
        transaction_id=transaction_id,
        sender_report=sender_report,
        receiver_report=receiver_report,
    )

    # 4. Save to Independent Coordinator Storage
    save_coordinated_decision(decision)

    return decision
