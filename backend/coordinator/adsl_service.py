"""
ADSL Central Intelligent Transaction Processing Service.
Coordinates the end-to-end intelligent transaction pipeline:
- Receives transaction (INITIATED -> PROCESSING)
- Fetches stored sender and receiver risk profiles from Bank Risk Provider
- Evaluates allow thresholds (Combined Risk < 30 -> ALLOW -> COMPLETED without GNN/Graph)
- For suspicious transactions (>= 30):
  - Network Graph Analysis
  - Fund Provenance Analysis
  - Live GNN Inference (Pre-trained model, zero retraining)
  - Mule Network Clustering & Grouping
  - Under Review / Lien Layer hold
- Provides Admin Investigation actions (RELEASE, MONITOR, RESTRICT, FREEZE)
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
from network_monitoring.fund_provenance import trace_fund_provenance
from network_monitoring.lien_layer import GLOBAL_LIEN_LAYER
from .mule_network_manager import GLOBAL_MULE_NETWORKS
import threading

# Configurable Thresholds per Architecture Specification
ALLOW_THRESHOLD = 30.0
MONITOR_THRESHOLD = 50.0
REVIEW_THRESHOLD = 70.0
RESTRICT_THRESHOLD = 85.0

BANK_RISK_API_URL = os.environ.get("BANK_RISK_API_URL", "http://localhost:8001")

RECENT_ADSL_TRANSACTIONS: List[Dict[str, Any]] = []
_adsl_tx_lock = threading.RLock()


def get_recent_adsl_transactions(limit: int = 60) -> List[Dict[str, Any]]:
    """Returns the most recent transactions processed through ADSL."""
    with _adsl_tx_lock:
        return list(RECENT_ADSL_TRANSACTIONS[:limit])


def _update_bank_tx_status(bank: str, tx_id: str, new_status: str, honeypot_status: str = "NONE", lien_status: str = "NONE"):
    """Safely updates transactions table across bank databases with status and honeypot/lien flags."""
    try:
        from simulator.db_connection import get_all_bank_connections
        conns = get_all_bank_connections()
        for b_name, conn in conns.items():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE transactions SET
                        transaction_status = %s,
                        honeypot_status = %s,
                        lien_status = %s
                    WHERE transaction_id = %s
                """, (new_status, honeypot_status, lien_status, tx_id))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[ADSL] Error updating tx status in DB: {e}")


def _fetch_account_stored_risk(account_id: str, bank_name: str) -> Dict[str, Any]:
    """
    Fetches the stored behavioural risk profile from Bank Risk API.
    Does NOT calculate risk on demand. Falls back to direct DB read if HTTP fails.
    """
    # 1. Attempt HTTP request to Bank Risk API
    try:
        resp = requests.get(
            f"{BANK_RISK_API_URL}/risk/account/{account_id}",
            timeout=1.0,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # 2. Fallback to internal direct DB fetch
    try:
        from simulator.db_connection import get_bank_connection
        from risk_engine.account_risk_profile import get_stored_account_risk_profile
        conn = get_bank_connection(bank_name)
        profile = get_stored_account_risk_profile(conn, bank_name, account_id)
        conn.close()
        return profile
    except Exception as e:
        print(f"[ADSL] Error fetching risk for {account_id}: {e}")
        return {
            "account_id": account_id,
            "bank_name": bank_name,
            "risk_score": 20.0,
            "risk_level": "LOW",
            "risk_factors": ["Default baseline"],
            "last_updated": datetime.now().isoformat(),
        }


def _compute_transaction_xgboost_risk(
    tx_data: Dict[str, Any],
    sender_risk_score: float,
    receiver_risk_score: float,
) -> Dict[str, Any]:
    """
    Evaluates transaction-level risk using the trained XGBoost model.
    Incorporates transaction features, sender/receiver behavior history, and business profile baselines.
    """
    if "xgboost_risk_score" in tx_data:
        return {
            "score": float(tx_data["xgboost_risk_score"]),
            "level": tx_data.get("risk_level", "LOW"),
            "reasons": tx_data.get("risk_reasons", ["Pre-computed XGBoost risk"]),
            "class": tx_data.get("predicted_class", "NORMAL"),
            "probability": float(tx_data.get("prediction_probability", 0.9)),
        }

    conns = {}
    try:
        from xgboost_risk.predictor import GLOBAL_PREDICTOR
        from xgboost_risk.feature_extractor import extract_features_for_transaction
        from simulator.db_connection import get_bank_connection

        sb = tx_data.get("sender_bank", "SBI")
        rb = tx_data.get("receiver_bank", "SBI")
        conns[sb] = get_bank_connection(sb)
        if rb != sb:
            conns[rb] = get_bank_connection(rb)

        ts_raw = tx_data.get("transaction_timestamp") or tx_data.get("timestamp") or datetime.now().isoformat()
        try:
            ts = datetime.fromisoformat(str(ts_raw))
        except Exception:
            ts = datetime.now()

        features = extract_features_for_transaction(
            conns=conns,
            sender_bank=sb,
            sender_account_id=tx_data.get("sender_account_id") or tx_data.get("sender_account") or tx_data.get("sender_id", ""),
            receiver_bank=rb,
            receiver_account_id=tx_data.get("receiver_account_id") or tx_data.get("receiver_account") or tx_data.get("receiver_id", ""),
            amount=int(tx_data.get("amount", 10000)),
            tx_type=tx_data.get("transaction_type", "UPI"),
            timestamp=ts,
            device_ip=tx_data.get("device_ip", "Mobile:192.168.1.1"),
            location=tx_data.get("location", "Chennai"),
            recipient_is_new=bool(tx_data.get("recipient_is_new", False)),
            sender_risk_score=sender_risk_score,
            receiver_risk_score=receiver_risk_score,
        )

        pred = GLOBAL_PREDICTOR.predict_transaction_risk(features)
        return {
            "score": float(pred["xgboost_risk_score"]),
            "level": pred["risk_level"],
            "reasons": pred["top_risk_factors"],
            "class": pred["predicted_class"],
            "probability": float(pred.get("prediction_probability", 0.9)),
            "feature_snapshot": features,
        }
    except Exception as e:
        # Fallback to combined account baseline
        combined = round((sender_risk_score * 0.5) + (receiver_risk_score * 0.5), 2)
        lvl = "LOW" if combined <= 30 else ("MEDIUM" if combined <= 60 else "HIGH")
        return {
            "score": combined,
            "level": lvl,
            "reasons": [f"Fallback heuristic baseline applied ({e})"],
            "class": "NORMAL" if combined <= 30 else ("SUSPICIOUS" if combined <= 60 else "CRITICAL_FRAUD"),
            "probability": 0.80,
        }
    finally:
        for c in conns.values():
            try:
                if c and not c.closed:
                    c.close()
            except Exception:
                pass


def process_adsl_transaction(tx_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the ADSL intelligent transaction decision flow:
    1. Status = PROCESSING
    2. Fetch stored sender & receiver account risk profiles from bank
    3. Compute transaction-level risk using XGBoost engine
    4. Tiered Threshold Routing:
       - LOW RISK (0-30): ALLOW -> COMPLETED
       - MEDIUM RISK (31-60): MONITOR -> MONITORING (Dynamic Monitoring Manager)
       - HIGH RISK (61-100): LIEN -> NetworkX -> GNN -> Mule Networks -> RL Agent
    """
    tx_id = tx_data.get("transaction_id") or f"TX_{int(datetime.now().timestamp()*1000)}"
    sender_bank = tx_data.get("sender_bank", "SBI")
    sender_id = tx_data.get("sender_account_id") or tx_data.get("sender_account") or tx_data.get("sender_id")
    receiver_bank = tx_data.get("receiver_bank", "SBI")
    receiver_id = tx_data.get("receiver_account_id") or tx_data.get("receiver_account") or tx_data.get("receiver_id")
    amount = int(tx_data.get("amount", 10000))
    tx_type = tx_data.get("transaction_type", "TRANSFER")
    timestamp_str = tx_data.get("transaction_timestamp") or tx_data.get("timestamp") or datetime.now().isoformat()
    device_ip = tx_data.get("device_ip", "Mobile:192.168.1.1")
    location = tx_data.get("location", "Chennai")

    # ── Step 1: Add transaction to Graph ─────────────────────────────────────
    graph_dict = {
        "transaction_id": tx_id,
        "sender_account_id": sender_id,
        "sender_bank": sender_bank,
        "receiver_account_id": receiver_id,
        "receiver_bank": receiver_bank,
        "amount": amount,
        "transaction_type": tx_type,
        "transaction_timestamp": timestamp_str,
        "device_ip": device_ip,
        "location": location,
        "transaction_status": "PROCESSING",
    }
    try:
        GLOBAL_NETWORK_GRAPH.add_transaction_edge(graph_dict)
    except Exception as e:
        print(f"[ADSL] Graph edge error: {e}")

    # ── Step 2: Request Sender & Receiver Risk from Bank ─────────────────────
    sender_profile = _fetch_account_stored_risk(sender_id, sender_bank)
    receiver_profile = _fetch_account_stored_risk(receiver_id, receiver_bank)

    sender_risk_score = float(sender_profile.get("risk_score", 15.0))
    receiver_risk_score = float(receiver_profile.get("risk_score", 15.0))

    # ── Step 3: XGBoost Transaction Risk Calculation ─────────────────────────
    xgb_assessment = _compute_transaction_xgboost_risk(tx_data, sender_risk_score, receiver_risk_score)
    transaction_risk_score = float(xgb_assessment["score"])
    risk_level = xgb_assessment["level"]
    risk_reasons = xgb_assessment["reasons"]

    # ── Step 4: Tiered Threshold Processing ──────────────────────────────────
    # Tier 1: LOW RISK (0 - 30) -> Action = ALLOW -> Status = COMPLETED
    if transaction_risk_score <= ALLOW_THRESHOLD and sender_risk_score < 70 and receiver_risk_score < 70:
        try:
            GLOBAL_NETWORK_GRAPH.update_transaction_status(tx_id, "COMPLETED")
        except Exception:
            pass

        # Check if sender has an active monitoring case — genuine subsequent activity resolves monitoring case!
        try:
            from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
            GLOBAL_MONITORING_MANAGER.record_subsequent_activity(
                account_id=sender_id,
                new_tx_id=tx_id,
                new_amount=amount,
                is_rapid_forward=False,
                is_suspicious_counterparty=False,
                is_genuine_flow=True,
                new_risk_score=transaction_risk_score,
            )
        except Exception as e:
            print(f"[ADSL] Monitoring follow-up error: {e}")

        # Update bank DB status
        _update_bank_tx_status(sender_bank, tx_id, "COMPLETED", "NONE", "NONE")

        result_low = {
            "transaction_id": tx_id,
            "sender_account_id": sender_id,
            "sender_bank": sender_bank,
            "receiver_account_id": receiver_id,
            "receiver_bank": receiver_bank,
            "amount": amount,
            "transaction_type": tx_type,
            "status": "COMPLETED",
            "decision": "ALLOW",
            "action": "ALLOW",
            "risk_score": transaction_risk_score,
            "risk_level": "LOW",
            "risk_reasons": risk_reasons,
            "combined_risk_score": transaction_risk_score,
            "sender_risk_score": sender_risk_score,
            "receiver_risk_score": receiver_risk_score,
            "deep_analysis_performed": False,
            "graph_updated": True,
            "message": "Low risk (0-30) — transaction allowed immediately as COMPLETED",
            "timestamp": datetime.now().isoformat(),
        }

        with _adsl_tx_lock:
            RECENT_ADSL_TRANSACTIONS.insert(0, result_low)
            if len(RECENT_ADSL_TRANSACTIONS) > 200:
                RECENT_ADSL_TRANSACTIONS.pop()

        return result_low

    # ── Step 5: Suspicious Transaction -> ADSL Deeper Processing ────────────
    # Exceeds ALLOW_THRESHOLD: Trigger Graph Analysis, Provenance, GNN, Mule Grouping
    
    # 5B. Fund Provenance Analysis
    provenance_result = {}
    try:
        provenance_result = trace_fund_provenance(
            account_id=receiver_id,
            max_hops=3,
            graph_instance=GLOBAL_NETWORK_GRAPH,
        )
    except Exception as e:
        print(f"[ADSL] Provenance error: {e}")

    # 5C. GNN Live Inference (Using pre-trained model, zero retraining)
    gnn_result = {}
    gnn_mule_prob = 0.20
    try:
        from gnn_detection.predictor import GLOBAL_GNN_PREDICTOR
        if GLOBAL_GNN_PREDICTOR.is_loaded:
            gnn_result = GLOBAL_GNN_PREDICTOR.predict_network(tx_id, graph_instance=GLOBAL_NETWORK_GRAPH)
            if gnn_result and "node_classifications" in gnn_result:
                s_class = gnn_result["node_classifications"].get(sender_id, {})
                r_class = gnn_result["node_classifications"].get(receiver_id, {})
                gnn_mule_prob = max(
                    s_class.get("mule_probability", 0.0),
                    r_class.get("mule_probability", 0.0),
                )
    except Exception as e:
        print(f"[ADSL] GNN live prediction error: {e}")

    # 5D. Mule Network Dynamic Tracking
    network_info = None
    gnn_tracked_mule = False
    if gnn_result and "node_classifications" in gnn_result:
        for node_id, cls_info in gnn_result["node_classifications"].items():
            if cls_info.get("is_mule") or cls_info.get("classification") in ("MULE", "SUSPICIOUS") or cls_info.get("mule_probability", 0) >= 0.35:
                gnn_tracked_mule = True
                break

    if gnn_tracked_mule or gnn_mule_prob >= 0.35 or transaction_risk_score > 60.0:
        try:
            network_info = GLOBAL_MULE_NETWORKS.register_or_update_network(
                trigger_tx_id=tx_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                gnn_result=gnn_result,
                pattern_type="GNN_DETECTED_MULE" if gnn_tracked_mule else "MULE_SUSPICIOUS_FLOW",
                risk_score=max(transaction_risk_score, round(gnn_mule_prob * 100, 1)),
            )
        except Exception as e:
            print(f"[ADSL] Mule grouping error: {e}")

    # 5E. Final Decision & Status Assignment (Sections 13, 14, 15, 16)
    # LOW: <= 30.0 -> ALLOW -> COMPLETED
    # MEDIUM: 30.1 - 60.0 -> MONITOR -> MONITORING
    # HIGH: > 60.0 -> HONEYPOT + LIEN APPLIED -> ADSL Analysis
    lien_receipt = None

    if transaction_risk_score > 60.0 or gnn_tracked_mule or gnn_mule_prob >= 0.40:
        final_status = "HONEYPOT"
        final_decision = "HONEYPOT"
        h_status = "HONEYPOT"
        l_status = "LIEN_APPLIED"

        # Apply protective lien on recipient account
        try:
            lien_receipt = GLOBAL_LIEN_LAYER.place_lien(
                transaction_id=tx_id,
                account_id=receiver_id,
                bank=receiver_bank,
                amount=amount,
                reason=f"ADSL Honeypot + Lien: High risk score ({transaction_risk_score:.1f}) | GNN Mule Prob {gnn_mule_prob:.2f}",
                lien_type="LIEN",
                risk_score=max(transaction_risk_score, round(gnn_mule_prob * 100, 1)),
            )
        except Exception as e:
            print(f"[ADSL] Automated Lien placement error: {e}")

        # If sender was under monitoring, escalate!
        try:
            from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
            GLOBAL_MONITORING_MANAGER.record_subsequent_activity(
                account_id=sender_id,
                new_tx_id=tx_id,
                new_amount=amount,
                is_rapid_forward=True,
                is_suspicious_counterparty=True,
                new_risk_score=transaction_risk_score,
            )
        except Exception:
            pass

    elif transaction_risk_score > ALLOW_THRESHOLD:
        final_status = "MONITORING"
        final_decision = "MONITOR"
        h_status = "NONE"
        l_status = "NONE"

        # Register in Dynamic Monitoring Manager for observation of subsequent behaviour
        try:
            from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
            GLOBAL_MONITORING_MANAGER.register_case(
                transaction_id=tx_id,
                account_id=sender_id,
                counterparty_account_id=receiver_id,
                bank=sender_bank,
                amount=amount,
                risk_score=transaction_risk_score,
                reason="Medium-risk score (31-60) requiring behavioural monitoring",
            )
        except Exception as e:
            print(f"[ADSL] Monitoring registration error: {e}")

    else:
        final_status = "COMPLETED"
        final_decision = "ALLOW"
        h_status = "NONE"
        l_status = "NONE"

    # Update status in bank DB transactions table
    _update_bank_tx_status(sender_bank, tx_id, final_status, h_status, l_status)

    # 5F. RL Investigation Agent (Decides whether to expand graph, analyze neighbours, or escalate)
    rl_decision = None
    if network_info:
        try:
            from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT
            is_genuine_receiver = (float(r_risk.get("risk_score", 0.0) or 0.0) <= 30.0 and float(gnn_mule_prob or 0.0) < 0.35)
            rl_decision = GLOBAL_RL_AGENT.decide_investigation_action(
                network_id=network_info.get("network_id", "MN-DEFAULT"),
                transaction_id=tx_id,
                network_risk_score=float(network_info.get("risk_score", transaction_risk_score)),
                max_mule_probability=float(gnn_mule_prob),
                suspicious_node_count=int(network_info.get("suspicious_accounts", 1)),
                current_hops_analyzed=len(provenance_result.get("upstream_chain", [])) + 1,
                graph_density=0.35,
                recent_suspicious_tx_count=len(network_info.get("edges", [])),
                lien_active=lien_receipt is not None,
                node_count=int(network_info.get("total_accounts", 2)),
                is_genuine_recipient=is_genuine_receiver,
                genuine_account_id=receiver_id if is_genuine_receiver else None,
            )
        except Exception as e:
            print(f"[ADSL] RL investigation decision error: {e}")

    # Update status in live graph
    try:
        GLOBAL_NETWORK_GRAPH.update_transaction_status(tx_id, final_status)
    except Exception as e:
        print(f"[ADSL] Graph status error: {e}")

    res_dict = {
        "transaction_id": tx_id,
        "sender_account_id": sender_id,
        "sender_bank": sender_bank,
        "receiver_account_id": receiver_id,
        "receiver_bank": receiver_bank,
        "amount": amount,
        "transaction_type": tx_type,
        "status": final_status,
        "decision": final_decision,
        "action": final_decision,
        "risk_score": transaction_risk_score,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "combined_risk_score": transaction_risk_score,
        "sender_risk_score": sender_risk_score,
        "receiver_risk_score": receiver_risk_score,
        "gnn_mule_probability": round(gnn_mule_prob, 3),
        "deep_analysis_performed": True,
        "graph_updated": True,
        "mule_network_id": network_info.get("network_id") if network_info else None,
        "mule_networks": [network_info] if network_info else [],
        "lien": lien_receipt,
        "lien_applied": lien_receipt is not None,
        "lien_id": lien_receipt.get("lien_id") if lien_receipt else None,
        "provenance": provenance_result,
        "rl_investigation": rl_decision,
        "rl_decision": rl_decision,
        "timestamp": datetime.now().isoformat(),
    }

    with _adsl_tx_lock:
        RECENT_ADSL_TRANSACTIONS.insert(0, res_dict)
        if len(RECENT_ADSL_TRANSACTIONS) > 200:
            RECENT_ADSL_TRANSACTIONS.pop()

    return res_dict



def execute_adsl_admin_action(
    transaction_id: str,
    action: str,
    investigator_id: str = "COMPLIANCE_OFFICER_01",
    notes: str = "Admin verification completed",
) -> Dict[str, Any]:
    """
    Executes an administrative investigation decision on an Under Review transaction.
    Actions:
    - RELEASE: releases lien -> status RELEASED -> COMPLETED
    - MONITOR: status MONITORING
    - RESTRICT: status RESTRICTED
    - FREEZE: status FROZEN (and freezes customer account in DB)
    """
    act = action.upper()
    status_map = {
        "RELEASE": "RELEASED",
        "MONITOR": "MONITORING",
        "RESTRICT": "RESTRICTED",
        "FREEZE": "FROZEN",
    }

    if act not in status_map:
        return {"success": False, "error": f"Invalid action {action}. Choose from RELEASE, MONITOR, RESTRICT, FREEZE"}

    new_status = status_map[act]

    # 1. Update Lien Layer
    lien = GLOBAL_LIEN_LAYER.update_lien_status(
        identifier=transaction_id,
        new_status=new_status,
        investigator_id=investigator_id,
        reason=notes,
    )

    # 2. Update Graph Status & Mule Networks
    try:
        GLOBAL_NETWORK_GRAPH.update_transaction_status(transaction_id, new_status)
    except Exception:
        pass

    try:
        GLOBAL_MULE_NETWORKS.update_network_for_account_or_tx(transaction_id, new_status)
        if lien and lien.get("account_id"):
            GLOBAL_MULE_NETWORKS.update_network_for_account_or_tx(lien.get("account_id"), new_status)
    except Exception:
        pass

    # 3. If FREEZE: freeze the account in the bank database
    account_frozen = False
    if act == "FREEZE" and lien:
        acc_id = lien.get("account_id")
        bank = lien.get("bank", "SBI")
        if acc_id:
            try:
                from simulator.db_connection import get_bank_connection
                conn = get_bank_connection(bank)
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE accounts SET account_status = 'FROZEN' WHERE account_id = %s",
                        (acc_id,)
                    )
                conn.commit()
                conn.close()
                account_frozen = True
            except Exception as e:
                print(f"[ADSL] Account freeze error: {e}")

    # 4. Update transaction status in transactions table
    try:
        from simulator.db_connection import get_all_bank_connections
        conns = get_all_bank_connections()
        for b, c in conns.items():
            with c.cursor() as cur:
                cur.execute(
                    "UPDATE transactions SET transaction_status = %s WHERE transaction_id = %s",
                    (new_status, transaction_id)
                )
            c.commit()
            c.close()
    except Exception:
        pass

    return {
        "success": True,
        "transaction_id": transaction_id,
        "action": act,
        "new_status": new_status,
        "account_frozen": account_frozen,
        "updated_at": datetime.now().isoformat(),
        "lien": lien,
    }


def execute_adsl_account_action(
    account_id: str,
    action: str,
    bank: str = "SBI",
    investigator_id: str = "COMPLIANCE_OFFICER_01",
    notes: str = "Account action executed from Graph Forensics",
) -> Dict[str, Any]:
    """
    Executes direct administrative enforcement on a specific account (e.g. from the Graph Inspector):
    - FREEZE: Sets account_status = 'FROZEN' in bank DB and places protective lien
    - RESTRICT: Sets account_status = 'RESTRICTED'
    - MONITOR: Flags account for real-time tracking
    - RELEASE: Restores account to 'ACTIVE'
    """
    act = action.upper()
    valid_actions = {"FREEZE", "RESTRICT", "MONITOR", "RELEASE"}
    if act not in valid_actions:
        return {"success": False, "error": f"Invalid action {action}. Choose from FREEZE, RESTRICT, MONITOR, RELEASE"}

    status_target = {
        "FREEZE": "FROZEN",
        "RESTRICT": "RESTRICTED",
        "MONITOR": "ACTIVE",
        "RELEASE": "ACTIVE",
    }[act]

    # Update in bank PostgreSQL database
    db_updated = False
    try:
        from simulator.db_connection import get_bank_connection
        conn = get_bank_connection(bank)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE accounts SET account_status = %s WHERE account_id = %s",
                (status_target, account_id)
            )
        conn.commit()
        conn.close()
        db_updated = True
    except Exception as e:
        print(f"[ADSL] Error updating account {account_id} status: {e}")

    # If action is FREEZE or RESTRICT, place a holding lien
    lien_created = None
    if act in ("FREEZE", "RESTRICT"):
        try:
            lien_created = GLOBAL_LIEN_LAYER.place_lien(
                transaction_id=f"ADM_{account_id}_{int(datetime.now().timestamp())}",
                account_id=account_id,
                bank=bank,
                amount=50000,
                reason=f"Direct Admin Action: {act} - {notes}",
                lien_type="RESTRICTION" if act == "RESTRICT" else "FREEZE",
                risk_score=95.0 if act == "FREEZE" else 80.0,
            )
        except Exception as e:
            print(f"[ADSL] Error applying lien: {e}")

    # Update node attributes in in-memory graph & mule networks
    try:
        with GLOBAL_NETWORK_GRAPH._lock:
            if GLOBAL_NETWORK_GRAPH.graph.has_node(account_id):
                GLOBAL_NETWORK_GRAPH.graph.nodes[account_id]["account_status"] = status_target
                GLOBAL_NETWORK_GRAPH.graph.nodes[account_id]["admin_action"] = act
    except Exception:
        pass

    try:
        GLOBAL_MULE_NETWORKS.update_network_for_account_or_tx(account_id, status_target)
    except Exception:
        pass

    return {
        "success": True,
        "account_id": account_id,
        "bank": bank,
        "action": act,
        "new_status": status_target,
        "db_updated": db_updated,
        "lien": lien_created,
        "timestamp": datetime.now().isoformat(),
    }
