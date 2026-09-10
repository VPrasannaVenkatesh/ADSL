"""
FastAPI Router for Coordinator Dashboard API.
Provides coordinator decision streams, filters, audit drawers, summaries, and thresholds.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from .storage import (
    query_decisions,
    get_decision_detail,
    get_coordinator_summary,
)
from .coordinator_service import coordinate_transaction_risk
from .config import DECISION_THRESHOLDS, COORDINATOR_WEIGHTS, SYNERGY_RULES

coordinator_router = APIRouter(prefix="/api/coordinator", tags=["Risk Coordinator"])


class CoordinateRequest(BaseModel):
    sender_bank: str
    receiver_bank: str


@coordinator_router.post("/coordinate/{transaction_id}")
def trigger_coordination(transaction_id: str, req: CoordinateRequest):
    """
    Triggers decentralized risk coordination for a transaction between sender_bank and receiver_bank.
    """
    decision = coordinate_transaction_risk(
        transaction_id=transaction_id,
        sender_bank=req.sender_bank,
        receiver_bank=req.receiver_bank,
    )
    if not decision:
        raise HTTPException(status_code=500, detail="Failed to synthesize coordinated decision")
    return decision


@coordinator_router.get("/decisions")
def get_decisions(
    bank: Optional[str] = Query(None, description="SBI, AXIS, IOB, or ALL"),
    decision: Optional[str] = Query(None, description="ALLOW, MONITOR, REVIEW, CONTROLLED_ACTION"),
    risk_level: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    transaction_id: Optional[str] = Query(None),
    coordination_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    """Returns paginated coordinator decisions with optional filtering."""
    data = query_decisions(
        limit=limit,
        offset=offset,
        bank=bank,
        decision=decision,
        risk_level=risk_level,
        transaction_id=transaction_id,
        coordination_id=coordination_id,
    )
    return {"decisions": data, "count": len(data)}


@coordinator_router.get("/decisions/{coordination_id}")
def get_decision(coordination_id: str):
    """Returns full detail for a single coordinated decision."""
    data = get_decision_detail(coordination_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Coordination {coordination_id} not found")
    return data


@coordinator_router.get("/summary")
def get_summary(bank: Optional[str] = Query(None)):
    """Returns coordinator decision totals, averages, and cross-bank pair breakdown."""
    return get_coordinator_summary(bank=bank)


@coordinator_router.get("/live")
def get_live(bank: Optional[str] = Query(None), limit: int = Query(50, le=200)):
    """Returns recent live coordinated decisions for real-time dashboard feed."""
    data = query_decisions(limit=limit, bank=bank)
    return {"decisions": data}


@coordinator_router.get("/config")
def get_config():
    """Returns active decision thresholds and weights."""
    return {
        "thresholds": DECISION_THRESHOLDS,
        "weights": COORDINATOR_WEIGHTS,
        "synergy_rules": SYNERGY_RULES,
    }


@coordinator_router.get("/health")
def health():
    return {"status": "ok", "service": "decentralized-risk-coordinator"}
