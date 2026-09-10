"""
Risk Assessment Storage.
Persists RiskAssessmentResult into the bank's risk_assessments table via psycopg2.
"""

import uuid
import json
from datetime import datetime
from typing import Dict
import psycopg2

from .aggregator import RiskAssessmentResult


def store_risk_assessment(
    conn: psycopg2.extensions.connection,
    result: RiskAssessmentResult,
) -> str:
    """
    Inserts a completed risk assessment into the bank's risk_assessments table.
    Returns the generated assessment_id.
    """
    assessment_id = f"RA_{uuid.uuid4().hex[:14].upper()}"

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO risk_assessments (
                assessment_id, transaction_id, account_id, bank_name, role,
                amount, transaction_type, assessment_timestamp,
                amount_risk, velocity_risk, behaviour_deviation_risk,
                device_risk, location_risk, counterparty_risk,
                timing_risk, network_pattern_risk,
                final_risk_score, risk_level, risk_reasons
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (assessment_id) DO NOTHING
        """, (
            assessment_id,
            result.transaction_id,
            result.account_id,
            result.bank_name,
            result.role,
            result.amount,
            result.transaction_type,
            result.assessment_timestamp,
            result.amount_risk,
            result.velocity_risk,
            result.behaviour_deviation_risk,
            result.device_risk,
            result.location_risk,
            result.counterparty_risk,
            result.timing_risk,
            result.network_pattern_risk,
            result.final_risk_score,
            result.risk_level,
            json.dumps(result.risk_reasons),
        ))
    conn.commit()
    return assessment_id
