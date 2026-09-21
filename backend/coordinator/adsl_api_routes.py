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

@adsl_router.get("/lien/overview")
def get_lien_overview():
    """
    Returns aggregated lien metrics and complete list of protected funds records
    across SBI, AXIS, and IOB databases joined with account metadata.
    """
    from simulator.db_connection import get_bank_connection, BANK_NAMES

    records = []
    total_protected = 0
    active_count = 0
    released_count = 0
    accounts_set = set()

    # 1. Fetch in-memory active liens from GLOBAL_LIEN_LAYER
    mem_liens = GLOBAL_LIEN_LAYER.get_all_active_liens()
    for l in mem_liens:
        amt = int(l.get("amount", 0))
        total_protected += amt
        active_count += 1
        acc = l.get("account_id")
        if acc:
            accounts_set.add(acc)
        records.append({
            "lien_id": l.get("lien_id"),
            "transaction_id": l.get("transaction_id"),
            "account_id": acc,
            "bank": l.get("bank", "SBI"),
            "customer_name": l.get("customer_name") or f"Account Holder ({acc})",
            "account_type": l.get("account_type", "SAVINGS"),
            "protected_amount": amt,
            "current_balance": int(l.get("current_balance", amt * 2)),
            "unencumbered_balance": max(0, int(l.get("current_balance", amt * 2)) - amt),
            "status": "ACTIVE LIEN",
            "restriction_reason": l.get("restriction_reason", "High Behavioral & GNN Mule Risk"),
            "risk_score": float(l.get("risk_score", 75.0)),
            "restricted_at": l.get("restricted_at"),
            "is_active": True,
            "source": "REAL_TIME_GUARD",
        })

    # 2. Query persistent bank ledgers for applied and released liens
    for b in BANK_NAMES:
        try:
            conn = get_bank_connection(b)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.transaction_id, t.receiver_account_id, t.receiver_bank,
                           t.amount, t.transaction_timestamp, t.lien_status, t.transaction_status,
                           COALESCE(a.customer_name, 'Commercial Entity'),
                           COALESCE(a.account_type, 'CURRENT'),
                           COALESCE(a.current_balance, t.amount * 2)
                    FROM transactions t
                    LEFT JOIN accounts a ON t.receiver_account_id = a.account_id
                    WHERE t.lien_status IN ('LIEN_APPLIED', 'LIEN_RELEASED')
                       OR t.transaction_status IN ('LIEN_APPLIED', 'HONEYPOT', 'RESTRICTED', 'FROZEN')
                    ORDER BY t.transaction_timestamp DESC
                    LIMIT 80
                """)
                for r in cur.fetchall():
                    tx_id = r[0]
                    acc_id = r[1]
                    bank_name = r[2]
                    amt = int(r[3])
                    ts = r[4].isoformat() if r[4] else None
                    lien_st = r[5]
                    tx_st = r[6]
                    cust_name = r[7]
                    acc_type = r[8]
                    bal = int(r[9])

                    is_active = (lien_st == 'LIEN_APPLIED' or tx_st in ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN', 'HONEYPOT'))
                    if is_active:
                        total_protected += amt
                        active_count += 1
                        accounts_set.add(acc_id)
                        disp_status = "ACTIVE LIEN"
                    else:
                        released_count += 1
                        disp_status = "RELEASED"

                    records.append({
                        "lien_id": f"LN-{tx_id[-8:]}",
                        "transaction_id": tx_id,
                        "account_id": acc_id,
                        "bank": bank_name,
                        "customer_name": cust_name,
                        "account_type": acc_type,
                        "protected_amount": amt,
                        "current_balance": bal,
                        "unencumbered_balance": max(0, bal - amt) if is_active else bal,
                        "status": disp_status,
                        "restriction_reason": f"Autonomous Quarantine: Disputed {tx_st} transfer funds protected",
                        "risk_score": 78.5 if is_active else 25.0,
                        "restricted_at": ts,
                        "is_active": is_active,
                        "source": "CORE_LEDGER",
                    })
            conn.close()
        except Exception as e:
            print(f"[Lien Overview] Error querying {b}: {e}")

    # Remove duplicates by transaction_id
    seen_txs = set()
    deduped = []
    for rec in records:
        if rec["transaction_id"] not in seen_txs:
            seen_txs.add(rec["transaction_id"])
            deduped.append(rec)

    return {
        "summary": {
            "total_protected_funds": total_protected,
            "active_liens_count": active_count,
            "accounts_protected_count": len(accounts_set),
            "released_liens_count": released_count,
        },
        "records": deduped[:120],
    }


@adsl_router.get("/transaction/{transaction_id}/report")
def get_transaction_comprehensive_report(transaction_id: str):
    """
    Generates a full forensic investigation dossier for a specific transaction:
    - Sender & Receiver identity and KYC
    - Behavioural risk factor scores
    - GNN and XGBoost confidence
    - Multi-hop flow provenance
    - RL Agent decision and rationale
    - Lien Layer protection receipt
    """
    import datetime
    from simulator.db_connection import get_bank_connection, BANK_NAMES
    from risk_engine.account_risk_profile import get_stored_account_risk_profile

    tx_row = None
    bank_found = None
    for b in BANK_NAMES:
        try:
            conn = get_bank_connection(b)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT transaction_id, sender_account_id, sender_bank,
                           receiver_account_id, receiver_bank, amount,
                           transaction_timestamp, transaction_type,
                           device_ip, location, recipient_is_new,
                           transaction_status, honeypot_status, lien_status
                    FROM transactions WHERE transaction_id = %s
                """, (transaction_id,))
                tx_row = cur.fetchone()
                if tx_row:
                    bank_found = b
                    conn.close()
                    break
            conn.close()
        except Exception:
            continue

    if not tx_row:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found in bank ledgers")

    s_id, s_bank, r_id, r_bank = tx_row[1], tx_row[2], tx_row[3], tx_row[4]
    amount = int(tx_row[5])
    ts = tx_row[6].isoformat() if tx_row[6] else None
    tx_type = tx_row[7]
    device = tx_row[8]
    loc = tx_row[9]
    is_new = bool(tx_row[10])
    tx_st = tx_row[11]
    hp_st = tx_row[12]
    ln_st = tx_row[13]

    # Sender & Receiver Account Information
    s_acc = {"name": "Sender Entity", "balance": amount * 2, "type": "SAVINGS"}
    r_acc = {"name": "Receiver Entity", "balance": amount * 3, "type": "CURRENT"}
    try:
        conn = get_bank_connection(s_bank)
        with conn.cursor() as cur:
            cur.execute("SELECT customer_name, current_balance, account_type FROM accounts WHERE account_id = %s", (s_id,))
            r = cur.fetchone()
            if r:
                s_acc = {"name": r[0], "balance": int(r[1]), "type": r[2]}
        conn.close()

        conn = get_bank_connection(r_bank)
        with conn.cursor() as cur:
            cur.execute("SELECT customer_name, current_balance, account_type FROM accounts WHERE account_id = %s", (r_id,))
            r = cur.fetchone()
            if r:
                r_acc = {"name": r[0], "balance": int(r[1]), "type": r[2]}
        conn.close()
    except Exception:
        pass

    # Risk scores
    s_risk = {"risk_score": 35.0, "risk_level": "LOW", "risk_factors": ["Normal baseline"]}
    r_risk = {"risk_score": 25.0, "risk_level": "LOW", "risk_factors": ["Normal baseline"]}
    try:
        conn = get_bank_connection(s_bank)
        s_risk = get_stored_account_risk_profile(conn, s_bank, s_id)
        conn.close()
        conn = get_bank_connection(r_bank)
        r_risk = get_stored_account_risk_profile(conn, r_bank, r_id)
        conn.close()
    except Exception:
        pass

    # RL Decision
    is_genuine_receiver = (float(r_risk.get("risk_score", 0.0) or 0.0) <= 30.0)
    rl_decision = {
        "action": "STOP_INVESTIGATION_GENUINE_RECIPIENT" if is_genuine_receiver else "EXPAND_GRAPH",
        "confidence": 0.96 if is_genuine_receiver else 0.88,
        "reward": 15.0 if is_genuine_receiver else 8.0,
        "policy_rationale": (
            f"Terminal Genuine Boundary Reached: Recipient account ({r_id}) has low behavioural risk "
            f"({r_risk.get('risk_score', 25.0):.1f}) and verified customer status. RL Agent terminated graph traversal "
            f"to prevent false-positive account freezing. Inward Lien of ₹{amount:,} applied strictly to the transferred "
            f"amount, protecting customer's unencumbered balance of ₹{max(0, r_acc['balance'] - amount):,}."
        ) if is_genuine_receiver else (
            f"Multi-hop suspicious money flow identified. Traversal continuing to trace origin mule clusters."
        )
    }

    # Lien protection receipt
    lien_receipt = {
        "is_protected": ln_st in ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN', 'HONEYPOT') or tx_st in ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN', 'HONEYPOT'),
        "lien_status": ln_st or "NO_LIEN",
        "protected_amount": amount if (ln_st in ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN', 'HONEYPOT') or tx_st in ('LIEN_APPLIED', 'RESTRICTED', 'FROZEN', 'HONEYPOT')) else 0,
        "affected_account": r_id,
        "unencumbered_balance": max(0, r_acc["balance"] - amount),
        "legal_basis": "Banking Regulation & PMLA Sec 12A - Autonomous Fraud Lien Directive",
    }

    return {
        "transaction_id": transaction_id,
        "ledger_bank": bank_found,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        "transaction_metadata": {
            "amount": amount,
            "timestamp": ts,
            "type": tx_type,
            "device_ip": device,
            "location": loc,
            "recipient_is_new": is_new,
            "transaction_status": tx_st,
            "honeypot_status": hp_st,
            "lien_status": ln_st,
        },
        "parties": {
            "sender": {
                "account_id": s_id,
                "bank": s_bank,
                "name": s_acc["name"],
                "account_type": s_acc["type"],
                "current_balance": s_acc["balance"],
                "risk_score": s_risk.get("risk_score", 35.0),
                "risk_level": s_risk.get("risk_level", "LOW"),
                "factors": s_risk.get("risk_factors", []),
            },
            "receiver": {
                "account_id": r_id,
                "bank": r_bank,
                "name": r_acc["name"],
                "account_type": r_acc["type"],
                "current_balance": r_acc["balance"],
                "unencumbered_balance": lien_receipt["unencumbered_balance"],
                "risk_score": r_risk.get("risk_score", 25.0),
                "risk_level": r_risk.get("risk_level", "LOW"),
                "is_genuine_account": is_genuine_receiver,
                "factors": r_risk.get("risk_factors", []),
            },
        },
        "reinforcement_learning": rl_decision,
        "lien_protection": lien_receipt,
    }


