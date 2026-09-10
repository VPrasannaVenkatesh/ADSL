"""
FastAPI Risk Monitoring Dashboard API.
Serves risk assessment data from sbi_db, axis_db, and iob_db.
Run with: uvicorn risk_api:app --port 8001 --reload
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from risk_engine.api_routes import router as risk_router
from xgboost_risk.api_routes import xgboost_router
from coordinator.api_routes import coordinator_router
from coordinator.bank_endpoints import bank_risk_share_router
from gnn_detection.api import gnn_router
from network_monitoring.api_routes import network_router

from risk_engine.account_risk_profile import initialize_all_account_risk_tables, get_stored_account_risk_profile
from simulator.db_connection import get_bank_connection, BANK_NAMES

app = FastAPI(
    title="Bank Risk API",
    description="Bank-Level Behavioural Risk Provider & Analytics API (Port 8001)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk_router)
app.include_router(xgboost_router)
app.include_router(coordinator_router)
app.include_router(bank_risk_share_router)
app.include_router(gnn_router)
app.include_router(network_router)

@app.on_event("startup")
def on_startup():
    try:
        initialize_all_account_risk_tables()
    except Exception as e:
        print(f"[STARTUP] Error initializing risk profile tables: {e}")

@app.get("/")
def root():
    return {"status": "ok", "service": "Bank Risk API", "port": 8001}

@app.get("/risk/account/{account_id}")
def get_account_risk_direct(account_id: str):
    """Direct alias for ADSL request: GET /risk/account/{account_id}."""
    bank_name = "SBI"
    for b in BANK_NAMES:
        if account_id.upper().startswith(b):
            bank_name = b
            break
    try:
        conn = get_bank_connection(bank_name)
        profile = get_stored_account_risk_profile(conn, bank_name, account_id)
        conn.close()
        return profile
    except Exception as e:
        return {
            "account_id": account_id,
            "bank_name": bank_name,
            "risk_score": 15.0,
            "risk_level": "LOW",
            "risk_factors": ["Default baseline profile"],
            "last_updated": "now",
        }

