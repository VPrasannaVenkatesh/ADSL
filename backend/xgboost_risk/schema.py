"""
Database schema definition, migrations, and initialization for XGBoost Transaction Risk Assessments.
Stores all 18 transaction processing & risk assessment attributes.
Uses direct psycopg2 connections (zero SQLAlchemy / Alembic).
"""

import os
import sys
from typing import Dict
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.db_connection import get_all_bank_connections, BANK_NAMES

CREATE_TRANSACTION_RISK_ASSESSMENTS_SQL = """
CREATE TABLE IF NOT EXISTS transaction_risk_assessments (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR UNIQUE NOT NULL,
    transaction_id VARCHAR NOT NULL,
    bank VARCHAR NOT NULL,
    sender_account_id VARCHAR NOT NULL,
    receiver_account_id VARCHAR NOT NULL,
    sender_bank VARCHAR,
    receiver_bank VARCHAR,
    amount BIGINT DEFAULT 0,
    
    -- Risk Scores (0.0 to 100.0)
    sender_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    receiver_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    xgboost_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    combined_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    network_risk DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    
    -- Risk Classification & Metrics
    risk_level VARCHAR NOT NULL DEFAULT 'LOW',                -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    prediction_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    top_risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    coordinator_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version VARCHAR NOT NULL DEFAULT 'v1.0.0-xgb',
    decision_status VARCHAR NOT NULL DEFAULT 'ALLOW',          -- 'ALLOW', 'MONITOR', 'CONTROLLED_ACTION'
    final_decision VARCHAR NOT NULL DEFAULT 'ALLOW',
    transaction_status VARCHAR NOT NULL DEFAULT 'COMPLETED',
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrations to guarantee all 18 fields exist on existing tables
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS sender_bank VARCHAR;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS receiver_bank VARCHAR;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS amount BIGINT DEFAULT 0;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS risk_reasons JSONB DEFAULT '[]'::jsonb;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS coordinator_result JSONB DEFAULT '{}'::jsonb;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS network_risk DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS final_decision VARCHAR DEFAULT 'ALLOW';
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS transaction_status VARCHAR DEFAULT 'COMPLETED';
ALTER TABLE transaction_risk_assessments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Performance indices for fast real-time lookups & analytics
CREATE INDEX IF NOT EXISTS idx_tra_tx_id ON transaction_risk_assessments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_tra_bank_ts ON transaction_risk_assessments(bank, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tra_risk_level ON transaction_risk_assessments(risk_level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tra_flagged ON transaction_risk_assessments(flagged, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tra_combined_score ON transaction_risk_assessments(combined_risk_score DESC);
"""


def initialize_xgboost_tables() -> Dict[str, bool]:
    """
    Initializes transaction_risk_assessments table across sbi_db, axis_db, and iob_db.
    """
    conns = get_all_bank_connections()
    results = {}
    print("=" * 68)
    print("  Initializing & Migrating transaction_risk_assessments in PostgreSQL DBs")
    print("=" * 68)
    for bank, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute(CREATE_TRANSACTION_RISK_ASSESSMENTS_SQL)
            conn.commit()
            print(f"  [OK] {bank}_db: transaction_risk_assessments table migrated & verified.")
            results[bank] = True
        except Exception as e:
            conn.rollback()
            print(f"  [ERROR] {bank}_db failed to initialize: {e}")
            results[bank] = False

    return results


if __name__ == "__main__":
    initialize_xgboost_tables()
