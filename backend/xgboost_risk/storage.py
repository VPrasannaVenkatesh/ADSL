"""
Storage module for XGBoost & Unified Transaction Risk Assessments.
Uses direct psycopg2 queries to store and fetch records from
transaction_risk_assessments in sbi_db, axis_db, and iob_db.
Stores all Section 17 audit attributes including:
- transaction_id, sender, receiver, banks, amount, timestamp,
- transaction_type, device, location, account_type,
- numerical xgboost_risk_score, risk_level, current_status,
- honeypot_status, lien_status, risk_factors.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import psycopg2


def save_transaction_risk_assessment(
    conn: psycopg2.extensions.connection,
    bank: str,
    transaction_id: str,
    sender_account_id: str,
    receiver_account_id: str,
    sender_risk_score: float,
    receiver_risk_score: float,
    xgboost_risk_score: float,
    combined_risk_score: float,
    risk_level: str,
    prediction_probability: float,
    top_risk_factors: List[str],
    model_version: str,
    decision_status: str,
    flagged: bool,
    sender_bank: Optional[str] = None,
    receiver_bank: Optional[str] = None,
    amount: int = 0,
    risk_reasons: Optional[List[str]] = None,
    coordinator_result: Optional[Dict[str, Any]] = None,
    network_risk: float = 0.0,
    final_decision: Optional[str] = None,
    transaction_status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    device_ip: Optional[str] = None,
    location: Optional[str] = None,
    account_type: Optional[str] = None,
    honeypot_status: Optional[str] = None,
    lien_status: Optional[str] = None,
) -> str:
    """
    Inserts or updates a comprehensive transaction_risk_assessments record into the bank's PostgreSQL database.
    Stores all numerical scores and Section 17 required attributes.
    Returns the assessment_id.
    """
    assessment_id = f"XGB_{uuid.uuid4().hex[:12].upper()}"
    factors_json = json.dumps(top_risk_factors or [])
    reasons_json = json.dumps(risk_reasons or top_risk_factors or [])
    coord_json = json.dumps(coordinator_result or {})
    
    s_bank = sender_bank or bank
    r_bank = receiver_bank or bank
    f_decision = final_decision or decision_status
    
    # Map default status based on risk level
    if transaction_status:
        t_status = transaction_status
    elif risk_level == "HIGH" or flagged:
        t_status = "HONEYPOT"
    elif risk_level == "MEDIUM":
        t_status = "MONITORING"
    else:
        t_status = "COMPLETED"

    h_status = honeypot_status or ("HONEYPOT" if (risk_level == "HIGH" or flagged) else "NONE")
    l_status = lien_status or ("LIEN_APPLIED" if (risk_level == "HIGH" or flagged) else "NONE")
    t_type = transaction_type or "UPI"
    dev = device_ip or "Mobile:192.168.1.1"
    loc = location or "Chennai"
    acc_t = account_type or "PERSONAL"

    with conn.cursor() as cur:
        # Idempotency Protection: Check if this transaction has already been assessed
        cur.execute("""
            SELECT assessment_id FROM transaction_risk_assessments 
            WHERE transaction_id = %s LIMIT 1
        """, (transaction_id,))
        existing_row = cur.fetchone()
        if existing_row:
            existing_id = existing_row[0]
            cur.execute("""
                UPDATE transaction_risk_assessments SET
                    final_decision = COALESCE(%s, final_decision),
                    transaction_status = COALESCE(%s, transaction_status),
                    honeypot_status = COALESCE(%s, honeypot_status),
                    lien_status = COALESCE(%s, lien_status),
                    network_risk = GREATEST(network_risk, %s),
                    updated_at = NOW()
                WHERE assessment_id = %s
            """, (f_decision, t_status, h_status, l_status, float(network_risk), existing_id))
            conn.commit()
            return existing_id

        cur.execute("""
            INSERT INTO transaction_risk_assessments (
                assessment_id, transaction_id, bank,
                sender_account_id, receiver_account_id,
                sender_bank, receiver_bank, amount,
                sender_risk_score, receiver_risk_score,
                xgboost_risk_score, combined_risk_score, network_risk,
                risk_level, prediction_probability,
                top_risk_factors, risk_reasons, coordinator_result,
                model_version, decision_status, final_decision,
                transaction_status, flagged,
                transaction_type, device_ip, location, account_type,
                honeypot_status, lien_status,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                NOW(), NOW()
            )
            ON CONFLICT (assessment_id) DO UPDATE SET
                final_decision = EXCLUDED.final_decision,
                transaction_status = EXCLUDED.transaction_status,
                honeypot_status = EXCLUDED.honeypot_status,
                lien_status = EXCLUDED.lien_status,
                network_risk = EXCLUDED.network_risk,
                updated_at = NOW()
        """, (
            assessment_id, transaction_id, bank,
            sender_account_id, receiver_account_id,
            s_bank, r_bank, amount,
            float(sender_risk_score), float(receiver_risk_score),
            float(xgboost_risk_score), float(combined_risk_score), float(network_risk),
            risk_level, float(prediction_probability),
            factors_json, reasons_json, coord_json,
            model_version, decision_status, f_decision,
            t_status, flagged,
            t_type, dev, loc, acc_t,
            h_status, l_status,
        ))
    conn.commit()
    return assessment_id


def get_recent_transaction_risk_assessments(
    conns: Dict[str, psycopg2.extensions.connection],
    bank: str = "ALL",
    limit: int = 60,
    offset: int = 0,
    flagged_only: bool = False,
    risk_level: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches recent transaction_risk_assessments across one or all bank databases.
    Supports filtering by risk_level ('LOW', 'MEDIUM', 'HIGH') and status ('COMPLETED', 'MONITORING', 'HONEYPOT').
    """
    banks_to_query = [bank.upper()] if bank.upper() in conns else ["SBI", "AXIS", "IOB"]
    all_rows = []

    for b in banks_to_query:
        conn = conns.get(b)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                where_clauses = []
                params = []

                if flagged_only:
                    where_clauses.append("(flagged = TRUE OR risk_level = 'HIGH' OR transaction_status = 'HONEYPOT')")
                if risk_level and risk_level.upper() != "ALL":
                    where_clauses.append("UPPER(risk_level) = %s")
                    params.append(risk_level.upper())
                if status_filter and status_filter.upper() != "ALL":
                    where_clauses.append("UPPER(transaction_status) = %s")
                    params.append(status_filter.upper())

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cur.execute(f"""
                    SELECT 
                        assessment_id, transaction_id, bank,
                        sender_account_id, receiver_account_id,
                        sender_bank, receiver_bank, amount,
                        sender_risk_score, receiver_risk_score,
                        xgboost_risk_score, combined_risk_score, network_risk,
                        risk_level, prediction_probability,
                        top_risk_factors, risk_reasons, coordinator_result,
                        model_version, decision_status, final_decision,
                        transaction_status, flagged,
                        COALESCE(transaction_type, 'UPI') as transaction_type,
                        COALESCE(device_ip, 'Mobile:192.168.1.1') as device_ip,
                        COALESCE(location, 'Chennai') as location,
                        COALESCE(account_type, 'PERSONAL') as account_type,
                        COALESCE(honeypot_status, 'NONE') as honeypot_status,
                        COALESCE(lien_status, 'NONE') as lien_status,
                        created_at, updated_at
                    FROM transaction_risk_assessments
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])

                cols = [desc[0] for desc in cur.description]
                for r in cur.fetchall():
                    row_dict = dict(zip(cols, r))
                    if isinstance(row_dict.get("top_risk_factors"), str):
                        try:
                            row_dict["top_risk_factors"] = json.loads(row_dict["top_risk_factors"])
                        except Exception:
                            row_dict["top_risk_factors"] = []
                    if isinstance(row_dict.get("risk_reasons"), str):
                        try:
                            row_dict["risk_reasons"] = json.loads(row_dict["risk_reasons"])
                        except Exception:
                            row_dict["risk_reasons"] = []
                    if isinstance(row_dict.get("coordinator_result"), str):
                        try:
                            row_dict["coordinator_result"] = json.loads(row_dict["coordinator_result"])
                        except Exception:
                            row_dict["coordinator_result"] = {}
                    if isinstance(row_dict.get("created_at"), datetime):
                        row_dict["created_at"] = row_dict["created_at"].isoformat()
                    if isinstance(row_dict.get("updated_at"), datetime):
                        row_dict["updated_at"] = row_dict["updated_at"].isoformat()

                    # Guarantee 3-tier risk level (no CRITICAL)
                    lvl = str(row_dict.get("risk_level", "LOW")).upper()
                    if lvl == "CRITICAL":
                        row_dict["risk_level"] = "HIGH"
                    elif lvl not in ("LOW", "MEDIUM", "HIGH"):
                        s = float(row_dict.get("xgboost_risk_score", 0.0))
                        row_dict["risk_level"] = "HIGH" if s > 60.0 else ("MEDIUM" if s > 30.0 else "LOW")

                    all_rows.append(row_dict)
        except Exception as e:
            print(f"[Error querying assessments for {b}]: {e}")

    all_rows.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return all_rows[:limit]


def get_xgboost_summary_stats(conns: Dict[str, psycopg2.extensions.connection], bank: str = "ALL") -> Dict[str, Any]:
    """
    Returns aggregate KPIs: total predictions, flagged count, 3-tier level counts, avg scores.
    """
    banks_to_query = [bank.upper()] if bank.upper() in conns else ["SBI", "AXIS", "IOB"]
    total_assessed = 0
    total_flagged = 0
    total_monitoring = 0
    total_honeypot = 0
    sum_score = 0.0
    level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for b in banks_to_query:
        conn = conns.get(b)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*),
                        COUNT(*) FILTER (WHERE flagged = TRUE OR risk_level IN ('HIGH', 'CRITICAL')),
                        COUNT(*) FILTER (WHERE transaction_status = 'MONITORING'),
                        COUNT(*) FILTER (WHERE transaction_status IN ('HONEYPOT', 'RESTRICTED')),
                        COALESCE(AVG(xgboost_risk_score), 0.0)
                    FROM transaction_risk_assessments
                """)
                row = cur.fetchone()
                if row:
                    cnt, flg, mon, hny, avg_s = row
                    total_assessed += cnt
                    total_flagged += flg
                    total_monitoring += mon
                    total_honeypot += hny
                    sum_score += avg_s * cnt

                cur.execute("""
                    SELECT risk_level, COUNT(*)
                    FROM transaction_risk_assessments
                    GROUP BY risk_level
                """)
                for lvl, l_cnt in cur.fetchall():
                    u_lvl = str(lvl).upper()
                    if u_lvl == "CRITICAL":
                        level_counts["HIGH"] += l_cnt
                    elif u_lvl in level_counts:
                        level_counts[u_lvl] += l_cnt
                    else:
                        level_counts["LOW"] += l_cnt
        except Exception:
            pass

    avg_score = round(sum_score / total_assessed, 1) if total_assessed > 0 else 0.0
    flag_rate = round((total_flagged / total_assessed) * 100, 1) if total_assessed > 0 else 0.0

    return {
        "bank": bank,
        "total_assessed": total_assessed,
        "total_flagged": total_flagged,
        "total_monitoring": total_monitoring,
        "total_honeypot": total_honeypot,
        "flagged_percentage": flag_rate,
        "average_xgboost_score": avg_score,
        "level_counts": level_counts,
    }
