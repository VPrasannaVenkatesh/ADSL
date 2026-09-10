"""
Storage module for XGBoost & Unified Transaction Risk Assessments.
Uses direct psycopg2 queries to store and fetch records from
transaction_risk_assessments in sbi_db, axis_db, and iob_db.
Stores all 18 complete audit attributes.
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
) -> str:
    """
    Inserts a comprehensive transaction_risk_assessments record into the bank's PostgreSQL database.
    Stores all 18 required assessment & lifecycle attributes.
    Returns the generated assessment_id.
    """
    assessment_id = f"XGB_{uuid.uuid4().hex[:12].upper()}"
    factors_json = json.dumps(top_risk_factors or [])
    reasons_json = json.dumps(risk_reasons or top_risk_factors or [])
    coord_json = json.dumps(coordinator_result or {})
    
    s_bank = sender_bank or bank
    r_bank = receiver_bank or bank
    f_decision = final_decision or decision_status
    t_status = transaction_status or ("RESTRICTED" if flagged else "COMPLETED")

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
                    network_risk = GREATEST(network_risk, %s),
                    updated_at = NOW()
                WHERE assessment_id = %s
            """, (f_decision, t_status, float(network_risk), existing_id))
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
                transaction_status, flagged, created_at, updated_at
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, NOW(), NOW()
            )
            ON CONFLICT (assessment_id) DO UPDATE SET
                final_decision = EXCLUDED.final_decision,
                transaction_status = EXCLUDED.transaction_status,
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
        ))
    conn.commit()
    return assessment_id


def get_recent_transaction_risk_assessments(
    conns: Dict[str, psycopg2.extensions.connection],
    bank: str = "ALL",
    limit: int = 50,
    offset: int = 0,
    flagged_only: bool = False,
    risk_level: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches recent transaction_risk_assessments across one or all bank databases.
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
                    where_clauses.append("flagged = TRUE")
                if risk_level:
                    where_clauses.append("risk_level = %s")
                    params.append(risk_level.upper())

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
                        transaction_status, flagged, created_at, updated_at
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

                    # Derive or format 4-class multi-category risk classification
                    if not row_dict.get("predicted_class"):
                        r_level = str(row_dict.get("risk_level", "LOW")).upper()
                        if r_level == "CRITICAL":
                            row_dict["predicted_class"] = "CRITICAL_FRAUD"
                        elif r_level == "HIGH":
                            row_dict["predicted_class"] = "MULE_FLOW"
                        elif r_level == "MEDIUM":
                            row_dict["predicted_class"] = "SUSPICIOUS"
                        else:
                            row_dict["predicted_class"] = "NORMAL"

                    all_rows.append(row_dict)
        except Exception as e:
            print(f"[Error querying assessments for {b}]: {e}")

    all_rows.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return all_rows[:limit]


def get_xgboost_summary_stats(conns: Dict[str, psycopg2.extensions.connection], bank: str = "ALL") -> Dict[str, Any]:
    """
    Returns aggregate KPIs: total predictions, flagged count, level counts, avg scores.
    """
    banks_to_query = [bank.upper()] if bank.upper() in conns else ["SBI", "AXIS", "IOB"]
    total_assessed = 0
    total_flagged = 0
    total_restricted = 0
    sum_score = 0.0
    sum_combined = 0.0
    level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for b in banks_to_query:
        conn = conns.get(b)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*),
                        COUNT(*) FILTER (WHERE flagged = TRUE),
                        COUNT(*) FILTER (WHERE transaction_status = 'RESTRICTED'),
                        COALESCE(AVG(xgboost_risk_score), 0.0),
                        COALESCE(AVG(combined_risk_score), 0.0)
                    FROM transaction_risk_assessments
                """)
                row = cur.fetchone()
                if row:
                    cnt, flg, rst, avg_s, avg_c = row
                    total_assessed += cnt
                    total_flagged += flg
                    total_restricted += rst
                    sum_score += avg_s * cnt
                    sum_combined += avg_c * cnt

                cur.execute("""
                    SELECT risk_level, COUNT(*)
                    FROM transaction_risk_assessments
                    GROUP BY risk_level
                """)
                for lvl, l_cnt in cur.fetchall():
                    if lvl in level_counts:
                        level_counts[lvl] += l_cnt
        except Exception:
            pass

    avg_score = round(sum_score / total_assessed, 2) if total_assessed > 0 else 0.0
    avg_combined = round(sum_combined / total_assessed, 2) if total_assessed > 0 else 0.0
    flag_rate = round((total_flagged / total_assessed) * 100, 1) if total_assessed > 0 else 0.0

    return {
        "bank": bank,
        "total_assessed": total_assessed,
        "total_flagged": total_flagged,
        "total_restricted": total_restricted,
        "flagged_percentage": flag_rate,
        "average_xgboost_score": avg_score,
        "average_combined_score": avg_combined,
        "level_counts": level_counts,
    }


def get_assessment_by_transaction_id(
    conns: Dict[str, psycopg2.extensions.connection],
    transaction_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Idempotency lookup: checks across banks for an already computed assessment for transaction_id.
    """
    for bank_name, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        assessment_id, transaction_id, bank,
                        sender_account_id, receiver_account_id,
                        sender_bank, receiver_bank, amount,
                        sender_risk_score, receiver_risk_score,
                        xgboost_risk_score, combined_risk_score, network_risk,
                        risk_level, prediction_probability,
                        top_risk_factors, risk_reasons, coordinator_result,
                        model_version, decision_status, final_decision,
                        transaction_status, flagged, created_at
                    FROM transaction_risk_assessments
                    WHERE transaction_id = %s
                    LIMIT 1
                """, (transaction_id,))
                r = cur.fetchone()
                if r:
                    factors = json.loads(r[15]) if isinstance(r[15], str) else (r[15] or [])
                    reasons = json.loads(r[16]) if isinstance(r[16], str) else (r[16] or [])
                    coord = json.loads(r[17]) if isinstance(r[17], str) else (r[17] or {})
                    return {
                        "assessment_id": r[0],
                        "transaction_id": r[1],
                        "bank": r[2],
                        "sender_account_id": r[3],
                        "receiver_account_id": r[4],
                        "sender_bank": r[5],
                        "receiver_bank": r[6],
                        "amount": int(r[7] or 0),
                        "sender_risk_score": float(r[8] or 0.0),
                        "receiver_risk_score": float(r[9] or 0.0),
                        "xgboost_risk_score": float(r[10] or 0.0),
                        "combined_risk_score": float(r[11] or 0.0),
                        "network_risk": float(r[12] or 0.0),
                        "risk_level": r[13],
                        "prediction_probability": float(r[14] or 0.0),
                        "top_risk_factors": factors,
                        "risk_reasons": reasons,
                        "coordinator_result": coord,
                        "model_version": r[18],
                        "decision_status": r[19],
                        "final_decision": r[20],
                        "transaction_status": r[21],
                        "flagged": bool(r[22]),
                        "created_at": r[23].isoformat() if r[23] else None,
                    }
        except Exception:
            continue
    return None
