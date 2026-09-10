"""
FastAPI Router for ADSL Central Transaction Processing & Mule Network Forensics.
Endpoints:
- POST /api/adsl/transaction (and /adsl/transaction)
- GET  /api/adsl/mule-networks (and /adsl/mule-networks)
- GET  /api/adsl/mule-networks/{network_id} (and /adsl/mule-networks/{network_id})
- GET  /api/adsl/under-review (and /adsl/under-review)
- POST /api/adsl/review/{transaction_id}/action (and /adsl/review/{transaction_id}/action)
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from .adsl_service import (
    process_adsl_transaction,
    execute_adsl_admin_action,
    ALLOW_THRESHOLD,
    MONITOR_THRESHOLD,
    REVIEW_THRESHOLD,
    RESTRICT_THRESHOLD,
)
from .mule_network_manager import GLOBAL_MULE_NETWORKS
from network_monitoring.lien_layer import GLOBAL_LIEN_LAYER

adsl_router = APIRouter(prefix="/api/adsl", tags=["ADSL"])


class ADSLTransactionRequest(BaseModel):
    transaction_id: Optional[str] = None
    sender_bank: str
    sender_account_id: str
    receiver_bank: str
    receiver_account_id: str
    amount: int
    transaction_type: Optional[str] = "TRANSFER"
    transaction_timestamp: Optional[str] = None
    device_ip: Optional[str] = "Mobile:192.168.1.1"
    location: Optional[str] = "Chennai"
    recipient_is_new: Optional[bool] = False


class AdminReviewActionRequest(BaseModel):
    action: str  # "RELEASE", "MONITOR", "RESTRICT", "FREEZE"
    investigator_id: Optional[str] = "COMPLIANCE_OFFICER_01"
    notes: Optional[str] = "Investigation action executed"


@adsl_router.post("/transaction")
def adsl_process_transaction(req: ADSLTransactionRequest):
    """
    ADSL Central Transaction Decision Pipeline:
    - Queries stored bank risk profiles for sender and receiver
    - If combined risk < 30 (ALLOW): Fast path COMPLETED (bypasses graph and GNN!)
    - If combined risk >= 30: Triggers Graph Analysis, Fund Provenance, pre-trained GNN, and Mule Network grouping
    """
    result = process_adsl_transaction(req.dict())
    return result


@adsl_router.get("/thresholds")
def get_adsl_thresholds():
    """Returns the ADSL decision thresholds."""
    return {
        "ALLOW_THRESHOLD": ALLOW_THRESHOLD,
        "MONITOR_THRESHOLD": MONITOR_THRESHOLD,
        "REVIEW_THRESHOLD": REVIEW_THRESHOLD,
        "RESTRICT_THRESHOLD": RESTRICT_THRESHOLD,
    }


@adsl_router.get("/mule-networks")
def get_mule_networks():
    """
    Returns detected Mule Networks summary and list:
    Total Networks, Critical Networks, Mule Accounts Detected, Suspicious Accounts, Networks Under Review.
    """
    return GLOBAL_MULE_NETWORKS.get_summary()


@adsl_router.get("/mule-networks/{network_id}")
def get_mule_network_detail(network_id: str):
    """
    Returns complete graph data for an individual Mule Network for interactive visualization:
    nodes (with roles, behaviour risk, XGBoost risk, GNN mule prob), directed edges, amounts, timestamps.
    """
    net = GLOBAL_MULE_NETWORKS.get_network_detail(network_id)
    if not net:
        raise HTTPException(status_code=404, detail=f"Mule Network {network_id} not found")
    return net


@adsl_router.get("/under-review")
def get_under_review_transactions():
    """
    Returns all transactions and liens currently Under Review.
    """
    liens = GLOBAL_LIEN_LAYER.get_all_active_liens()
    return {
        "count": len(liens),
        "under_review_items": liens,
    }


@adsl_router.post("/review/{transaction_id}/action")
def take_review_action(transaction_id: str, req: AdminReviewActionRequest):
    """
    Executes manual admin review action on a transaction:
    - RELEASE: Releases lien hold -> status RELEASED -> COMPLETED
    - MONITOR: status MONITORING
    - RESTRICT: status RESTRICTED
    - FREEZE: status FROZEN (account frozen in DB)
    """
    res = execute_adsl_admin_action(
        transaction_id=transaction_id,
        action=req.action,
        investigator_id=req.investigator_id or "ADMIN_OFFICER",
        notes=req.notes or "Action approved",
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


class AccountEnforcementRequest(BaseModel):
    action: str  # "FREEZE", "RESTRICT", "MONITOR", "RELEASE"
    bank: Optional[str] = "SBI"
    investigator_id: Optional[str] = "COMPLIANCE_OFFICER_01"
    notes: Optional[str] = "Admin action via Graph Forensics"


@adsl_router.post("/account/{account_id}/action")
def take_account_action(account_id: str, req: AccountEnforcementRequest):
    """
    Direct enforcement on a specific node/account from the Graph Forensics UI:
    - FREEZE: Instantly locks account and places freeze lien
    - RESTRICT: Caps transaction velocity
    - MONITOR: Flags for heightened GNN tracking
    - RELEASE: Clears restrictions
    """
    from .adsl_service import execute_adsl_account_action
    res = execute_adsl_account_action(
        account_id=account_id,
        action=req.action,
        bank=req.bank or "SBI",
        investigator_id=req.investigator_id or "ADMIN_OFFICER",
        notes=req.notes or "Manual account action",
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@adsl_router.get("/monitoring-cases")
def get_monitoring_cases(status: Optional[str] = None):
    """
    Returns active or resolved monitoring cases (genuine vs. suspicious indicators, follow-up counts).
    """
    from .monitoring_manager import GLOBAL_MONITORING_MANAGER
    cases = GLOBAL_MONITORING_MANAGER.get_all_cases(status=status)
    return {
        "count": len(cases),
        "cases": cases,
    }


@adsl_router.get("/rl-decisions")
def get_rl_decisions(limit: int = 50):
    """
    Returns RL graph exploration decisions and audit trail.
    """
    from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT
    decisions = GLOBAL_RL_AGENT.get_recent_decisions(limit=limit)
    return {
        "count": len(decisions),
        "decisions": decisions,
    }


@adsl_router.get("/lien/account/{account_id}/balance")
def get_account_lien_breakdown(account_id: str, current_balance: int = 100000):
    """
    Returns available balance vs. protected lien amount breakdown for an account.
    """
    return GLOBAL_LIEN_LAYER.get_account_balance_breakdown(account_id, current_balance)

