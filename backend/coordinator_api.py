"""
FastAPI Server for Decentralized Bank Risk Coordinator.
Exposes Coordinator APIs and Bank-Level Risk Sharing endpoints on port 8002.
Run with: uvicorn coordinator_api:app --port 8002 --reload
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from coordinator.api_routes import coordinator_router
from coordinator.bank_endpoints import bank_risk_share_router
from coordinator.adsl_api_routes import adsl_router
from network_monitoring.api_routes import network_router
from gnn_detection.api import gnn_router

app = FastAPI(
    title="ADSL API",
    description="Autonomous Decentralized Security Layer (ADSL) — Central Transaction Processing & Mule Forensics (Port 8002)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(adsl_router)
app.include_router(coordinator_router)
app.include_router(bank_risk_share_router)
app.include_router(network_router)
app.include_router(gnn_router)

# Direct aliases for /adsl/... matching specification
@app.post("/adsl/transaction")
def adsl_tx_direct(req: dict):
    from coordinator.adsl_service import process_adsl_transaction
    return process_adsl_transaction(req)

@app.get("/adsl/mule-networks")
def adsl_nets_direct():
    from coordinator.mule_network_manager import GLOBAL_MULE_NETWORKS
    return GLOBAL_MULE_NETWORKS.get_summary()

@app.get("/adsl/mule-networks/{network_id}")
def adsl_net_detail_direct(network_id: str):
    from coordinator.mule_network_manager import GLOBAL_MULE_NETWORKS
    from fastapi import HTTPException
    net = GLOBAL_MULE_NETWORKS.get_network_detail(network_id)
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
    return net

@app.get("/adsl/under-review")
def adsl_review_direct():
    from network_monitoring.lien_layer import GLOBAL_LIEN_LAYER
    return {"count": len(GLOBAL_LIEN_LAYER.get_all_active_liens()), "under_review_items": GLOBAL_LIEN_LAYER.get_all_active_liens()}

@app.post("/adsl/review/{transaction_id}/action")
def adsl_action_direct(transaction_id: str, req: dict):
    from coordinator.adsl_service import execute_adsl_admin_action
    from fastapi import HTTPException
    action = req.get("action", "RELEASE")
    investigator = req.get("investigator_id", "ADMIN_OFFICER")
    notes = req.get("notes", "Action approved")
    res = execute_adsl_admin_action(transaction_id, action, investigator, notes)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.post("/adsl/account/{account_id}/action")
def adsl_account_action_direct(account_id: str, req: dict):
    from coordinator.adsl_service import execute_adsl_account_action
    from fastapi import HTTPException
    action = req.get("action", "FREEZE")
    bank = req.get("bank", "SBI")
    investigator = req.get("investigator_id", "ADMIN_OFFICER")
    notes = req.get("notes", "Direct account enforcement")
    res = execute_adsl_account_action(account_id, action, bank, investigator, notes)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.get("/adsl/monitoring-cases")
def adsl_monitoring_cases_direct(status: str = None):
    from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
    cases = GLOBAL_MONITORING_MANAGER.get_all_cases(status=status)
    return {"count": len(cases), "cases": cases}

@app.get("/adsl/rl-decisions")
def adsl_rl_decisions_direct(limit: int = 50):
    from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT
    decisions = GLOBAL_RL_AGENT.get_recent_decisions(limit=limit)
    return {"count": len(decisions), "decisions": decisions}

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "ADSL API",
        "port": 8002,
        "endpoints": [
            "/api/adsl/transaction",
            "/api/adsl/mule-networks",
            "/api/adsl/under-review",
            "/api/coordinator/decisions"
        ]
    }

