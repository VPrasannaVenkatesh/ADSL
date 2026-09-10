"""
FastAPI Router for Bank-Level Behavioural Risk Assessments.
Provides endpoints for live risk monitoring, summaries, filtering, and detail drawers.
"""

import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from simulator.db_connection import get_bank_connection, BANK_NAMES

router = APIRouter(prefix="/api/risk", tags=["Risk Monitoring"])

LEVEL_COLOR = {
    "LOW": "#10B981",
    "MEDIUM": "#F59E0B",
    "HIGH": "#F97316",
    "CRITICAL": "#EF4444",
}


def _query_assessments(
    banks: List[str],
    limit: int = 100,
    offset: int = 0,
    risk_level: Optional[str] = None,
    account_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    min_score: Optional[float] = None,
) -> List[dict]:
    rows = []
    for bank in banks:
        try:
            conn = get_bank_connection(bank)
            conditions = ["1=1"]
            params = []

            if risk_level:
                conditions.append("risk_level = %s")
                params.append(risk_level.upper())
            if account_id:
                conditions.append("account_id ILIKE %s")
                params.append(f"%{account_id}%")
            if transaction_id:
                conditions.append("transaction_id ILIKE %s")
                params.append(f"%{transaction_id}%")
            if min_score is not None:
                conditions.append("final_risk_score >= %s")
                params.append(min_score)

            where = " AND ".join(conditions)

            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT assessment_id, transaction_id, account_id, bank_name, role,
                           amount, transaction_type, assessment_timestamp,
                           amount_risk, velocity_risk, behaviour_deviation_risk,
                           device_risk, location_risk, counterparty_risk,
                           timing_risk, network_pattern_risk,
                           final_risk_score, risk_level, risk_reasons,
                           created_at
                    FROM risk_assessments
                    WHERE {where}
                    ORDER BY assessment_timestamp DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                for r in cur.fetchall():
                    reasons_val = r[18]
                    if isinstance(reasons_val, str):
                        try:
                            reasons_val = json.loads(reasons_val)
                        except Exception:
                            reasons_val = [reasons_val]
                    elif not isinstance(reasons_val, list):
                        reasons_val = []

                    rows.append({
                        "assessment_id": r[0],
                        "transaction_id": r[1],
                        "account_id": r[2],
                        "bank_name": r[3],
                        "role": r[4],
                        "amount": int(r[5]),
                        "transaction_type": r[6],
                        "assessment_timestamp": r[7].isoformat() if r[7] else None,
                        "amount_risk": round(float(r[8]), 2),
                        "velocity_risk": round(float(r[9]), 2),
                        "behaviour_deviation_risk": round(float(r[10]), 2),
                        "device_risk": round(float(r[11]), 2),
                        "location_risk": round(float(r[12]), 2),
                        "counterparty_risk": round(float(r[13]), 2),
                        "timing_risk": round(float(r[14]), 2),
                        "network_pattern_risk": round(float(r[15]), 2),
                        "final_risk_score": round(float(r[16]), 2),
                        "risk_level": r[17],
                        "risk_reasons": reasons_val,
                        "created_at": r[19].isoformat() if r[19] else None,
                        "risk_color": LEVEL_COLOR.get(r[17], "#6B7280"),
                    })
            conn.close()
        except Exception as e:
            print(f"[RISK API] Error querying {bank}: {e}")
    return rows


@router.get("/assessments")
def get_assessments(
    bank: Optional[str] = Query(None, description="SBI, AXIS, IOB, or ALL"),
    risk_level: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    transaction_id: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    """Return paginated risk assessments with optional filters."""
    banks = BANK_NAMES if (not bank or bank.upper() == "ALL") else [bank.upper()]
    data = _query_assessments(banks, limit, offset, risk_level, account_id, transaction_id, min_score)
    data.sort(key=lambda x: x["assessment_timestamp"] or "", reverse=True)
    return {"assessments": data[:limit], "count": len(data)}


@router.get("/assessments/{assessment_id}")
def get_assessment_detail(assessment_id: str):
    """Return full detail for a single assessment by ID."""
    for bank in BANK_NAMES:
        try:
            conn = get_bank_connection(bank)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT assessment_id, transaction_id, account_id, bank_name, role,
                           amount, transaction_type, assessment_timestamp,
                           amount_risk, velocity_risk, behaviour_deviation_risk,
                           device_risk, location_risk, counterparty_risk,
                           timing_risk, network_pattern_risk,
                           final_risk_score, risk_level, risk_reasons, created_at
                    FROM risk_assessments WHERE assessment_id = %s
                """, (assessment_id,))
                r = cur.fetchone()
                if r:
                    conn.close()
                    reasons_val = r[18]
                    if isinstance(reasons_val, str):
                        try:
                            reasons_val = json.loads(reasons_val)
                        except Exception:
                            reasons_val = [reasons_val]
                    elif not isinstance(reasons_val, list):
                        reasons_val = []

                    return {
                        "assessment_id": r[0],
                        "transaction_id": r[1],
                        "account_id": r[2],
                        "bank_name": r[3],
                        "role": r[4],
                        "amount": int(r[5]),
                        "transaction_type": r[6],
                        "assessment_timestamp": r[7].isoformat() if r[7] else None,
                        "components": {
                            "amount_risk": round(float(r[8]), 2),
                            "velocity_risk": round(float(r[9]), 2),
                            "behaviour_deviation_risk": round(float(r[10]), 2),
                            "device_risk": round(float(r[11]), 2),
                            "location_risk": round(float(r[12]), 2),
                            "counterparty_risk": round(float(r[13]), 2),
                            "timing_risk": round(float(r[14]), 2),
                            "network_pattern_risk": round(float(r[15]), 2),
                        },
                        "final_risk_score": round(float(r[16]), 2),
                        "risk_level": r[17],
                        "risk_color": LEVEL_COLOR.get(r[17], "#6B7280"),
                        "risk_reasons": reasons_val,
                        "created_at": r[19].isoformat() if r[19] else None,
                    }
            conn.close()
        except Exception:
            continue
    raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")


@router.get("/summary")
def get_risk_summary(bank: Optional[str] = Query(None)):
    """Return count-by-risk-level summary across all or a specific bank."""
    banks = BANK_NAMES if (not bank or bank.upper() == "ALL") else [bank.upper()]
    summary = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "total": 0}
    bank_breakdown = {}

    for b in banks:
        try:
            conn = get_bank_connection(b)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT risk_level, COUNT(*) FROM risk_assessments
                    GROUP BY risk_level
                """)
                bank_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
                for row in cur.fetchall():
                    level, cnt = row[0], int(row[1])
                    summary[level] = summary.get(level, 0) + cnt
                    summary["total"] += cnt
                    bank_counts[level] = cnt
                bank_breakdown[b] = bank_counts
            conn.close()
        except Exception as e:
            print(f"[RISK SUMMARY] {b}: {e}")

    return {"summary": summary, "by_bank": bank_breakdown}


@router.get("/live")
def get_live_assessments(
    bank: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """Return the most recent risk assessments for live streaming feed."""
    banks = BANK_NAMES if (not bank or bank.upper() == "ALL") else [bank.upper()]
    data = _query_assessments(banks, limit=limit)
    data.sort(key=lambda x: x["assessment_timestamp"] or "", reverse=True)
    return {"assessments": data[:limit]}


@router.get("/account/{account_id}")
@router.get("/account/{account_id}/profile")
def get_account_risk_profile(
    account_id: str,
    bank: Optional[str] = Query(None),
):
    """
    Returns the latest stored behavioural risk profile for an account.
    CRITICAL: Does not recalculate risk on request.
    """
    from .account_risk_profile import get_stored_account_risk_profile
    # Deduce bank from account_id prefix if not provided (e.g. SBI-101 -> SBI)
    bank_name = bank.upper() if bank else None
    if not bank_name:
        for b in BANK_NAMES:
            if account_id.upper().startswith(b):
                bank_name = b
                break
    if not bank_name:
        bank_name = "SBI"

    try:
        conn = get_bank_connection(bank_name)
        profile = get_stored_account_risk_profile(conn, bank_name, account_id)
        conn.close()
        return profile
    except Exception as e:
        print(f"[RISK API] Profile error for {account_id}: {e}")
        return {
            "account_id": account_id,
            "bank_name": bank_name,
            "risk_score": 15.0,
            "risk_level": "LOW",
            "risk_factors": ["Default baseline profile"],
            "recalculation_count": 0,
            "last_trigger_reason": "FALLBACK",
            "last_updated": datetime.now().isoformat(),
        }


@router.get("/account/{account_id}/history")
def get_account_risk_history(
    account_id: str,
    bank: Optional[str] = Query(None),
    limit: int = Query(30, le=100),
):
    """Return recent historical risk assessments for a specific account."""
    banks = BANK_NAMES if (not bank or bank.upper() == "ALL") else [bank.upper()]
    data = _query_assessments(banks, limit=limit, account_id=account_id)
    data.sort(key=lambda x: x["assessment_timestamp"] or "", reverse=True)
    return {"account_id": account_id, "assessments": data}


@router.get("/profiles")
def get_all_risk_profiles(
    bank: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """Returns stored behavioural risk profiles across accounts for Bank Dashboard."""
    banks = BANK_NAMES if (not bank or bank.upper() == "ALL") else [bank.upper()]
    profiles = []
    for b in banks:
        try:
            conn = get_bank_connection(b)
            with conn.cursor() as cur:
                where = ["1=1"]
                params = []
                if risk_level:
                    where.append("risk_level = %s")
                    params.append(risk_level.upper())
                cur.execute(f"""
                    SELECT account_id, bank_name, risk_score, risk_level,
                           risk_factors, recalculation_count, last_trigger_reason,
                           last_updated
                    FROM account_risk_profiles
                    WHERE {" AND ".join(where)}
                    ORDER BY risk_score DESC, last_updated DESC
                    LIMIT %s
                """, params + [limit])
                for r in cur.fetchall():
                    factors = r[4]
                    if isinstance(factors, str):
                        try:
                            factors = json.loads(factors)
                        except Exception:
                            factors = [factors]
                    elif not isinstance(factors, list):
                        factors = []
                    profiles.append({
                        "account_id": r[0],
                        "bank_name": r[1],
                        "risk_score": round(float(r[2]), 2),
                        "risk_level": r[3],
                        "risk_factors": factors,
                        "recalculation_count": int(r[5] or 0),
                        "last_trigger_reason": r[6] or "STORED",
                        "last_updated": r[7].isoformat() if r[7] else None,
                    })
            conn.close()
        except Exception as err:
            print(f"[RISK API] Query profiles error for {b}: {err}")
    return {"profiles": profiles[:limit], "count": len(profiles)}


@router.get("/health")
def health():
    return {"status": "ok", "service": "Bank Risk API"}

