"""
Unified Real-Time Transaction Decision Lifecycle Pipeline.
Coordinates the complete 17-step end-to-end flow:
1. TRANSACTION GENERATED (INITIATED)
2. VALIDATION (Balance, Accounts, Amount, IP, Location)
3. BEHAVIOURAL ANALYSIS (Sender Risk Score & Receiver Risk Score)
4. XGBOOST TRANSACTION RISK (ML Probability 0-1 -> Score 0-100)
5. COMBINED BANK-LEVEL RISK (0.30*Sender + 0.30*Receiver + 0.40*XGBoost)
6. CROSS-BANK ADSL COORDINATION (Privacy-preserving masked signals)
7. INITIAL DECISION (ALLOW / MONITOR / RESTRICT)
8. STATUS LIFECYCLE & PROCESS_TRANSACTION (SUCCESSFUL / MONITORING / RESTRICTED)
9. NETWORK GRAPH ANALYSIS (Multi-hop, Circular, Fan-in/out, Dwell Time)
10. FUND PROVENANCE (Lineage Tracking)
11. RISK PROPAGATION (Contextual Network Risk)
12. GNN/GAT & PPO PREPARATION
14. CONTROLLED FUNDS / LIEN LAYER (Lien hold placement)
15. DATABASE STORAGE (All 18 attributes persisted with direct psycopg2)
"""

from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List
import psycopg2

from .balance_manager import BalanceManager, TransactionRecord
from .behaviour_history_updater import update_daily_account_behaviour
from risk_engine.engine import assess_transaction_risk
from coordinator.coordinator_service import coordinate_transaction_risk
from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
from network_monitoring.pattern_detector import analyze_connected_network_risk
from network_monitoring.fund_provenance import trace_fund_provenance
from network_monitoring.risk_propagation import calculate_network_risk_propagation
from network_monitoring.lien_layer import GLOBAL_LIEN_LAYER
from network_monitoring.ppo_decision_engine import GLOBAL_PPO_ENGINE
from network_monitoring.config import DECISION_TO_STATUS
from xgboost_risk.feature_extractor import extract_features_for_transaction
from xgboost_risk.predictor import GLOBAL_PREDICTOR
from xgboost_risk.combination_engine import combine_risk_assessments
from xgboost_risk.storage import save_transaction_risk_assessment

# ── GNN Module (optional — graceful fallback if not yet trained) ───────────────
try:
    from gnn_detection.predictor import GLOBAL_GNN_PREDICTOR
    from gnn_detection.config import GNN_TRIGGER_SCORE_THRESHOLD
    _GNN_AVAILABLE = True
except Exception as _gnn_import_err:
    _GNN_AVAILABLE = False
    print(f"[Lifecycle] GNN module not available: {_gnn_import_err}")



class TransactionLifecyclePipeline:
    """
    Orchestrates the complete 17-step real-time state machine for every banking transaction.
    """

    def __init__(self, conns: Dict[str, psycopg2.extensions.connection], balance_mgr: BalanceManager):
        self.conns = conns
        self.balance_mgr = balance_mgr

    def validate_transaction(
        self,
        sender_bank: str,
        sender_account_id: str,
        receiver_bank: str,
        receiver_account_id: str,
        amount: int,
        device_ip: str,
        location: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Step 2: Basic transaction validation before behavioural analysis.
        Validates account existence, balance sufficiency, amount bounds, and device/location fields.
        """
        if amount <= 0:
            return False, "Invalid transaction amount: Amount must be greater than zero"
        
        if sender_account_id == receiver_account_id and sender_bank == receiver_bank:
            return False, "Invalid transaction: Sender and receiver accounts cannot be identical"

        if not device_ip or not location:
            return False, "Missing required security metadata: Device or Location missing"

        # Check sender account validity and balance
        try:
            s_conn = self.conns[sender_bank]
            with s_conn.cursor() as cur:
                cur.execute(
                    "SELECT current_balance, account_status FROM accounts WHERE account_id = %s",
                    (sender_account_id,)
                )
                row = cur.fetchone()
                if not row:
                    return False, f"Sender account {sender_account_id} not found in {sender_bank}"
                bal, status = row
                if status != "ACTIVE":
                    return False, f"Sender account is not active (status: {status})"
                if bal < amount:
                    return False, f"Insufficient balance: Available INR {bal:,}, Required INR {amount:,}"
        except Exception as e:
            return False, f"Sender validation error: {str(e)}"

        # Check receiver account validity
        try:
            r_conn = self.conns[receiver_bank]
            with r_conn.cursor() as cur:
                cur.execute(
                    "SELECT account_status FROM accounts WHERE account_id = %s",
                    (receiver_account_id,)
                )
                row = cur.fetchone()
                if not row:
                    return False, f"Receiver account {receiver_account_id} not found in {receiver_bank}"
                if row[0] != "ACTIVE":
                    return False, f"Receiver account is not active (status: {row[0]})"
        except Exception as e:
            return False, f"Receiver validation error: {str(e)}"

        return True, None

    def process_transaction(
        self,
        sender_bank: str,
        sender_account_id: str,
        receiver_bank: str,
        receiver_account_id: str,
        amount: int,
        tx_type: str,
        timestamp: datetime,
        device_ip: str,
        location: str,
        recipient_is_new: bool,
    ) -> Optional[Tuple[TransactionRecord, Dict[str, Any]]]:
        """
        Executes the full automated transaction decision lifecycle:
        1. GENERATION (INITIATED)
        2. VALIDATION
        3. BEHAVIOURAL ANALYSIS (Sender Risk & Receiver Risk)
        4. XGBOOST TRANSACTION RISK
        5. COMBINED BANK-LEVEL RISK
        6. CROSS-BANK ADSL COORDINATION
        7. INITIAL DECISION (ALLOW / MONITOR / RESTRICT)
        8. PROCESS_TRANSACTION (Ledger Balance Update -> COMPLETED / SUCCESSFUL)
        9. NETWORK ANALYSIS (Graph topology)
        10. FUND PROVENANCE & 11. RISK PROPAGATION
        14. LIEN LAYER (On restriction)
        15. DATABASE STORAGE (All 18 attributes)
        """
        # ── Step 1: GENERATION & VALIDATION ──────────────────────────────────
        is_valid, validation_err = self.validate_transaction(
            sender_bank=sender_bank,
            sender_account_id=sender_account_id,
            receiver_bank=receiver_bank,
            receiver_account_id=receiver_account_id,
            amount=amount,
            device_ip=device_ip,
            location=location,
        )
        if not is_valid:
            print(f"[TRANSACTION REJECTED]: {validation_err}")
            return None

        # Execute balance deduction & ledger record (marked INITIATED initially)
        rec = self.balance_mgr.execute_transfer(
            sender_bank=sender_bank,
            sender_account_id=sender_account_id,
            receiver_bank=receiver_bank,
            receiver_account_id=receiver_account_id,
            amount=amount,
            tx_type=tx_type,
            timestamp=timestamp,
            device_ip=device_ip,
            location=location,
            recipient_is_new=recipient_is_new,
        )
        if not rec:
            return None

        # Edge registration in Transaction Graph
        tx_dict = {
            "transaction_id": rec.transaction_id,
            "sender_account_id": sender_account_id,
            "sender_bank": sender_bank,
            "receiver_account_id": receiver_account_id,
            "receiver_bank": receiver_bank,
            "amount": amount,
            "transaction_type": tx_type,
            "transaction_timestamp": timestamp,
            "device_ip": device_ip,
            "location": location,
            "recipient_is_new": recipient_is_new,
            "transaction_status": "INITIATED",
        }
        dwell_sec = GLOBAL_NETWORK_GRAPH.add_transaction_edge(tx_dict)

        # ── Step 3: BEHAVIOURAL ANALYSIS (Sender & Receiver Risk) ────────────
        GLOBAL_NETWORK_GRAPH.update_transaction_status(rec.transaction_id, "ASSESSING")
        txn_date = timestamp.date()
        update_daily_account_behaviour(self.conns[sender_bank], sender_bank, sender_account_id, txn_date)
        update_daily_account_behaviour(self.conns[receiver_bank], receiver_bank, receiver_account_id, txn_date)

        local_risks = assess_transaction_risk(
            conns=self.conns,
            transaction_id=rec.transaction_id,
            sender_bank=sender_bank,
            sender_account_id=sender_account_id,
            receiver_bank=receiver_bank,
            receiver_account_id=receiver_account_id,
            amount=amount,
            tx_type=tx_type,
            timestamp=timestamp,
            device_ip=device_ip,
            location=location,
            recipient_is_new=recipient_is_new,
        )
        s_risk_score = float(local_risks.get("sender_risk_score", 0.0) or 0.0)
        r_risk_score = float(local_risks.get("receiver_risk_score", 0.0) or 0.0)

        # ── Step 4: XGBOOST TRANSACTION RISK ─────────────────────────────────
        GLOBAL_NETWORK_GRAPH.update_transaction_status(rec.transaction_id, "ASSESSING")

        features = extract_features_for_transaction(
            conns=self.conns,
            sender_bank=sender_bank,
            sender_account_id=sender_account_id,
            receiver_bank=receiver_bank,
            receiver_account_id=receiver_account_id,
            amount=amount,
            tx_type=tx_type,
            timestamp=timestamp,
            device_ip=device_ip,
            location=location,
            recipient_is_new=recipient_is_new,
            sender_risk_score=s_risk_score,
            receiver_risk_score=r_risk_score,
            dwell_sec=dwell_sec,
        )

        xgb_pred = GLOBAL_PREDICTOR.predict_transaction_risk(features)

        # ── Step 5: COMBINED BANK-LEVEL RISK ─────────────────────────────────
        # Formula: 0.30 * Sender + 0.30 * Receiver + 0.40 * XGBoost
        combined_result = combine_risk_assessments(
            sender_risk_score=s_risk_score,
            receiver_risk_score=r_risk_score,
            xgboost_prediction=xgb_pred,
        )

        # ── Step 6: CROSS-BANK ADSL COORDINATION ──────────────────────────────
        GLOBAL_NETWORK_GRAPH.update_transaction_status(rec.transaction_id, "COORDINATING")
        coord_decision = coordinate_transaction_risk(
            transaction_id=rec.transaction_id,
            sender_bank=sender_bank,
            receiver_bank=receiver_bank,
        )

        # ── Step 7: INITIAL DECISION ──────────────────────────────────────────
        # Policy resolution between Coordinator and Combined Bank-Level Risk
        policy_decision = combined_result["decision_status"]
        if coord_decision and coord_decision.final_decision in ("CONTROLLED_ACTION", "FREEZE"):
            policy_decision = coord_decision.final_decision
        elif policy_decision not in ("CONTROLLED_ACTION", "FREEZE") and coord_decision:
            policy_decision = coord_decision.final_decision

        initial_status = DECISION_TO_STATUS.get(policy_decision, "COMPLETED")
        if combined_result["flagged"] and initial_status == "COMPLETED":
            initial_status = "UNDER_REVIEW"

        # ── Step 9: MONITORING & TRANSACTION NETWORK ANALYSIS ─────────────────
        network_analysis = {
            "network_risk_score": 0.0,
            "should_escalate": False,
            "detected_patterns": [],
            "reasons": [],
        }

        comb_score = combined_result["combined_risk_score"]

        # Only run deep network analysis if elevated/suspicious (> 30) per Section 13
        if comb_score >= 30.0 or initial_status != "COMPLETED":
            sender_net = analyze_connected_network_risk(sender_account_id, current_tx_dwell_sec=dwell_sec)
            receiver_net = analyze_connected_network_risk(receiver_account_id, current_tx_dwell_sec=dwell_sec)

            max_net_score = max(sender_net["network_risk_score"], receiver_net["network_risk_score"])
            should_escalate = (sender_net["should_escalate"] or receiver_net["should_escalate"])

            network_analysis = {
                "network_risk_score": max_net_score,
                "should_escalate": should_escalate,
                "detected_patterns": list(set(sender_net["detected_patterns"] + receiver_net["detected_patterns"])),
                "reasons": sender_net["reasons"] + receiver_net["reasons"],
            }

            # Canonical threshold resolution (Section 13 & 14)
            # 0 - 30   -> COMPLETED (ALLOW)
            # 31 - 60  -> MONITORING (MONITOR)
            # 61 - 100 -> HONEYPOT (HONEYPOT + LIEN APPLIED)
            effective_score = max(comb_score, max_net_score if should_escalate else 0.0)

            if effective_score > 60.0 or policy_decision in ("HONEYPOT", "CONTROLLED_ACTION", "FREEZE") or combined_result["flagged"]:
                final_status = "HONEYPOT"
            elif effective_score > 30.0 or policy_decision == "MONITOR":
                final_status = "MONITORING"
            else:
                final_status = "COMPLETED"
        else:
            final_status = "COMPLETED"

        # ── Step 10 & 11: FUND PROVENANCE & RISK PROPAGATION ──────────────────
        provenance = trace_fund_provenance(receiver_account_id, max_hops=3)
        propagation = calculate_network_risk_propagation(
            account_id=receiver_account_id,
            direct_tx_risk=combined_result["xgboost_risk_score"],
            account_behav_risk=r_risk_score,
        )

        # ── Step 13: PPO ADAPTIVE DECISION EVALUATION ─────────────────────────
        ppo_eval = GLOBAL_PPO_ENGINE.evaluate_decision(
            combined_risk_score=combined_result["combined_risk_score"],
            sender_risk_score=s_risk_score,
            receiver_risk_score=r_risk_score,
            network_risk_score=network_analysis["network_risk_score"],
            is_cross_bank=(sender_bank != receiver_bank),
            dwell_time_sec=dwell_sec,
            is_flagged=combined_result["flagged"],
        )

        # ── Step 14: CONTROLLED FUNDS / LIEN LAYER ───────────────────────────
        lien_receipt = None
        if final_status in ("HONEYPOT", "UNDER_REVIEW", "RESTRICTED", "FROZEN"):
            lien_type = "LIEN"
            lien_reason = (
                f"[{final_status}] Transaction Risk {comb_score:.1f}/100. "
                f"Mule/Risk Patterns: {network_analysis['detected_patterns'] or 'Suspicious High Risk'}. "
                f"Suspicious funds placed under Lien protection."
            )
            lien_receipt = GLOBAL_LIEN_LAYER.place_lien(
                transaction_id=rec.transaction_id,
                account_id=receiver_account_id,
                bank=receiver_bank,
                amount=amount,
                reason=lien_reason,
                lien_type=lien_type,
                risk_score=comb_score,
            )

        # ── Step 14B: DYNAMIC BEHAVIOURAL MONITORING REGISTRATION ────────────
        if final_status == "MONITORING":
            try:
                from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
                GLOBAL_MONITORING_MANAGER.register_case(
                    transaction_id=rec.transaction_id,
                    account_id=sender_account_id,
                    counterparty_account_id=receiver_account_id,
                    bank=sender_bank,
                    amount=float(amount),
                    risk_score=float(comb_score),
                    reason=f"Medium-risk score ({comb_score:.1f}) requiring behavioural monitoring",
                )
            except Exception as _mon_err:
                print(f"[Lifecycle Monitoring] Error registering case: {_mon_err}")

        # ── Step 14C: RL INVESTIGATION AGENT DECISION ─────────────────────────
        rl_decision = None
        if final_status in ("HONEYPOT", "UNDER_REVIEW", "RESTRICTED", "FROZEN", "MONITORING"):
            try:
                from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT
                is_genuine_receiver = (r_risk_score <= 30.0 and (not combined_result.get("flagged", False)))
                rl_decision = GLOBAL_RL_AGENT.decide_investigation_action(
                    network_id=f"NET-SIM-{rec.transaction_id[:8]}",
                    transaction_id=rec.transaction_id,
                    network_risk_score=float(comb_score),
                    max_mule_probability=float(combined_result.get("prediction_probability", 0.5)),
                    suspicious_node_count=1 if final_status == "MONITORING" else 2,
                    current_hops_analyzed=min(4, max(1, len(network_analysis.get("detected_patterns", [])) + 1)),
                    graph_density=0.35,
                    recent_suspicious_tx_count=1,
                    lien_active=(lien_receipt is not None),
                    node_count=2,
                    is_genuine_recipient=is_genuine_receiver,
                    genuine_account_id=receiver_account_id if is_genuine_receiver else None,
                )
            except Exception as _rl_err:
                print(f"[Lifecycle RL Agent] Error evaluating action: {_rl_err}")

        # ── Step 8: FINALIZE STATUS & HALT FLOW IF STOPPED ───────────────────
        rec.status = final_status
        rec.flow_stopped = final_status in ("HONEYPOT", "UNDER_REVIEW", "RESTRICTED", "FROZEN")
        GLOBAL_NETWORK_GRAPH.update_transaction_status(rec.transaction_id, final_status)
        h_stat = "HONEYPOT" if final_status == "HONEYPOT" else "NONE"
        l_stat = "LIEN_APPLIED" if lien_receipt else "NONE"
        self._update_db_transaction_status(rec.transaction_id, sender_bank, receiver_bank, final_status, h_stat, l_stat)

        # ── Step 12: GNN NETWORK RISK (Async — only for MEDIUM/HIGH/CRITICAL) ─
        gnn_analysis = {
            "triggered":              False,
            "gnn_risk_score":         0.0,
            "sender_classification":  "UNKNOWN",
            "receiver_classification": "UNKNOWN",
            "network_pattern":        "UNKNOWN",
        }

        risk_lev = combined_result.get("risk_level", "LOW")
        trigger_gnn = (
            _GNN_AVAILABLE and
            risk_lev in ("MEDIUM", "HIGH", "CRITICAL") and
            combined_result["combined_risk_score"] >= GNN_TRIGGER_SCORE_THRESHOLD
        )

        if trigger_gnn:
            def _run_gnn_async():
                try:
                    net_result = GLOBAL_GNN_PREDICTOR.predict_network(
                        transaction_id=rec.transaction_id
                    )
                    # Persist flagged accounts
                    from gnn_detection.api import _save_account_async, _save_network_async
                    for acc_id, cls_data in net_result.get("node_classifications", {}).items():
                        if cls_data.get("classification") in ("SUSPICIOUS", "MULE"):
                            _save_account_async(
                                {
                                    "account_id":              acc_id,
                                    "classification":          cls_data["classification"],
                                    "mule_probability":        cls_data.get("mule_probability", 0.0),
                                    "suspicious_probability":  0.0,
                                    "normal_probability":      0.0,
                                    "gnn_risk_score":          cls_data.get("gnn_risk_score", 0.0),
                                    "risk_level":              cls_data.get("risk_level", "LOW"),
                                    "network_pattern":         net_result.get("network_pattern", "UNKNOWN"),
                                    "connected_account_count": 0,
                                    "confidence":              cls_data.get("confidence", 0.0),
                                    "explanation":             [],
                                    "model_loaded":            True,
                                    "model_version":           "v1.0.0-gatv2",
                                },
                                trigger_tx_id=rec.transaction_id,
                            )
                    if net_result.get("node_count", 0) > 0:
                        _save_network_async(net_result)
                except Exception as _gnn_err:
                    print(f"[GNN Async] Error: {_gnn_err}")

            threading.Thread(target=_run_gnn_async, daemon=True).start()
            gnn_analysis["triggered"] = True


        # ── Step 15: DATABASE STORAGE (All 18 Attributes Persisted) ───────────
        coord_summary_dict = {
            "coordination_id": coord_decision.coordination_id if coord_decision else None,
            "final_decision": coord_decision.final_decision if coord_decision else policy_decision,
            "final_risk_score": coord_decision.final_risk_score if coord_decision else 0.0,
            "final_risk_level": coord_decision.final_risk_level if coord_decision else "LOW",
            "decision_reasons": coord_decision.decision_reasons if coord_decision else [],
        }

        try:
            # Store in sender bank DB
            save_transaction_risk_assessment(
                conn=self.conns[sender_bank],
                bank=sender_bank,
                transaction_id=rec.transaction_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_account_id,
                sender_risk_score=s_risk_score,
                receiver_risk_score=r_risk_score,
                xgboost_risk_score=combined_result["xgboost_risk_score"],
                combined_risk_score=combined_result["combined_risk_score"],
                risk_level=combined_result["risk_level"],
                prediction_probability=combined_result["prediction_probability"],
                top_risk_factors=combined_result["top_risk_factors"],
                model_version=combined_result["model_version"],
                decision_status=combined_result["decision_status"],
                flagged=combined_result["flagged"],
                sender_bank=sender_bank,
                receiver_bank=receiver_bank,
                amount=amount,
                risk_reasons=combined_result["top_risk_factors"] + network_analysis["reasons"],
                coordinator_result=coord_summary_dict,
                network_risk=network_analysis["network_risk_score"],
                final_decision=policy_decision,
                transaction_status=final_status,
                transaction_type=tx_type,
                device_ip=device_ip,
                location=location,
                account_type="BUSINESS" if features.get("is_business") == 1.0 else "PERSONAL",
                honeypot_status=h_stat,
                lien_status=l_stat,
            )

            # If cross-bank, also store in receiver bank DB
            if sender_bank != receiver_bank:
                save_transaction_risk_assessment(
                    conn=self.conns[receiver_bank],
                    bank=receiver_bank,
                    transaction_id=rec.transaction_id,
                    sender_account_id=sender_account_id,
                    receiver_account_id=receiver_account_id,
                    sender_risk_score=s_risk_score,
                    receiver_risk_score=r_risk_score,
                    xgboost_risk_score=combined_result["xgboost_risk_score"],
                    combined_risk_score=combined_result["combined_risk_score"],
                    risk_level=combined_result["risk_level"],
                    prediction_probability=combined_result["prediction_probability"],
                    top_risk_factors=combined_result["top_risk_factors"],
                    model_version=combined_result["model_version"],
                    decision_status=combined_result["decision_status"],
                    flagged=combined_result["flagged"],
                    sender_bank=sender_bank,
                    receiver_bank=receiver_bank,
                    amount=amount,
                    risk_reasons=combined_result["top_risk_factors"] + network_analysis["reasons"],
                    coordinator_result=coord_summary_dict,
                    network_risk=network_analysis["network_risk_score"],
                    final_decision=policy_decision,
                    transaction_status=final_status,
                    transaction_type=tx_type,
                    device_ip=device_ip,
                    location=location,
                    account_type="BUSINESS" if features.get("is_business") == 1.0 else "PERSONAL",
                    honeypot_status=h_stat,
                    lien_status=l_stat,
                )
        except Exception as _st_err:
            print(f"[Unified Storage Error]: {_st_err}")

        # Merged lifecycle response metadata
        lifecycle_metadata = {
            "transaction_id": rec.transaction_id,
            "lifecycle_status": final_status,
            "initial_decision": policy_decision,
            "sender_risk_score": s_risk_score,
            "receiver_risk_score": r_risk_score,
            "xgboost_risk_score": combined_result["xgboost_risk_score"],
            "combined_risk_score": combined_result["combined_risk_score"],
            "risk_level": combined_result["risk_level"],
            "prediction_probability": combined_result["prediction_probability"],
            "top_risk_factors": combined_result["top_risk_factors"],
            "model_version": combined_result["model_version"],
            "network_risk_score": network_analysis["network_risk_score"],
            "detected_patterns": network_analysis["detected_patterns"],
            "provenance_chain": provenance.get("trace_chain", []),
            "risk_propagation": propagation,
            "ppo_action": ppo_eval.get("recommended_action"),
            "lien_receipt": lien_receipt,
            "gnn_analysis": gnn_analysis,
        }

        return rec, lifecycle_metadata

    def _update_db_transaction_status(
        self,
        tx_id: str,
        sender_bank: str,
        receiver_bank: str,
        status: str,
        honeypot_status: str = "NONE",
        lien_status: str = "NONE",
    ):
        """Updates transaction_status, honeypot_status, lien_status columns in PostgreSQL databases."""
        try:
            s_conn = self.conns[sender_bank]
            with s_conn.cursor() as cur:
                cur.execute("""
                    UPDATE transactions
                    SET transaction_status = %s,
                        honeypot_status = %s,
                        lien_status = %s
                    WHERE transaction_id = %s
                """, (status, honeypot_status, lien_status, tx_id))
            s_conn.commit()
        except Exception:
            pass

        if sender_bank != receiver_bank:
            try:
                r_conn = self.conns[receiver_bank]
                with r_conn.cursor() as cur:
                    cur.execute("""
                        UPDATE transactions
                        SET transaction_status = %s,
                            honeypot_status = %s,
                            lien_status = %s
                        WHERE transaction_id = %s
                    """, (status, honeypot_status, lien_status, tx_id))
                r_conn.commit()
            except Exception:
                pass
