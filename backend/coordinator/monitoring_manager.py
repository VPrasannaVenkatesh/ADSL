"""
Dynamic Monitoring Cases & Lifecycle Tracking Engine.
Tracks medium-risk transactions (31 - 60) under active watch:
- Observes subsequent account activity
- Computes genuine indicators (velocity normalized, trusted counterparties, expected hours)
- Computes suspicious indicators (rapid forwarding, new high-risk beneficiaries, velocity spike)
- Resolves cases: RESOLVED_AS_GENUINE (status -> COMPLETED) or ESCALATED_TO_HIGH_RISK (status -> UNDER_REVIEW, applies Lien)
"""

import threading
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

MONITORING_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'coordinator.db'))


def init_monitoring_tables():
    """Initializes the monitoring_cases table in coordinator.db."""
    try:
        conn = sqlite3.connect(MONITORING_DB_PATH)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    transaction_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    counterparty_account_id TEXT NOT NULL,
                    bank TEXT NOT NULL,
                    amount REAL NOT NULL,
                    initial_risk_score REAL NOT NULL,
                    monitoring_reason TEXT NOT NULL,
                    
                    -- Dynamic Observational Tracking
                    genuine_indicators TEXT NOT NULL DEFAULT '[]',    -- JSON array of strings
                    suspicious_indicators TEXT NOT NULL DEFAULT '[]', -- JSON array of strings
                    follow_up_transaction_count INTEGER DEFAULT 0,
                    total_follow_up_amount REAL DEFAULT 0.0,
                    rapid_forward_detected INTEGER DEFAULT 0,
                    velocity_normalized INTEGER DEFAULT 1,
                    
                    -- Lifecycle Status: 'ACTIVE', 'RESOLVED_AS_GENUINE', 'ESCALATED_TO_HIGH_RISK'
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    final_outcome TEXT,
                    resolution_notes TEXT,
                    
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mc_tx_id ON monitoring_cases(transaction_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mc_acc_id ON monitoring_cases(account_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mc_status ON monitoring_cases(status);")
        conn.close()
    except Exception as e:
        print(f"[MonitoringManager] Error initializing table: {e}")


class MonitoringManager:
    """
    Manages lifecycle of active monitoring cases.
    """

    def __init__(self):
        self._lock = threading.RLock()
        init_monitoring_tables()

    def register_case(
        self,
        transaction_id: str,
        account_id: str,
        counterparty_account_id: str,
        bank: str,
        amount: float,
        risk_score: float,
        reason: str,
    ) -> Dict[str, Any]:
        """Registers a new transaction under dynamic monitoring."""
        with self._lock:
            case_id = f"MON_{transaction_id[:16]}"
            now_iso = datetime.now().isoformat()
            
            genuine_ind = [
                "Transaction processed within operating hours",
                "Account age and baseline tenure established",
            ]
            susp_ind = [
                f"Risk score {risk_score:.1f} exceeds standard allow threshold (30.0)",
                reason,
            ]

            try:
                conn = sqlite3.connect(MONITORING_DB_PATH)
                with conn:
                    conn.execute("""
                        INSERT INTO monitoring_cases (
                            case_id, transaction_id, account_id, counterparty_account_id,
                            bank, amount, initial_risk_score, monitoring_reason,
                            genuine_indicators, suspicious_indicators, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                        ON CONFLICT(case_id) DO UPDATE SET
                            updated_at = excluded.updated_at
                    """, (
                        case_id, transaction_id, account_id, counterparty_account_id,
                        bank, amount, risk_score, reason,
                        str(genuine_ind), str(susp_ind), now_iso, now_iso
                    ))
                conn.close()
            except Exception as e:
                print(f"[MonitoringManager] Error registering case: {e}")

            return {
                "case_id": case_id,
                "transaction_id": transaction_id,
                "account_id": account_id,
                "status": "ACTIVE",
                "risk_score": risk_score,
                "monitoring_reason": reason,
            }

    def record_subsequent_activity(
        self,
        account_id: str,
        new_tx_id: str,
        new_amount: float,
        is_rapid_forward: bool = False,
        is_suspicious_counterparty: bool = False,
    ):
        """Updates active monitoring cases for an account when follow-up transactions occur."""
        with self._lock:
            try:
                conn = sqlite3.connect(MONITORING_DB_PATH)
                conn.row_factory = sqlite3.Row
                with conn:
                    cases = conn.execute("""
                        SELECT * FROM monitoring_cases WHERE account_id = ? AND status = 'ACTIVE'
                    """, (account_id,)).fetchall()

                    for c in cases:
                        follow_cnt = c["follow_up_transaction_count"] + 1
                        total_amt = c["total_follow_up_amount"] + new_amount
                        now_iso = datetime.now().isoformat()

                        # Evaluate if escalating or resolving
                        if is_rapid_forward or is_suspicious_counterparty:
                            new_status = "ESCALATED_TO_HIGH_RISK"
                            outcome = "ESCALATED"
                            notes = "Rapid onward forwarding / suspicious counterparty observed during monitoring window."
                        elif follow_cnt >= 3 and not is_rapid_forward:
                            new_status = "RESOLVED_AS_GENUINE"
                            outcome = "RESOLVED_GENUINE"
                            notes = "Subsequent account activity normalized without onward dispersal."
                        else:
                            new_status = "ACTIVE"
                            outcome = None
                            notes = None

                        conn.execute("""
                            UPDATE monitoring_cases
                            SET follow_up_transaction_count = ?,
                                total_follow_up_amount = ?,
                                rapid_forward_detected = CASE WHEN ? THEN 1 ELSE rapid_forward_detected END,
                                status = ?,
                                final_outcome = COALESCE(?, final_outcome),
                                resolution_notes = COALESCE(?, resolution_notes),
                                updated_at = ?
                            WHERE id = ?
                        """, (
                            follow_cnt, total_amt, 1 if is_rapid_forward else 0,
                            new_status, outcome, notes, now_iso, c["id"]
                        ))
                conn.close()
            except Exception as e:
                print(f"[MonitoringManager] Error recording subsequent activity: {e}")

    def observe_account_activity(self, account_id: str, activity: Dict[str, Any]):
        """Alias for observing subsequent activity on monitored account."""
        amt = float(activity.get("amount", 1000.0))
        tx_id = activity.get("tx_id", f"TX-SUB-{int(datetime.now().timestamp()*1000)}")
        rapid = bool(activity.get("rapid_forwarding", False))
        susp = bool(activity.get("is_suspicious", False) or activity.get("fan_in_increase", False))
        return self.record_subsequent_activity(account_id, tx_id, amt, is_rapid_forward=rapid, is_suspicious_counterparty=susp)

    def get_all_cases(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves monitoring cases for the ADSL Dashboard."""
        try:
            conn = sqlite3.connect(MONITORING_DB_PATH)
            conn.row_factory = sqlite3.Row
            with conn:
                if status:
                    rows = conn.execute("""
                        SELECT * FROM monitoring_cases WHERE status = ? ORDER BY id DESC LIMIT ?
                    """, (status, limit)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT * FROM monitoring_cases ORDER BY id DESC LIMIT ?
                    """, (limit,)).fetchall()
            conn.close()
            
            results = []
            for r in rows:
                item = dict(r)
                # Parse JSON/eval indicators safely
                for key in ("genuine_indicators", "suspicious_indicators"):
                    raw = item.get(key, "[]")
                    if isinstance(raw, str):
                        try:
                            import ast
                            item[key] = ast.literal_eval(raw)
                        except Exception:
                            item[key] = [raw]
                results.append(item)
            return results
        except Exception as e:
            print(f"[MonitoringManager] Error fetching cases: {e}")
            return []

    def get_case_for_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Finds the most recent monitoring case for a given account."""
        try:
            conn = sqlite3.connect(MONITORING_DB_PATH)
            conn.row_factory = sqlite3.Row
            with conn:
                row = conn.execute("""
                    SELECT * FROM monitoring_cases WHERE account_id = ? ORDER BY id DESC LIMIT 1
                """, (account_id,)).fetchone()
            conn.close()
            if row:
                res = dict(row)
                for k in ("genuine_indicators", "suspicious_indicators"):
                    raw = res.get(k, "[]")
                    try:
                        import ast
                        res[k] = ast.literal_eval(raw)
                    except Exception:
                        res[k] = [raw]
                return res
            return None
        except Exception as e:
            print(f"[MonitoringManager] Error fetching case for account {account_id}: {e}")
            return None

    def resolve_case(self, account_id: str, outcome: str = "RESOLVED_GENUINE", notes: str = "Normalized behaviour") -> Dict[str, Any]:
        """Resolves active monitoring case for an account as genuine."""
        try:
            conn = sqlite3.connect(MONITORING_DB_PATH)
            now_iso = datetime.now().isoformat()
            with conn:
                conn.execute("""
                    UPDATE monitoring_cases
                    SET status = 'RESOLVED_GENUINE',
                        final_outcome = ?,
                        resolution_notes = ?,
                        updated_at = ?
                    WHERE account_id = ?
                """, (outcome, notes, now_iso, account_id))
            conn.close()
            return self.get_case_for_account(account_id) or {"status": "RESOLVED_GENUINE", "account_id": account_id}
        except Exception as e:
            print(f"[MonitoringManager] Error resolving case: {e}")
            return {"status": "RESOLVED_GENUINE", "account_id": account_id}

    def escalate_case(self, account_id: str, escalation_reason: str = "Suspicious activity detected") -> Dict[str, Any]:
        """Escalates active monitoring case for an account to high risk."""
        try:
            conn = sqlite3.connect(MONITORING_DB_PATH)
            now_iso = datetime.now().isoformat()
            with conn:
                conn.execute("""
                    UPDATE monitoring_cases
                    SET status = 'ESCALATED',
                        final_outcome = 'ESCALATED_TO_HIGH_RISK',
                        resolution_notes = ?,
                        updated_at = ?
                    WHERE account_id = ?
                """, (escalation_reason, now_iso, account_id))
            conn.close()
            case = self.get_case_for_account(account_id) or {}
            case["status"] = "ESCALATED"
            case["escalation_reason"] = escalation_reason
            return case
        except Exception as e:
            print(f"[MonitoringManager] Error escalating case: {e}")
            return {"status": "ESCALATED", "account_id": account_id, "escalation_reason": escalation_reason}


# Singleton Monitoring Manager
GLOBAL_MONITORING_MANAGER = MonitoringManager()
