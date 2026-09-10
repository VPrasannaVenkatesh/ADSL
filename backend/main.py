"""
FastAPI Backend Application for Multi-Bank Live Transaction Simulation & Behavioural Analytics.
Direct PostgreSQL access via psycopg2 across sbi_db, axis_db, and iob_db.
"""

import os
import sys
from datetime import datetime, date
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from simulator.config import (
    SimulatorConfig,
    BANK_NAMES,
    SPEED_PRESETS,
    SIMULATION_MIX_MODES,
    DEFAULT_SIMULATION_MIX,
    TRANSACTION_STATUSES,
    HONEYPOT_STATUSES,
    LIEN_STATUSES,
)
from simulator.engine import LiveTransactionSimulator
from simulator.db import get_connection, get_all_connections

simulator_instance: Optional[LiveTransactionSimulator] = None

def get_or_init_simulator() -> LiveTransactionSimulator:
    global simulator_instance
    if simulator_instance is None:
        config = SimulatorConfig(mode="normal", total_count=0, mix_mode=DEFAULT_SIMULATION_MIX)
        simulator_instance = LiveTransactionSimulator(config)
    return simulator_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[SERVER] Initializing and Starting Live Transaction Simulator...")
    sim = get_or_init_simulator()
    sim.start_background()
    yield
    print("[SERVER] Shutting down Live Transaction Simulator...")
    if simulator_instance:
        simulator_instance.close()


app = FastAPI(
    title="Transaction Simulator API",
    description="Multi-Bank Live Transaction Simulator & Single Bank Ledger Engine (Port 8000)",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from risk_engine.api_routes import router as risk_router
from coordinator.api_routes import coordinator_router
from coordinator.bank_endpoints import bank_risk_share_router
from coordinator.adsl_api_routes import adsl_router
from network_monitoring.api_routes import network_router
from xgboost_risk.api_routes import xgboost_router
from xgboost_risk.schema import initialize_xgboost_tables
from gnn_detection.api import gnn_router
from gnn_detection.schema import initialize_gnn_tables

app.include_router(risk_router)
app.include_router(coordinator_router)
app.include_router(bank_risk_share_router)
app.include_router(adsl_router)
app.include_router(network_router)
app.include_router(xgboost_router)
app.include_router(gnn_router)


@app.on_event("startup")
def on_startup():
    try:
        initialize_xgboost_tables()
    except Exception as e:
        print(f"[STARTUP] XGBoost table init: {e}")
    try:
        initialize_gnn_tables()
    except Exception as e:
        print(f"[STARTUP] GNN table init: {e}")
    try:
        from gnn_detection.predictor import GLOBAL_GNN_PREDICTOR
        print(f"[STARTUP] GNN Predictor status: {GLOBAL_GNN_PREDICTOR.get_status()['status']}")
    except Exception as e:
        print(f"[STARTUP] GNN predictor load: {e}")


# Request / Response Models

class StartRequest(BaseModel):
    mode: Optional[str] = "normal"
    delay: Optional[float] = None
    mix_mode: Optional[str] = "balanced"


class SpeedRequest(BaseModel):
    speed: Optional[str] = None
    delay: Optional[float] = None


class MixRequest(BaseModel):
    mix_mode: Optional[str] = "balanced"


# Core Simulator Control Endpoints

@app.get("/api/status")
def get_simulator_status():
    """Returns the current state and speed mode of the simulator."""
    sim = get_or_init_simulator()
    return {
        "is_running": sim.is_running,
        "is_paused": sim.is_paused,
        "mode": sim.config.mode,
        "mix_mode": getattr(sim.config, "mix_mode", "balanced"),
        "loop_delay": sim.config.loop_delay,
        "active_bank": sim.active_bank,
        "sim_clock": sim.sim_clock.isoformat(),
        "stats": sim.stats,
    }


@app.get("/api/simulator/active-bank")
def get_active_bank_endpoint():
    """Returns the currently active bank ledger and connectivity."""
    sim = get_or_init_simulator()
    return sim.get_active_bank_status()


@app.post("/api/simulator/active-bank")
def set_active_bank_endpoint(req: dict):
    """Sets active bank ledger ('ALL', 'SBI', 'AXIS', 'IOB')."""
    bank = req.get("bank")
    if not bank:
        raise HTTPException(status_code=400, detail="Missing bank field")
    sim = get_or_init_simulator()
    return sim.set_active_bank(bank)


@app.post("/api/simulator/start")
def start_simulator(req: Optional[StartRequest] = None):
    """Starts the continuous transaction simulation background loop."""
    sim = get_or_init_simulator()
    if req:
        if req.mode and req.mode in SPEED_PRESETS:
            sim.set_speed_preset(req.mode)
        if req.delay is not None:
            sim.set_custom_delay(req.delay)
        if req.mix_mode and req.mix_mode.lower() in SIMULATION_MIX_MODES:
            sim.set_simulation_mix(req.mix_mode.lower())

    sim.start_background()
    return {
        "status": "started",
        "mode": sim.config.mode,
        "mix_mode": sim.config.mix_mode,
        "loop_delay": sim.config.loop_delay,
    }


@app.post("/api/simulator/pause")
def pause_simulator():
    """Pauses transaction generation."""
    sim = get_or_init_simulator()
    sim.pause()
    return {"status": "paused"}


@app.post("/api/simulator/resume")
def resume_simulator():
    """Resumes transaction generation."""
    sim = get_or_init_simulator()
    sim.resume()
    return {"status": "running"}


@app.post("/api/simulator/stop")
def stop_simulator():
    """Stops the simulator loop."""
    sim = get_or_init_simulator()
    sim.stop()
    return {"status": "stopped"}


@app.post("/api/simulator/speed")
def set_simulator_speed(req: SpeedRequest):
    """Adjusts simulation speed preset or custom delay."""
    sim = get_or_init_simulator()
    if req.speed and req.speed in SPEED_PRESETS:
        sim.set_speed_preset(req.speed)
    elif req.delay is not None:
        sim.set_custom_delay(req.delay)

    return {
        "status": "updated",
        "mode": sim.config.mode,
        "loop_delay": sim.config.loop_delay,
    }


@app.post("/api/simulator/mix")
def set_simulator_mix(req: MixRequest):
    """Sets transaction mix mode: 'balanced', 'normal', 'business', 'mule'."""
    sim = get_or_init_simulator()
    mix = (req.mix_mode or "balanced").lower()
    return sim.set_simulation_mix(mix)


# Live & Historical Transaction Endpoints

@app.get("/api/transactions/live")
def get_live_transactions(limit: int = Query(50, ge=1, le=200), bank: Optional[str] = None):
    """
    Returns recent live transactions from memory buffer (with fallback to DB).
    Includes honeypot_status and lien_status.
    """
    sim = get_or_init_simulator()
    txns = sim.recent_transactions
    if bank and bank.upper() in BANK_NAMES:
        b = bank.upper()
        txns = [t for t in txns if t["sender_bank"] == b or t["receiver_bank"] == b]

    if not txns:
        txns = []
        for b_name in BANK_NAMES:
            conn = get_connection(b_name)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT transaction_id, sender_account_id, sender_bank,
                           receiver_account_id, receiver_bank,
                           amount, transaction_timestamp, transaction_type,
                           sender_balance_before, sender_balance_after,
                           receiver_balance_before, receiver_balance_after,
                           device_ip, location, recipient_is_new,
                           transaction_status,
                           COALESCE(honeypot_status, 'NOT_TRANSFERRED'),
                           COALESCE(lien_status, 'NO_LIEN')
                    FROM transactions
                    ORDER BY id DESC LIMIT 25
                """)
                for r in cur.fetchall():
                    txns.append({
                        "transaction_id": r[0],
                        "sender_account_id": r[1],
                        "sender_bank": r[2],
                        "receiver_account_id": r[3],
                        "receiver_bank": r[4],
                        "amount": r[5],
                        "transaction_timestamp": r[6].isoformat() if r[6] else None,
                        "transaction_type": r[7],
                        "sender_balance_before": r[8],
                        "sender_balance_after": r[9],
                        "receiver_balance_before": r[10],
                        "receiver_balance_after": r[11],
                        "device_ip": r[12],
                        "location": r[13],
                        "recipient_is_new": r[14],
                        "transaction_status": r[15] or "COMPLETED",
                        "honeypot_status": r[16] or "NOT_TRANSFERRED",
                        "lien_status": r[17] or "NO_LIEN",
                        "is_cross_bank": (r[2] != r[4]),
                    })
            conn.close()

        seen = set()
        deduped = []
        for t in sorted(txns, key=lambda x: x["transaction_timestamp"] or "", reverse=True):
            if t["transaction_id"] not in seen:
                seen.add(t["transaction_id"])
                deduped.append(t)
        txns = deduped

    return {"transactions": txns[:limit], "count": len(txns[:limit])}


@app.get("/api/transactions")
def query_transactions(
    bank: str = Query("ALL", pattern="^(ALL|SBI|AXIS|IOB)$"),
    account_id: Optional[str] = None,
    tx_type: Optional[str] = None,
    status: Optional[str] = None,
    cross_bank_only: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Queries historical and live transactions across bank databases with filters.
    """
    target_banks = [bank] if bank != "ALL" else BANK_NAMES
    all_rows = []

    for b in target_banks:
        conn = get_connection(b)
        with conn.cursor() as cur:
            query = """
                SELECT transaction_id, sender_account_id, sender_bank,
                       receiver_account_id, receiver_bank,
                       amount, transaction_timestamp, transaction_type,
                       device_ip, location, recipient_is_new,
                       transaction_status, simulation_source,
                       COALESCE(honeypot_status, 'NOT_TRANSFERRED'),
                       COALESCE(lien_status, 'NO_LIEN')
                FROM transactions
                WHERE 1=1
            """
            params = []
            if account_id:
                query += " AND (sender_account_id = %s OR receiver_account_id = %s)"
                params.extend([account_id, account_id])
            if tx_type:
                query += " AND transaction_type = %s"
                params.append(tx_type)
            if status:
                query += " AND transaction_status = %s"
                params.append(status)
            if cross_bank_only:
                query += " AND sender_bank <> receiver_bank"

            query += f" ORDER BY transaction_timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            for r in cur.fetchall():
                all_rows.append({
                    "transaction_id": r[0],
                    "sender_account_id": r[1],
                    "sender_bank": r[2],
                    "receiver_account_id": r[3],
                    "receiver_bank": r[4],
                    "amount": r[5],
                    "transaction_timestamp": r[6].isoformat() if r[6] else None,
                    "transaction_type": r[7],
                    "device_ip": r[8],
                    "location": r[9],
                    "recipient_is_new": r[10],
                    "transaction_status": r[11] or "COMPLETED",
                    "simulation_source": r[12],
                    "honeypot_status": r[13] or "NOT_TRANSFERRED",
                    "lien_status": r[14] or "NO_LIEN",
                    "is_cross_bank": (r[2] != r[4]),
                })
        conn.close()

    seen = set()
    deduped = []
    for r in sorted(all_rows, key=lambda x: x["transaction_timestamp"] or "", reverse=True):
        if r["transaction_id"] not in seen:
            seen.add(r["transaction_id"])
            deduped.append(r)

    return {"transactions": deduped[:limit], "count": len(deduped[:limit])}


# Bank & Account Analytics Endpoints

@app.get("/api/banks/stats")
def get_bank_summary_stats():
    """
    Returns aggregated summary stats across SBI, AXIS, and IOB databases.
    Includes connection status, database status, and active transaction counts.
    """
    sim = get_or_init_simulator()
    sim_stats = sim.stats if sim else {}

    stats_by_bank = {}
    total_txns = 0
    total_vol = 0
    total_accs = 0

    for b in BANK_NAMES:
        conn = get_connection(b)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COALESCE(SUM(current_balance), 0) FROM accounts")
            acc_count, total_bal = cur.fetchone()

            cur.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(amount), 0),
                       COUNT(*) FILTER (WHERE sender_bank = receiver_bank),
                       COUNT(*) FILTER (WHERE sender_bank <> receiver_bank),
                       MAX(transaction_timestamp),
                       COUNT(*) FILTER (WHERE transaction_status = 'COMPLETED'),
                       COUNT(*) FILTER (WHERE transaction_status = 'MONITORING'),
                       COUNT(*) FILTER (WHERE transaction_status = 'HONEYPOT' OR honeypot_status = 'TRANSFERRED'),
                       COUNT(*) FILTER (WHERE transaction_status IN ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN') OR lien_status = 'LIEN_APPLIED'),
                       COALESCE(SUM(amount) FILTER (WHERE transaction_status IN ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN') OR lien_status = 'LIEN_APPLIED'), 0)
                FROM transactions
            """)
            (tx_count, vol, intra_count, cross_count, latest_ts,
             c_count, m_count, h_count, l_count, l_amount) = cur.fetchone()

            stats_by_bank[b] = {
                "bank_name": b,
                "connection_status": "CONNECTED",
                "database_name": f"{b.lower()}_db",
                "accounts": acc_count,
                "total_balance": int(total_bal),
                "transactions": tx_count,
                "active_transactions": tx_count,
                "volume": int(vol),
                "intra_bank": intra_count,
                "cross_bank": cross_count,
                "latest_timestamp": latest_ts.isoformat() if latest_ts else None,
                "completed": c_count,
                "monitoring": m_count,
                "honeypot": h_count,
                "lien_protected_count": l_count,
                "lien_protected_amount": int(l_amount),
            }
            total_accs += acc_count
            total_txns += tx_count
            total_vol += vol
        conn.close()

    # Aggregate simulator in-memory counts with database counts
    completed = sum(b_data["completed"] for b_data in stats_by_bank.values())
    monitoring = sum(b_data["monitoring"] for b_data in stats_by_bank.values())
    honeypot = sum(b_data["honeypot"] for b_data in stats_by_bank.values())
    lien_count = sum(b_data["lien_protected_count"] for b_data in stats_by_bank.values())
    lien_amt = sum(b_data["lien_protected_amount"] for b_data in stats_by_bank.values())

    return {
        "total_accounts": total_accs,
        "total_transactions": total_txns,
        "total_volume": int(total_vol),
        "completed": completed,
        "monitoring": monitoring,
        "honeypot": honeypot,
        "lien_protected_count": lien_count,
        "lien_protected_amount": int(lien_amt),
        "banks": stats_by_bank,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/accounts")
def get_accounts_list(
    bank: str = Query("ALL", pattern="^(ALL|SBI|AXIS|IOB)$"),
    account_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Returns account directory for account explorer."""
    target_banks = [bank] if bank != "ALL" else BANK_NAMES
    accounts = []

    for b in target_banks:
        conn = get_connection(b)
        with conn.cursor() as cur:
            query = """
                SELECT account_id, account_number, customer_name,
                       phone_number, account_type, current_balance,
                       account_created_date, home_location, account_status,
                       business_category, expected_tx_range, tx_frequency_pattern
                FROM accounts WHERE 1=1
            """
            params = []
            if account_type:
                query += " AND account_type = %s"
                params.append(account_type)
            if search:
                query += " AND (account_id ILIKE %s OR customer_name ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])

            query += " ORDER BY account_id LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            for r in cur.fetchall():
                accounts.append({
                    "account_id": r[0],
                    "account_number": r[1],
                    "customer_name": r[2],
                    "phone_number": r[3],
                    "account_type": r[4],
                    "current_balance": int(r[5]),
                    "account_created_date": r[6].isoformat() if r[6] else None,
                    "home_location": r[7],
                    "account_status": r[8],
                    "business_category": r[9],
                    "expected_tx_range": r[10],
                    "tx_frequency_pattern": r[11],
                    "bank": b,
                })
        conn.close()

    return {"accounts": accounts[:limit], "count": len(accounts[:limit])}


@app.get("/api/accounts/{bank}/{account_id}")
def get_account_profile(bank: str, account_id: str):
    """
    Returns account details, business profile, and transaction history.
    Does NOT calculate or expose ML risk scores (XGBoost/GNN).
    """
    b = bank.upper()
    if b not in BANK_NAMES:
        raise HTTPException(status_code=400, detail="Invalid bank")

    conn = get_connection(b)
    try:
        with conn.cursor() as cur:
            # 1. Account info
            cur.execute("""
                SELECT account_id, account_number, customer_name,
                       phone_number, account_type, current_balance,
                       account_created_date, home_location, account_status,
                       business_category, expected_tx_range, tx_frequency_pattern
                FROM accounts WHERE account_id = %s
            """, (account_id,))
            acc_row = cur.fetchone()
            if not acc_row:
                raise HTTPException(status_code=404, detail="Account not found")

            account_data = {
                "account_id": acc_row[0],
                "account_number": acc_row[1],
                "customer_name": acc_row[2],
                "phone_number": acc_row[3],
                "account_type": acc_row[4],
                "current_balance": int(acc_row[5]),
                "account_created_date": acc_row[6].isoformat() if acc_row[6] else None,
                "home_location": acc_row[7],
                "account_status": acc_row[8],
                "business_category": acc_row[9] or ("Commercial Merchant" if acc_row[4] == "BUSINESS" else None),
                "expected_tx_range": acc_row[10] or ("₹25,000 - ₹10,00,000" if acc_row[4] == "BUSINESS" else "₹100 - ₹50,000"),
                "tx_frequency_pattern": acc_row[11] or ("Regular B2B and vendor transactions" if acc_row[4] == "BUSINESS" else "Standard personal transfers"),
                "bank": b,
            }

            # 2. Transaction Summary stats
            cur.execute("""
                SELECT 
                    COUNT(*),
                    COALESCE(SUM(amount) FILTER (WHERE sender_account_id = %s), 0),
                    COALESCE(SUM(amount) FILTER (WHERE receiver_account_id = %s), 0)
                FROM transactions
                WHERE sender_account_id = %s OR receiver_account_id = %s
            """, (account_id, account_id, account_id, account_id))
            tx_sum_row = cur.fetchone()
            tx_summary = {
                "transaction_count": tx_sum_row[0] if tx_sum_row else 0,
                "total_sent": int(tx_sum_row[1]) if tx_sum_row else 0,
                "total_received": int(tx_sum_row[2]) if tx_sum_row else 0,
            }

            # 3. Recent 15 Transactions
            cur.execute("""
                SELECT transaction_id, sender_account_id, sender_bank,
                       receiver_account_id, receiver_bank,
                       amount, transaction_timestamp, transaction_type,
                       device_ip, location, transaction_status,
                       COALESCE(honeypot_status, 'NOT_TRANSFERRED'),
                       COALESCE(lien_status, 'NO_LIEN')
                FROM transactions
                WHERE sender_account_id = %s OR receiver_account_id = %s
                ORDER BY transaction_timestamp DESC LIMIT 15
            """, (account_id, account_id))
            tx_rows = cur.fetchall()
            recent_txns = []
            for r in tx_rows:
                recent_txns.append({
                    "transaction_id": r[0],
                    "sender_account_id": r[1],
                    "sender_bank": r[2],
                    "receiver_account_id": r[3],
                    "receiver_bank": r[4],
                    "amount": r[5],
                    "transaction_timestamp": r[6].isoformat() if r[6] else None,
                    "transaction_type": r[7],
                    "device_ip": r[8],
                    "location": r[9],
                    "transaction_status": r[10] or "COMPLETED",
                    "honeypot_status": r[11] or "NOT_TRANSFERRED",
                    "lien_status": r[12] or "NO_LIEN",
                    "is_outgoing": (r[1] == account_id),
                })

            return {
                "account": account_data,
                "transaction_summary": tx_summary,
                "recent_transactions": recent_txns,
            }
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
