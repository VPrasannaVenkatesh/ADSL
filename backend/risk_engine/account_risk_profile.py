"""
Stored Behavioural Risk Profile Engine for Bank Accounts.
Implements:
- account_risk_profiles schema in PostgreSQL across sbi_db, axis_db, and iob_db
- Stored profile retrieval (GET /risk/account/{id} returns stored score WITHOUT recalculation)
- Smart recalculation: updates risk ONLY when meaningful behavioural changes occur
"""

import json
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple, List
import psycopg2
from psycopg2.extras import RealDictCursor

from .aggregator import score_to_level, RISK_WEIGHTS, run_risk_assessment
from .feature_extractor import extract_account_features

CREATE_ACCOUNT_RISK_PROFILES_SQL = """
CREATE TABLE IF NOT EXISTS account_risk_profiles (
    account_id VARCHAR PRIMARY KEY,
    bank_name VARCHAR NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 15.0,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW',
    risk_factors JSONB DEFAULT '[]'::jsonb,
    baseline_metrics JSONB DEFAULT '{}'::jsonb,
    recalculation_count INTEGER DEFAULT 0,
    last_trigger_reason VARCHAR DEFAULT 'INITIAL_BASELINE',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_arp_bank ON account_risk_profiles(bank_name);
CREATE INDEX IF NOT EXISTS idx_arp_risk_score ON account_risk_profiles(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_arp_risk_level ON account_risk_profiles(risk_level);
"""


def initialize_account_risk_profiles_table(conn: psycopg2.extensions.connection):
    """Creates the account_risk_profiles table if it does not exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_ACCOUNT_RISK_PROFILES_SQL)
    conn.commit()


def initialize_all_account_risk_tables():
    """Initializes account_risk_profiles in all bank databases."""
    try:
        from simulator.db_connection import get_all_bank_connections
        conns = get_all_bank_connections()
        for bank, conn in conns.items():
            try:
                initialize_account_risk_profiles_table(conn)
                print(f"[Bank Risk Provider] account_risk_profiles ready in {bank}_db.")
            except Exception as e:
                print(f"[Bank Risk Provider] Error initializing in {bank}: {e}")
            finally:
                conn.close()
    except Exception as err:
        print(f"[Bank Risk Provider] Table init err: {err}")


def get_stored_account_risk_profile(
    conn: psycopg2.extensions.connection,
    bank_name: str,
    account_id: str,
) -> Dict[str, Any]:
    """
    Returns the latest STORED behavioural risk profile for an account.
    CRITICAL REQUIREMENT: Does NOT recalculate the risk score on demand.
    """
    initialize_account_risk_profiles_table(conn)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT account_id, bank_name, risk_score, risk_level,
                   risk_factors, baseline_metrics, recalculation_count,
                   last_trigger_reason, last_updated
            FROM account_risk_profiles
            WHERE account_id = %s
            LIMIT 1
        """, (account_id,))
        row = cur.fetchone()

        if row:
            factors = row[4]
            if isinstance(factors, str):
                try:
                    factors = json.loads(factors)
                except Exception:
                    factors = [factors]
            elif not isinstance(factors, list):
                factors = []

            return {
                "account_id": row[0],
                "bank_name": row[1],
                "risk_score": round(float(row[2]), 2),
                "risk_level": row[3],
                "risk_factors": factors,
                "recalculation_count": int(row[6] or 0),
                "last_trigger_reason": row[7] or "STORED",
                "last_updated": row[8].isoformat() if row[8] else datetime.now().isoformat(),
            }

    # If no profile exists yet, seed an initial baseline profile and store it
    initial_score = 15.0
    initial_level = "LOW"
    initial_factors = ["Initial Account Baseline Established"]

    # Check recent assessments if any existed in risk_assessments table
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT final_risk_score, risk_level, risk_reasons, assessment_timestamp
                FROM risk_assessments
                WHERE account_id = %s
                ORDER BY assessment_timestamp DESC
                LIMIT 1
            """, (account_id,))
            prev = cur.fetchone()
            if prev:
                initial_score = round(float(prev[0]), 2)
                initial_level = prev[1]
                reasons = prev[2]
                if isinstance(reasons, str):
                    try:
                        reasons = json.loads(reasons)
                    except Exception:
                        reasons = [reasons]
                if isinstance(reasons, list) and reasons:
                    initial_factors = reasons
    except Exception:
        pass

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO account_risk_profiles (
                account_id, bank_name, risk_score, risk_level,
                risk_factors, recalculation_count, last_trigger_reason, last_updated
            ) VALUES (%s, %s, %s, %s, %s, 0, 'INITIAL_SEED', CURRENT_TIMESTAMP)
            ON CONFLICT (account_id) DO NOTHING
        """, (
            account_id,
            bank_name.upper(),
            initial_score,
            initial_level,
            json.dumps(initial_factors),
        ))
    conn.commit()

    return {
        "account_id": account_id,
        "bank_name": bank_name.upper(),
        "risk_score": initial_score,
        "risk_level": initial_level,
        "risk_factors": initial_factors,
        "recalculation_count": 0,
        "last_trigger_reason": "INITIAL_SEED",
        "last_updated": datetime.now().isoformat(),
    }


def check_meaningful_behaviour_change(
    features: Dict[str, Any],
    stored_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether a transaction introduces a meaningful behavioural change
    requiring account risk profile recalculation.

    Triggers:
    - Large amount deviation from baseline (amount > 3.0x 90-day avg or > baseline max)
    - Significant transaction velocity spike (txns_1h >= 3 or txns_24h >= 6)
    - New or unusual device (new_device=True or unique_devices >= 2)
    - New location or rapid location changes (new_location=True or location_changes >= 2)
    - Multiple new beneficiaries (new_recipients >= 2)
    - Rapid fund forwarding / short dwell (short_dwell_count > 0 or same_day_forward > 0)
    - Fan-in behaviour (fan_in >= 3)
    - Fan-out behaviour (fan_out >= 3)
    - Amount splitting (amount_split_count > 0)
    - Dormant account suddenly becoming active (zero prior volume but now large transaction)
    """
    if not features:
        return False, None

    amount = features.get("txn_amount", 0)
    avg_amt = features.get("baseline_avg_amount", 0) or 5000
    max_amt = features.get("baseline_max_amount", 0) or 50000

    # 1. Large amount deviation
    if amount > 3.0 * avg_amt and amount > 25000:
        return True, f"Large amount deviation: INR {amount:,} vs baseline avg INR {avg_amt:,}"
    if amount > 1.5 * max_amt and amount > 50000:
        return True, f"Exceeds historical maximum transaction amount: INR {amount:,}"

    # 2. Significant velocity spike
    txns_1h = features.get("transactions_1h", 0) or 0
    txns_24h = features.get("transactions_24h", 0) or 0
    if txns_1h >= 3:
        return True, f"Transaction velocity spike: {txns_1h} transactions in 1 hour"
    if txns_24h >= 8:
        return True, f"Unusual 24-hour transaction frequency: {txns_24h} transactions"

    # 3. New or unusual device
    if features.get("new_device"):
        return True, "New or unusual device detected for account"
    if (features.get("device_change_count", 0) or 0) >= 2:
        return True, "Multiple device changes observed"

    # 4. New location or rapid location shifts
    if features.get("new_location"):
        return True, f"New transaction location: {features.get('txn_location')}"
    if (features.get("location_change_count", 0) or 0) >= 2:
        return True, "Rapid location changes across short timeframe"

    # 5. Multiple new beneficiaries
    new_recipients = features.get("new_recipients_count", 0) or 0
    if new_recipients >= 2:
        return True, f"Multiple new beneficiaries added ({new_recipients})"

    # 6. Rapid fund forwarding
    if (features.get("same_day_forward_count", 0) or 0) > 0 or (features.get("short_dwell_count", 0) or 0) > 0:
        return True, "Rapid fund forwarding / short dwell time pattern detected"

    # 7. Fan-in or Fan-out behaviour
    fan_in = features.get("fan_in", 0) or 0
    fan_out = features.get("fan_out", 0) or 0
    if fan_in >= 3:
        return True, f"Fan-in pattern: {fan_in} incoming flows concentrated"
    if fan_out >= 3:
        return True, f"Fan-out pattern: {fan_out} outgoing dispersals"

    # 8. Amount splitting (smurfing)
    if (features.get("amount_split_count", 0) or 0) > 0:
        return True, "Structured amount splitting (smurfing) pattern"

    # 9. Dormant account reactivation
    total_txns = features.get("total_historical_txns", 0) or 0
    if total_txns < 3 and amount >= 20000:
        return True, "Dormant or newly opened account suddenly conducting high-value transaction"

    return False, None


def recalculate_and_store_profile(
    conn: psycopg2.extensions.connection,
    bank_name: str,
    account_id: str,
    trigger_reason: str,
    features: Dict[str, Any],
    role: str = "SENDER",
    transaction_id: str = "SYSTEM_SYNC",
) -> Dict[str, Any]:
    """
    Executes full behavioural risk calculation and updates the stored profile in PostgreSQL.
    """
    initialize_account_risk_profiles_table(conn)

    assessment = run_risk_assessment(
        transaction_id=transaction_id,
        features=features,
        role=role,
    )

    new_score = round(float(assessment.final_risk_score), 2)
    new_level = assessment.risk_level
    factors = list(assessment.risk_reasons)
    if trigger_reason and trigger_reason not in factors:
        factors.insert(0, trigger_reason)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO account_risk_profiles (
                account_id, bank_name, risk_score, risk_level,
                risk_factors, recalculation_count, last_trigger_reason,
                last_updated
            ) VALUES (
                %s, %s, %s, %s, %s, 1, %s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (account_id) DO UPDATE SET
                risk_score = EXCLUDED.risk_score,
                risk_level = EXCLUDED.risk_level,
                risk_factors = EXCLUDED.risk_factors,
                recalculation_count = account_risk_profiles.recalculation_count + 1,
                last_trigger_reason = EXCLUDED.last_trigger_reason,
                last_updated = CURRENT_TIMESTAMP
            RETURNING recalculation_count, last_updated
        """, (
            account_id,
            bank_name.upper(),
            new_score,
            new_level,
            json.dumps(factors),
            trigger_reason,
        ))
        row = cur.fetchone()
        recalc_count = row[0] if row else 1
        last_updated = row[1].isoformat() if row and row[1] else datetime.now().isoformat()

    conn.commit()

    return {
        "account_id": account_id,
        "bank_name": bank_name.upper(),
        "risk_score": new_score,
        "risk_level": new_level,
        "risk_factors": factors,
        "recalculation_count": recalc_count,
        "last_trigger_reason": trigger_reason,
        "last_updated": last_updated,
    }
