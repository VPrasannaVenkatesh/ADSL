"""
Coordinator Decision Storage.
Independent SQLite database ensuring 100% decoupling from the 3 private bank PostgreSQL databases.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from .models import CoordinatedDecisionResult
from .config import DECISION_THRESHOLDS

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'coordinator.db'))


def get_coordinator_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_coordinator_storage():
    """Initializes the coordinator database schema and indices."""
    conn = get_coordinator_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS coordinator_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coordination_id TEXT UNIQUE NOT NULL,
                transaction_id TEXT NOT NULL,
                participating_banks TEXT NOT NULL,      -- JSON array e.g. ["SBI", "AXIS"]
                
                sender_bank TEXT NOT NULL,
                sender_masked_account TEXT NOT NULL,
                sender_risk_score REAL NOT NULL,
                sender_risk_level TEXT NOT NULL,
                sender_indicators TEXT NOT NULL,        -- JSON array of strings
                
                receiver_bank TEXT NOT NULL,
                receiver_masked_account TEXT NOT NULL,
                receiver_risk_score REAL NOT NULL,
                receiver_risk_level TEXT NOT NULL,
                receiver_indicators TEXT NOT NULL,      -- JSON array of strings
                
                final_risk_score REAL NOT NULL,
                final_risk_level TEXT NOT NULL,
                final_decision TEXT NOT NULL,          -- 'ALLOW', 'MONITOR', 'REVIEW', 'CONTROLLED_ACTION'
                decision_reasons TEXT NOT NULL,        -- JSON array of strings
                
                coordination_timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_tx_id ON coordinator_decisions(transaction_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_decision ON coordinator_decisions(final_decision);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_ts ON coordinator_decisions(coordination_timestamp DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_banks ON coordinator_decisions(sender_bank, receiver_bank);")
        for col_def in [
            "ALTER TABLE coordinator_decisions ADD COLUMN xgboost_risk_score REAL;",
            "ALTER TABLE coordinator_decisions ADD COLUMN combined_risk_score REAL;",
            "ALTER TABLE coordinator_decisions ADD COLUMN flagged INTEGER DEFAULT 0;",
        ]:
            try:
                conn.execute(col_def)
            except Exception:
                pass
    conn.close()


def save_coordinated_decision(decision: CoordinatedDecisionResult) -> str:
    """Inserts a new coordinator decision."""
    conn = get_coordinator_db()
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO coordinator_decisions (
                coordination_id, transaction_id, participating_banks,
                sender_bank, sender_masked_account, sender_risk_score, sender_risk_level, sender_indicators,
                receiver_bank, receiver_masked_account, receiver_risk_score, receiver_risk_level, receiver_indicators,
                final_risk_score, final_risk_level, final_decision, decision_reasons,
                coordination_timestamp, xgboost_risk_score, combined_risk_score, flagged
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.coordination_id,
            decision.transaction_id,
            json.dumps(decision.participating_banks),
            decision.sender_bank,
            decision.sender_masked_account,
            decision.sender_risk_score,
            decision.sender_risk_level,
            json.dumps(decision.sender_indicators),
            decision.receiver_bank,
            decision.receiver_masked_account,
            decision.receiver_risk_score,
            decision.receiver_risk_level,
            json.dumps(decision.receiver_indicators),
            decision.final_risk_score,
            decision.final_risk_level,
            decision.final_decision,
            json.dumps(decision.decision_reasons),
            decision.coordination_timestamp.isoformat() if isinstance(decision.coordination_timestamp, datetime) else str(decision.coordination_timestamp),
            decision.xgboost_risk_score,
            decision.combined_risk_score,
            1 if decision.flagged else 0,
        ))
    conn.close()
    return decision.coordination_id


def query_decisions(
    limit: int = 100,
    offset: int = 0,
    bank: Optional[str] = None,
    decision: Optional[str] = None,
    risk_level: Optional[str] = None,
    transaction_id: Optional[str] = None,
    coordination_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves paginated coordinator decisions with optional filtering."""
    conn = get_coordinator_db()
    conditions = ["1=1"]
    params = []

    if bank and bank.upper() != "ALL":
        b = bank.upper()
        conditions.append("(sender_bank = ? OR receiver_bank = ?)")
        params.extend([b, b])

    if decision:
        conditions.append("final_decision = ?")
        params.append(decision.upper())

    if risk_level:
        conditions.append("final_risk_level = ?")
        params.append(risk_level.upper())

    if transaction_id:
        conditions.append("transaction_id LIKE ?")
        params.append(f"%{transaction_id}%")

    if coordination_id:
        conditions.append("coordination_id LIKE ?")
        params.append(f"%{coordination_id}%")

    where = " AND ".join(conditions)
    sql = f"""
        SELECT * FROM coordinator_decisions
        WHERE {where}
        ORDER BY coordination_timestamp DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for r in rows:
        dec_info = DECISION_THRESHOLDS.get(r["final_decision"], {})
        results.append({
            "coordination_id": r["coordination_id"],
            "transaction_id": r["transaction_id"],
            "participating_banks": json.loads(r["participating_banks"]),
            "sender_bank": r["sender_bank"],
            "sender_masked_account": r["sender_masked_account"],
            "sender_risk_score": r["sender_risk_score"],
            "sender_risk_level": r["sender_risk_level"],
            "sender_indicators": json.loads(r["sender_indicators"]),
            "receiver_bank": r["receiver_bank"],
            "receiver_masked_account": r["receiver_masked_account"],
            "receiver_risk_score": r["receiver_risk_score"],
            "receiver_risk_level": r["receiver_risk_level"],
            "receiver_indicators": json.loads(r["receiver_indicators"]),
            "final_risk_score": r["final_risk_score"],
            "final_risk_level": r["final_risk_level"],
            "final_decision": r["final_decision"],
            "decision_color": dec_info.get("color", "#6B7280"),
            "decision_reasons": json.loads(r["decision_reasons"]),
            "coordination_timestamp": r["coordination_timestamp"],
            "xgboost_risk_score": r["xgboost_risk_score"] if "xgboost_risk_score" in r.keys() else None,
            "combined_risk_score": r["combined_risk_score"] if "combined_risk_score" in r.keys() else None,
            "flagged": bool(r["flagged"]) if "flagged" in r.keys() and r["flagged"] is not None else False,
            "created_at": r["created_at"],
        })
    conn.close()
    return results


def get_decision_detail(coordination_id: str) -> Optional[Dict[str, Any]]:
    """Fetches full coordinator record by coordination_id or transaction_id."""
    conn = get_coordinator_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM coordinator_decisions
        WHERE coordination_id = ? OR transaction_id = ?
        LIMIT 1
    """, (coordination_id, coordination_id))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None

    dec_info = DECISION_THRESHOLDS.get(r["final_decision"], {})
    return {
        "coordination_id": r["coordination_id"],
        "transaction_id": r["transaction_id"],
        "participating_banks": json.loads(r["participating_banks"]),
        "sender_bank": r["sender_bank"],
        "sender_masked_account": r["sender_masked_account"],
        "sender_risk_score": r["sender_risk_score"],
        "sender_risk_level": r["sender_risk_level"],
        "sender_indicators": json.loads(r["sender_indicators"]),
        "receiver_bank": r["receiver_bank"],
        "receiver_masked_account": r["receiver_masked_account"],
        "receiver_risk_score": r["receiver_risk_score"],
        "receiver_risk_level": r["receiver_risk_level"],
        "receiver_indicators": json.loads(r["receiver_indicators"]),
        "final_risk_score": r["final_risk_score"],
        "final_risk_level": r["final_risk_level"],
        "final_decision": r["final_decision"],
        "decision_color": dec_info.get("color", "#6B7280"),
        "decision_reasons": json.loads(r["decision_reasons"]),
        "coordination_timestamp": r["coordination_timestamp"],
        "created_at": r["created_at"],
    }


def get_coordinator_summary(bank: Optional[str] = None) -> Dict[str, Any]:
    """Generates decision breakdown and statistics for the dashboard."""
    conn = get_coordinator_db()
    cur = conn.cursor()

    conditions = ["1=1"]
    params = []
    if bank and bank.upper() != "ALL":
        b = bank.upper()
        conditions.append("(sender_bank = ? OR receiver_bank = ?)")
        params.extend([b, b])

    where = " AND ".join(conditions)
    
    # Counts by decision
    cur.execute(f"""
        SELECT final_decision, COUNT(*), AVG(final_risk_score)
        FROM coordinator_decisions
        WHERE {where}
        GROUP BY final_decision
    """, params)
    
    dec_counts = {"ALLOW": 0, "MONITOR": 0, "REVIEW": 0, "CONTROLLED_ACTION": 0}
    total = 0
    total_score = 0.0

    for row in cur.fetchall():
        d_name, cnt, avg_s = row[0], int(row[1]), float(row[2] or 0)
        dec_counts[d_name] = cnt
        total += cnt
        total_score += (avg_s * cnt)

    avg_overall = round(total_score / total, 1) if total > 0 else 0.0

    # Cross-bank pair breakdown
    cur.execute(f"""
        SELECT sender_bank || ' ➔ ' || receiver_bank as pair, COUNT(*),
               SUM(CASE WHEN final_decision = 'ALLOW' THEN 1 ELSE 0 END),
               SUM(CASE WHEN final_decision = 'MONITOR' THEN 1 ELSE 0 END),
               SUM(CASE WHEN final_decision = 'REVIEW' THEN 1 ELSE 0 END),
               SUM(CASE WHEN final_decision = 'CONTROLLED_ACTION' THEN 1 ELSE 0 END)
        FROM coordinator_decisions
        WHERE {where}
        GROUP BY pair
        ORDER BY COUNT(*) DESC
    """, params)

    pairs = []
    for r in cur.fetchall():
        pairs.append({
            "pair": r[0],
            "total": r[1],
            "allow": r[2],
            "monitor": r[3],
            "review": r[4],
            "controlled_action": r[5],
        })

    conn.close()

    return {
        "summary": dec_counts,
        "total_coordinated": total,
        "average_risk_score": avg_overall,
        "by_pair": pairs,
    }


# Auto-initialize on import
init_coordinator_storage()
