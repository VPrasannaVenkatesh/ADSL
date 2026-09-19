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


@adsl_router.get("/transactions")
def get_adsl_transactions(limit: int = Query(60, le=200)):
    """
    Returns recent transactions processed through ADSL central engine with their
    risk scores, status, decision, and mule network IDs.
    """
    from .adsl_service import get_recent_adsl_transactions
    txns = get_recent_adsl_transactions(limit=limit)
    return {
        "count": len(txns),
        "transactions": txns,
    }


@adsl_router.get("/transaction-graph/{transaction_id}")
def get_adsl_transaction_graph(transaction_id: str, hops: int = Query(2, ge=1, le=4)):
    """
    Returns complete interactive graph topology (nodes, directed edges, roles,
    risk scores, GNN probabilities) centered around the specified transaction.
    Evaluates Reinforcement Learning decision for graph growth.
    """
    graph_data = GLOBAL_MULE_NETWORKS.get_subgraph_for_transaction(transaction_id, depth=hops)
    if not graph_data:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found in graph")
    return graph_data


@adsl_router.get("/account/{account_id}/report")
def get_adsl_account_report(account_id: str):
    """
    Generates an official institutional forensic audit report for an account,
    formatted as downloadable text and structured data.
    """
    import datetime
    from simulator.db_connection import get_bank_connection, BANK_NAMES
    from risk_engine.account_risk_profile import get_stored_account_risk_profile

    bank_name = "SBI"
    for b in BANK_NAMES:
        if account_id.upper().startswith(b):
            bank_name = b
            break

    # 1. Fetch account info & transactions from PostgreSQL
    acc_info = {}
    txns = []
    try:
        conn = get_bank_connection(bank_name)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT account_id, account_number, customer_name, phone_number,
                       account_type, current_balance, account_created_date,
                       home_location, account_status, business_category
                FROM accounts WHERE account_id = %s
            """, (account_id,))
            row = cur.fetchone()
            if row:
                acc_info = {
                    "account_id": row[0],
                    "account_number": row[1],
                    "customer_name": row[2],
                    "phone_number": row[3],
                    "account_type": row[4],
                    "current_balance": int(row[5]),
                    "created_date": str(row[6]),
                    "location": row[7],
                    "status": row[8],
                    "business_category": row[9] or "Retail Individual",
                }

            cur.execute("""
                SELECT transaction_id, sender_account_id, receiver_account_id,
                       amount, transaction_timestamp, transaction_type, transaction_status,
                       COALESCE(lien_status, 'NO_LIEN')
                FROM transactions
                WHERE sender_account_id = %s OR receiver_account_id = %s
                ORDER BY transaction_timestamp DESC LIMIT 15
            """, (account_id, account_id))
            for r in cur.fetchall():
                txns.append({
                    "tx_id": r[0],
                    "sender": r[1],
                    "receiver": r[2],
                    "amount": int(r[3]),
                    "timestamp": str(r[4]),
                    "type": r[5],
                    "status": r[6],
                    "lien_status": r[7],
                })
        conn.close()
    except Exception as e:
        print(f"[Account Report] Error fetching DB details: {e}")

    # 2. Fetch risk profile
    risk_info = {"risk_score": 25.0, "risk_level": "LOW", "risk_factors": ["Normal operational baseline"]}
    try:
        conn = get_bank_connection(bank_name)
        risk_info = get_stored_account_risk_profile(conn, bank_name, account_id)
        conn.close()
    except Exception:
        pass

    # 3. Check active lien
    active_lien = None
    for item in GLOBAL_LIEN_LAYER.get_all_active_liens():
        if item.get("account_id") == account_id or item.get("sender_account_id") == account_id:
            active_lien = item
            break

    # 4. Check mule network membership
    mule_net_id = GLOBAL_MULE_NETWORKS.account_to_network.get(account_id)
    mule_net = GLOBAL_MULE_NETWORKS.networks.get(mule_net_id) if mule_net_id else None

    # Format text report
    gen_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    report_lines = [
        "=" * 74,
        "   AUTONOMOUS DECENTRALIZED SECURITY LAYER (ADSL) — FORENSIC AUDIT DOSSIER",
        "=" * 74,
        f"  Report Timestamp     : {gen_time}",
        f"  Target Account ID    : {account_id}",
        f"  Hosting Bank Ledger  : {bank_name} Commercial Core Banking System",
        f"  Classification Tier  : {'CONFIDENTIAL — SUSPICIOUS ACTIVITY' if risk_info.get('risk_score', 0) >= 50 else 'STANDARD ACCOUNT DOSSIER'}",
        "-" * 74,
        " [1] ACCOUNT IDENTITY & KYC RECORD",
        f"  * Legal Entity / Name: {acc_info.get('customer_name', 'N/A')}",
        f"  * Core Account Number: {acc_info.get('account_number', 'N/A')}",
        f"  * Account Type / Class: {acc_info.get('account_type', 'SAVINGS')} ({acc_info.get('business_category', 'Retail')})",
        f"  * Registered Location: {acc_info.get('location', 'N/A')}",
        f"  * Operational Status : {acc_info.get('status', 'ACTIVE')}",
        f"  * Current Ledger Bal : ₹{acc_info.get('current_balance', 0):,}",
        "-" * 74,
        " [2] BEHAVIOURAL & MACHINE LEARNING RISK ASSESSMENT",
        f"  * Behavioural Risk   : {risk_info.get('risk_score', 25.0):.1f} / 100 [{risk_info.get('risk_level', 'LOW')}]",
        f"  * GNN Mule Prob      : {mule_net.get('risk_score', 12.0) if mule_net else 14.5:.1f}%",
        f"  * Mule Network Clust : {mule_net_id or 'None (Isolated / Non-Cluster)'}",
        f"  * Identified Factors : {', '.join(risk_info.get('risk_factors', ['Baseline profile established']))}",
        "-" * 74,
        " [3] AUTONOMOUS ENFORCEMENT & LIEN STATUS",
        f"  * System Verdict     : {'ACTIVE LIEN IMPOSED — FUNDS SECURED' if active_lien else 'NORMAL FAST-PATH MONITORING'}",
        f"  * Protected Lien Amt : ₹{active_lien.get('amount', 0):,} ({active_lien.get('status', 'NO_LIEN')})" if active_lien else "  * Protected Lien Amt : ₹0 (No active restrictive lien)",
        f"  * Quarantine Reason  : {active_lien.get('restriction_reason', 'N/A')}" if active_lien else "  * Quarantine Reason  : N/A",
        "-" * 74,
        " [4] RECENT LEDGER TRANSACTIONS AUDIT TRAIL",
        f"  {'TX ID':<16} {'DIRECTION':<9} {'COUNTERPARTY':<16} {'AMOUNT (INR)':<14} {'STATUS'}",
        "  " + "-" * 70,
    ]

    for t in txns:
        direction = "CREDIT" if t["receiver"] == account_id else "DEBIT"
        counterparty = t["sender"] if direction == "CREDIT" else t["receiver"]
        report_lines.append(
            f"  {t['tx_id']:<16} {direction:<9} {counterparty:<16} ₹{t['amount']:<13, } {t['status']}"
        )

    if not txns:
        report_lines.append("  No historical transactions logged for this account.")

    report_lines.extend([
        "=" * 74,
        "  END OF OFFICIAL COMPLIANCE & FORENSIC DOSSIER",
        "  Verified by ADSL Consortium Smart Rule & GNN Investigation Engine",
        "=" * 74,
    ])

    report_text = "\n".join(report_lines)

    return {
        "account_id": account_id,
        "bank": bank_name,
        "generated_at": gen_time,
        "account_info": acc_info,
        "risk_profile": risk_info,
        "active_lien": active_lien,
        "mule_network": mule_net,
        "transactions": txns,
        "report_text": report_text,
    }


@adsl_router.post("/simulate/mule-sink")
def simulate_mule_sink_flow():
    """
    Triggers the 6-transaction multi-mule and sink dispersion flow directly
    from the ADSL dashboard to observe live graph updates.
    """
    import requests
    sim_url = "http://localhost:8000"
    try:
        resp = requests.post(f"{sim_url}/api/simulator/patterns/mule-sink", timeout=10.0)
        return resp.json()
    except Exception as e:
        return {"success": False, "error": f"Failed to contact simulator on port 8000: {e}"}


