"""
Transaction Simulation Orchestrator.
Combines normal transactions and concurrent connected network patterns,
updates PostgreSQL accounts, transactions, and behaviour_history tables.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import psycopg2

from .db_connection import (
    get_all_bank_connections,
    fetch_latest_transaction_timestamp,
    BANK_NAMES,
)
from .balance_manager import BalanceManager, TransactionRecord
from .behaviour_history_updater import update_daily_account_behaviour
from .normal_transaction_generator import NormalTransactionGenerator
from .connected_pattern_generator import ConnectedPatternGenerator

try:
    from risk_engine.engine import assess_transaction_risk
    RISK_ENGINE_ENABLED = True
except ImportError:
    RISK_ENGINE_ENABLED = False

try:
    from coordinator.coordinator_service import coordinate_transaction_risk
    COORDINATOR_ENABLED = True
except ImportError:
    COORDINATOR_ENABLED = False

SPEED_SETTINGS = {
    "slow": {"delay": 2.5, "clock_step_range": (30, 240)},
    "normal": {"delay": 0.8, "clock_step_range": (10, 90)},
    "fast": {"delay": 0.08, "clock_step_range": (2, 30)},
}


class TransactionSimulationEngine:
    def __init__(self, speed: str = "normal"):
        self.speed = speed.lower() if speed.lower() in SPEED_SETTINGS else "normal"
        self.conns = get_all_bank_connections()
        self.accounts_by_bank: Dict[str, List[dict]] = {b: [] for b in BANK_NAMES}
        self.accounts_by_id: Dict[str, dict] = {}

        self._load_accounts()
        self.balance_mgr = BalanceManager(self.conns)
        self.normal_gen = NormalTransactionGenerator(self.accounts_by_bank, self.accounts_by_id)
        self.pattern_gen = ConnectedPatternGenerator(self.accounts_by_bank, self.accounts_by_id)

        # Baseline chronological clock (strictly ahead of latest historical timestamp)
        self.sim_clock = fetch_latest_transaction_timestamp(self.conns) + timedelta(minutes=5)
        self.is_running = False

        self.stats = {
            "total_generated": 0,
            "intra_bank": 0,
            "cross_bank": 0,
            "total_volume": 0,
            "patterns_triggered": 0,
        }

    def _load_accounts(self):
        """Loads all active accounts from SBI, AXIS, and IOB databases."""
        for bank in BANK_NAMES:
            conn = self.conns[bank]
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, account_number, customer_name,
                           account_type, current_balance, home_location,
                           account_created_date
                    FROM accounts
                    WHERE account_status = 'ACTIVE'
                    ORDER BY account_id
                """)
                for r in cur.fetchall():
                    acc = {
                        "account_id": r[0],
                        "account_number": r[1],
                        "customer_name": r[2],
                        "account_type": r[3],
                        "current_balance": int(r[4]),
                        "home_location": r[5] or "Chennai",
                        "account_created_date": r[6],
                        "bank": bank,
                    }
                    self.accounts_by_bank[bank].append(acc)
                    self.accounts_by_id[acc["account_id"]] = acc

    def check_recipient_is_new(self, sender_id: str, receiver_id: str, sender_bank: str) -> bool:
        """Checks if sender has ever transferred to receiver before."""
        conn = self.conns[sender_bank]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM transactions
                WHERE sender_account_id = %s AND receiver_account_id = %s
                LIMIT 1
            """, (sender_id, receiver_id))
            return cur.fetchone() is None

    def advance_clock(self, seconds: Optional[int] = None):
        """Advances logical simulation timestamp."""
        if seconds is None:
            s_min, s_max = SPEED_SETTINGS[self.speed]["clock_step_range"]
            seconds = random.randint(s_min, s_max)
        self.sim_clock += timedelta(seconds=seconds)

    def step(self) -> Optional[TransactionRecord]:
        """
        Executes a single simulation step.
        Checks for ready multi-hop pattern steps first, then proceeds with normal transactions.
        """
        record: Optional[TransactionRecord] = None

        # ── 1. Check for ready step from scheduled pattern queues ─────────────
        ready_step = self.pattern_gen.pop_ready_step(self.sim_clock)
        if ready_step:
            sender = self.accounts_by_id.get(ready_step.sender_account_id)
            receiver = self.accounts_by_id.get(ready_step.receiver_account_id)
            if sender and receiver and sender["current_balance"] >= ready_step.amount:
                is_new = self.check_recipient_is_new(sender["account_id"], receiver["account_id"], sender["bank"])
                record = self.balance_mgr.execute_transfer(
                    sender_bank=sender["bank"],
                    sender_account_id=sender["account_id"],
                    receiver_bank=receiver["bank"],
                    receiver_account_id=receiver["account_id"],
                    amount=ready_step.amount,
                    tx_type=ready_step.tx_type,
                    timestamp=self.sim_clock,
                    device_ip=ready_step.device_ip,
                    location=ready_step.location,
                    recipient_is_new=is_new,
                )

        # ── 2. Randomly trigger a new connected pattern sequence (20% chance) ─
        if not record and random.random() < 0.20:
            self.pattern_gen.trigger_random_pattern(self.sim_clock)
            self.stats["patterns_triggered"] += 1

        # ── 3. Normal Routine Banking Transaction ─────────────────────────────
        if not record:
            selection = self.normal_gen.select_accounts()
            if selection:
                sender, receiver = selection
                self.advance_clock()
                tx_type = random.choices(["UPI", "IMPS", "NEFT", "BANK_TRANSFER"], weights=[0.55, 0.25, 0.12, 0.08], k=1)[0]
                amount = self.normal_gen.generate_amount(tx_type, sender["current_balance"])
                if amount >= 100 and amount <= sender["current_balance"]:
                    dev_ip = self.normal_gen.get_device(sender["account_id"])
                    loc = self.normal_gen.get_location(sender)
                    is_new = self.check_recipient_is_new(sender["account_id"], receiver["account_id"], sender["bank"])

                    record = self.balance_mgr.execute_transfer(
                        sender_bank=sender["bank"],
                        sender_account_id=sender["account_id"],
                        receiver_bank=receiver["bank"],
                        receiver_account_id=receiver["account_id"],
                        amount=amount,
                        tx_type=tx_type,
                        timestamp=self.sim_clock,
                        device_ip=dev_ip,
                        location=loc,
                        recipient_is_new=is_new,
                    )

        if record:
            # Update in-memory account balances
            self.accounts_by_id[record.sender_account_id]["current_balance"] = record.sender_bal_after
            self.accounts_by_id[record.receiver_account_id]["current_balance"] = record.receiver_bal_after

            # Register in Network Graph as INITIATED
            tx_dict = {
                "transaction_id": record.transaction_id,
                "sender_account_id": record.sender_account_id,
                "sender_bank": record.sender_bank,
                "receiver_account_id": record.receiver_account_id,
                "receiver_bank": record.receiver_bank,
                "amount": record.amount,
                "transaction_type": record.transaction_type,
                "transaction_timestamp": record.transaction_timestamp,
                "device_ip": record.device_ip,
                "location": record.location,
                "recipient_is_new": record.recipient_is_new,
                "transaction_status": "INITIATED",
            }
            dwell_sec = -1.0
            try:
                from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
                from network_monitoring.pattern_detector import analyze_connected_network_risk
                from network_monitoring.config import DECISION_TO_STATUS
                dwell_sec = GLOBAL_NETWORK_GRAPH.add_transaction_edge(tx_dict)
                GLOBAL_NETWORK_GRAPH.update_transaction_status(record.transaction_id, "ASSESSING")
            except Exception:
                pass

            # Dynamically recalculate daily behaviour_history for sender & receiver
            txn_date = record.transaction_timestamp.date()
            update_daily_account_behaviour(self.conns[record.sender_bank], record.sender_bank, record.sender_account_id, txn_date)
            update_daily_account_behaviour(self.conns[record.receiver_bank], record.receiver_bank, record.receiver_account_id, txn_date)

            # Trigger bank-level risk assessment independently per bank
            s_risk_score = 0.0
            r_risk_score = 0.0
            if RISK_ENGINE_ENABLED:
                try:
                    local_risks = assess_transaction_risk(
                        conns=self.conns,
                        transaction_id=record.transaction_id,
                        sender_bank=record.sender_bank,
                        sender_account_id=record.sender_account_id,
                        receiver_bank=record.receiver_bank,
                        receiver_account_id=record.receiver_account_id,
                        amount=record.amount,
                        tx_type=record.transaction_type,
                        timestamp=record.transaction_timestamp,
                        device_ip=record.device_ip,
                        location=record.location,
                        recipient_is_new=record.recipient_is_new,
                    )
                    if local_risks:
                        s_risk_score = float(local_risks.get("sender_risk_score", 0.0) or 0.0)
                        r_risk_score = float(local_risks.get("receiver_risk_score", 0.0) or 0.0)
                except Exception:
                    pass

            # XGBoost Transaction Risk Prediction (Module 4)
            is_flagged = False
            comb_score = max(s_risk_score, r_risk_score)
            try:
                from xgboost_risk.feature_extractor import extract_features_for_transaction
                from xgboost_risk.predictor import GLOBAL_PREDICTOR
                from xgboost_risk.combination_engine import combine_risk_assessments
                from xgboost_risk.storage import save_transaction_risk_assessment

                features = extract_features_for_transaction(
                    conns=self.conns,
                    sender_bank=record.sender_bank,
                    sender_account_id=record.sender_account_id,
                    receiver_bank=record.receiver_bank,
                    receiver_account_id=record.receiver_account_id,
                    amount=record.amount,
                    tx_type=record.transaction_type,
                    timestamp=record.transaction_timestamp,
                    device_ip=record.device_ip,
                    location=record.location,
                    recipient_is_new=record.recipient_is_new,
                    sender_risk_score=s_risk_score,
                    receiver_risk_score=r_risk_score,
                    dwell_sec=dwell_sec,
                )
                xgb_pred = GLOBAL_PREDICTOR.predict_transaction_risk(features)
                combined = combine_risk_assessments(
                    sender_risk_score=s_risk_score,
                    receiver_risk_score=r_risk_score,
                    xgboost_prediction=xgb_pred,
                )
                comb_score = combined["combined_risk_score"]
                is_flagged = combined["flagged"]

                save_transaction_risk_assessment(
                    conn=self.conns[record.sender_bank],
                    bank=record.sender_bank,
                    transaction_id=record.transaction_id,
                    sender_account_id=record.sender_account_id,
                    receiver_account_id=record.receiver_account_id,
                    sender_risk_score=s_risk_score,
                    receiver_risk_score=r_risk_score,
                    xgboost_risk_score=combined["xgboost_risk_score"],
                    combined_risk_score=combined["combined_risk_score"],
                    risk_level=combined["risk_level"],
                    prediction_probability=combined["prediction_probability"],
                    top_risk_factors=combined["top_risk_factors"],
                    model_version=combined["model_version"],
                    decision_status=combined["decision_status"],
                    flagged=is_flagged,
                )
                if record.sender_bank != record.receiver_bank:
                    save_transaction_risk_assessment(
                        conn=self.conns[record.receiver_bank],
                        bank=record.receiver_bank,
                        transaction_id=record.transaction_id,
                        sender_account_id=record.sender_account_id,
                        receiver_account_id=record.receiver_account_id,
                        sender_risk_score=s_risk_score,
                        receiver_risk_score=r_risk_score,
                        xgboost_risk_score=combined["xgboost_risk_score"],
                        combined_risk_score=combined["combined_risk_score"],
                        risk_level=combined["risk_level"],
                        prediction_probability=combined["prediction_probability"],
                        top_risk_factors=combined["top_risk_factors"],
                        model_version=combined["model_version"],
                        decision_status=combined["decision_status"],
                        flagged=is_flagged,
                    )
            except Exception as _xgb_err:
                pass

            # Trigger decentralized multi-bank risk coordination
            coord_decision = None
            if COORDINATOR_ENABLED:
                try:
                    coord_decision = coordinate_transaction_risk(
                        transaction_id=record.transaction_id,
                        sender_bank=record.sender_bank,
                        receiver_bank=record.receiver_bank,
                    )
                except Exception:
                    pass

            # Decision Resolution & Network Escalation
            final_decision = coord_decision.final_decision if coord_decision else "ALLOW"
            if is_flagged:
                final_decision = "CONTROLLED_ACTION"
            elif comb_score >= 65.0:
                final_decision = "CONTROLLED_ACTION"
            elif comb_score >= 35.0 and final_decision == "ALLOW":
                final_decision = "MONITOR"

            initial_status = "COMPLETED"
            try:
                initial_status = DECISION_TO_STATUS.get(final_decision, "COMPLETED")
            except Exception:
                pass
            if is_flagged:
                initial_status = "RESTRICTED"
            final_status = initial_status

            if initial_status == "MONITORING":
                try:
                    s_net = analyze_connected_network_risk(record.sender_account_id, current_tx_dwell_sec=dwell_sec)
                    r_net = analyze_connected_network_risk(record.receiver_account_id, current_tx_dwell_sec=dwell_sec)
                    if s_net.get("should_escalate") or r_net.get("should_escalate"):
                        final_status = "RESTRICTED"
                except Exception:
                    pass

            record.status = final_status
            try:
                GLOBAL_NETWORK_GRAPH.update_transaction_status(record.transaction_id, final_status)
            except Exception:
                pass

            # Update in DB
            try:
                s_conn = self.conns[record.sender_bank]
                with s_conn.cursor() as cur:
                    cur.execute("UPDATE transactions SET transaction_status = %s WHERE transaction_id = %s", (final_status, record.transaction_id))
                s_conn.commit()
            except Exception:
                pass

            if record.sender_bank != record.receiver_bank:
                try:
                    r_conn = self.conns[record.receiver_bank]
                    with r_conn.cursor() as cur:
                        cur.execute("UPDATE transactions SET transaction_status = %s WHERE transaction_id = %s", (final_status, record.transaction_id))
                    r_conn.commit()
                except Exception:
                    pass

            # Update stats
            self.stats["total_generated"] += 1
            self.stats["total_volume"] += record.amount
            if record.is_cross_bank:
                self.stats["cross_bank"] += 1
            else:
                self.stats["intra_bank"] += 1

        return record

    def run_loop(self, total_count: int = 0, on_record: Optional[Callable[[TransactionRecord, dict], None]] = None):
        """Runs the simulator continuously or up to total_count."""
        self.is_running = True
        delay = SPEED_SETTINGS[self.speed]["delay"]

        try:
            while self.is_running:
                rec = self.step()
                if rec and on_record:
                    on_record(rec, self.stats)

                if total_count > 0 and self.stats["total_generated"] >= total_count:
                    break

                time.sleep(delay)
        except KeyboardInterrupt:
            self.is_running = False
        finally:
            self.is_running = False

    def close(self):
        """Closes all database connections."""
        for conn in self.conns.values():
            if conn and not conn.closed:
                conn.close()
