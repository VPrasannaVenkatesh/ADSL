"""
Pydantic Data Models for Decentralized Bank Risk Sharing & Coordinator Decisions.
Strict privacy preservation: zero customer PII, zero balances, zero raw ledger rows.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


def mask_account_id(account_id: str) -> str:
    """Masks internal account identifier to protect customer privacy."""
    if not account_id:
        return "UNKNOWN"
    parts = account_id.split('-')
    if len(parts) == 2:
        bank, num = parts
        if len(num) > 3:
            return f"{bank}-***{num[-3:]}"
        return f"{bank}-***{num}"
    if len(account_id) > 4:
        return f"***{account_id[-4:]}"
    return "***"


class BankRiskShareResponse(BaseModel):
    """
    Privacy-preserving risk response provided by a bank to the Coordinator.
    Contains strictly risk indicators, zero private customer attributes.
    """
    transaction_id: str
    bank_name: str
    transaction_side: str  # 'SENDER' or 'RECEIVER'
    masked_account_id: str
    local_risk_score: float
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    top_risk_indicators: List[str]
    assessment_timestamp: Optional[datetime] = None
    xgboost_risk_score: Optional[float] = None
    combined_risk_score: Optional[float] = None
    flagged: Optional[bool] = None


class CoordinatedDecisionResult(BaseModel):
    """
    Synthesized transaction-level decision produced by the Coordinator.
    """
    coordination_id: str
    transaction_id: str
    participating_banks: List[str]
    
    sender_bank: str
    sender_masked_account: str
    sender_risk_score: float
    sender_risk_level: str
    sender_indicators: List[str]
    
    receiver_bank: str
    receiver_masked_account: str
    receiver_risk_score: float
    receiver_risk_level: str
    receiver_indicators: List[str]
    
    final_risk_score: float
    final_risk_level: str
    final_decision: str  # 'ALLOW', 'MONITOR', 'REVIEW', 'CONTROLLED_ACTION'
    decision_reasons: List[str]
    
    xgboost_risk_score: Optional[float] = None
    combined_risk_score: Optional[float] = None
    flagged: Optional[bool] = None
    
    coordination_timestamp: datetime
