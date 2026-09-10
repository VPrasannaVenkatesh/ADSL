import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.db_connection import get_all_bank_connections, BANK_NAMES

CREATE_RISK_ASSESSMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS risk_assessments (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR UNIQUE NOT NULL,
    transaction_id VARCHAR NOT NULL,
    account_id VARCHAR NOT NULL,
    bank_name VARCHAR NOT NULL,
    role VARCHAR NOT NULL,                      -- 'SENDER' or 'RECEIVER'
    amount BIGINT NOT NULL,
    transaction_type VARCHAR NOT NULL,
    assessment_timestamp TIMESTAMP NOT NULL,
    
    -- 8 Individual Risk Component Scores (0 to 100)
    amount_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    velocity_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    behaviour_deviation_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    device_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    location_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    counterparty_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    timing_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    network_pattern_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    
    -- Aggregated Risk Score & Category
    final_risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR NOT NULL,                -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    risk_reasons JSONB NOT NULL,                -- Array of explainable risk reason strings
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indices for live risk monitoring queries
CREATE INDEX IF NOT EXISTS idx_ra_bank_ts ON risk_assessments(bank_name, assessment_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ra_account_ts ON risk_assessments(account_id, assessment_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ra_tx_id ON risk_assessments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_ra_risk_level ON risk_assessments(risk_level, assessment_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ra_final_score ON risk_assessments(final_risk_score DESC);
"""


def initialize_risk_tables():
    """Applies risk_assessments table to all 3 bank databases."""
    conns = get_all_bank_connections()
    print("=" * 68)
    print("  Initializing Bank-Level Risk Assessment Tables in PostgreSQL")
    print("=" * 68)
    for bank, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute(CREATE_RISK_ASSESSMENTS_TABLE_SQL)
            conn.commit()
            print(f"  [OK] {bank}_db: risk_assessments table & indices ready")
        except Exception as e:
            conn.rollback()
            print(f"  [ERROR] {bank}_db: {e}")
            raise e
        finally:
            conn.close()
    print("=" * 68)


if __name__ == "__main__":
    initialize_risk_tables()
