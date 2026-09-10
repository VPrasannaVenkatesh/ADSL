"""
Decentralized Bank Risk Sharing Endpoints.
Exposed by each bank to provide strictly privacy-preserving risk responses to the Coordinator.
Zero raw PII, zero balances, zero raw ledger rows are shared.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from simulator.db_connection import get_bank_connection, BANK_NAMES
from .models import BankRiskShareResponse, mask_account_id

bank_risk_share_router = APIRouter(prefix="/api/banks", tags=["Decentralized Bank Risk Sharing"])


def fetch_bank_risk_share(bank_name: str, transaction_id: str, side: str = "SENDER") -> Optional[BankRiskShareResponse]:
    """
    Direct function to query a bank's private assessment and format into privacy-preserving payload.
    """
    b = bank_name.upper()
    if b not in BANK_NAMES:
        return None

    try:
        conn = get_bank_connection(b)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT transaction_id, bank_name, role, account_id,
                       final_risk_score, risk_level, risk_reasons, assessment_timestamp
                FROM risk_assessments
                WHERE transaction_id = %s AND role = %s
                LIMIT 1
            """, (transaction_id, side.upper()))
            row = cur.fetchone()
            if not row:
                # Fallback check without role in case of same-bank matching
                cur.execute("""
                    SELECT transaction_id, bank_name, role, account_id,
                           final_risk_score, risk_level, risk_reasons, assessment_timestamp
                    FROM risk_assessments
                    WHERE transaction_id = %s
                    LIMIT 1
                """, (transaction_id,))
                row = cur.fetchone()

            if row:
                xgb_score = None
                comb_score = None
                is_flagged = None
                try:
                    cur.execute("""
                        SELECT xgboost_risk_score, combined_risk_score, flagged
                        FROM transaction_risk_assessments
                        WHERE transaction_id = %s
                        LIMIT 1
                    """, (transaction_id,))
                    xgb_row = cur.fetchone()
                    if xgb_row:
                        xgb_score = round(float(xgb_row[0]), 2)
                        comb_score = round(float(xgb_row[1]), 2)
                        is_flagged = bool(xgb_row[2])
                except Exception:
                    pass

                conn.close()
                reasons = row[6]
                if isinstance(reasons, str):
                    try:
                        reasons = json.loads(reasons)
                    except Exception:
                        reasons = [reasons]
                elif not isinstance(reasons, list):
                    reasons = []

                return BankRiskShareResponse(
                    transaction_id=row[0],
                    bank_name=row[1],
                    transaction_side=row[2],
                    masked_account_id=mask_account_id(row[3]),
                    local_risk_score=round(float(row[4]), 2),
                    risk_level=row[5],
                    top_risk_indicators=reasons[:4],
                    assessment_timestamp=row[7],
                    xgboost_risk_score=xgb_score,
                    combined_risk_score=comb_score,
                    flagged=is_flagged,
                )
        conn.close()
    except Exception as e:
        print(f"[BANK RISK SHARE] Error querying {b} for {transaction_id}: {e}")

    return None


@bank_risk_share_router.get("/{bank_name}/risk-share/{transaction_id}", response_model=BankRiskShareResponse)
def get_bank_risk_share_endpoint(
    bank_name: str,
    transaction_id: str,
    side: str = Query("SENDER", description="SENDER or RECEIVER"),
):
    """
    Bank-level API endpoint: Returns privacy-preserving risk assessment for the specified transaction.
    Only accessible by the Coordinator for participating banks.
    """
    b = bank_name.upper()
    if b not in BANK_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid bank name: {bank_name}. Must be SBI, AXIS, or IOB.")

    result = fetch_bank_risk_share(b, transaction_id, side)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No risk assessment found in {b} for transaction {transaction_id} (Side: {side})"
        )

    return result
