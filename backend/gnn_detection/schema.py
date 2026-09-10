"""
Database Schema and Initialization for GNN Account & Network Assessments.
Creates gnn_account_assessments and gnn_network_assessments tables
in sbi_db, axis_db, and iob_db using direct psycopg2 (no ORM).
"""

import os
import sys
from typing import Dict
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

CREATE_GNN_ACCOUNT_ASSESSMENTS_SQL = """
CREATE TABLE IF NOT EXISTS gnn_account_assessments (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR UNIQUE NOT NULL,
    account_id VARCHAR NOT NULL,
    bank VARCHAR NOT NULL,
    classification VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    mule_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    suspicious_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    normal_probability DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    gnn_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    risk_level VARCHAR NOT NULL DEFAULT 'LOW',
    network_pattern VARCHAR DEFAULT 'UNKNOWN',
    connected_account_count INTEGER DEFAULT 0,
    confidence DOUBLE PRECISION DEFAULT 0.0,
    explanation JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_version VARCHAR DEFAULT 'v1.0.0-gatv2',
    trigger_transaction_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrations for schema additions
ALTER TABLE gnn_account_assessments ADD COLUMN IF NOT EXISTS suspicious_probability DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE gnn_account_assessments ADD COLUMN IF NOT EXISTS normal_probability DOUBLE PRECISION DEFAULT 1.0;
ALTER TABLE gnn_account_assessments ADD COLUMN IF NOT EXISTS model_version VARCHAR DEFAULT 'v1.0.0-gatv2';
ALTER TABLE gnn_account_assessments ADD COLUMN IF NOT EXISTS trigger_transaction_id VARCHAR;
ALTER TABLE gnn_account_assessments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Indices
CREATE INDEX IF NOT EXISTS idx_gnn_acc_account_id ON gnn_account_assessments(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gnn_acc_bank ON gnn_account_assessments(bank, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gnn_acc_classification ON gnn_account_assessments(classification, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gnn_acc_risk_score ON gnn_account_assessments(gnn_risk_score DESC);
"""

CREATE_GNN_NETWORK_ASSESSMENTS_SQL = """
CREATE TABLE IF NOT EXISTS gnn_network_assessments (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR UNIQUE NOT NULL,
    trigger_transaction_id VARCHAR,
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    mule_accounts_detected INTEGER DEFAULT 0,
    suspicious_accounts_detected INTEGER DEFAULT 0,
    network_pattern VARCHAR DEFAULT 'UNKNOWN',
    network_risk_score DOUBLE PRECISION DEFAULT 0.0,
    node_classifications JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gnn_net_tx_id ON gnn_network_assessments(trigger_transaction_id);
CREATE INDEX IF NOT EXISTS idx_gnn_net_risk ON gnn_network_assessments(network_risk_score DESC, created_at DESC);
"""


def initialize_gnn_tables() -> Dict[str, bool]:
    """
    Creates GNN tables in sbi_db, axis_db, and iob_db.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS + ALTER TABLE IF NOT EXISTS.
    """
    try:
        from simulator.db_connection import get_all_bank_connections
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from simulator.db_connection import get_all_bank_connections
        except ImportError:
            print("[GNN Schema] Could not import db_connection — skipping table initialization.")
            return {}

    conns = get_all_bank_connections()
    results = {}

    print("=" * 68)
    print("  GNN Module — Initializing PostgreSQL Tables")
    print("=" * 68)

    for bank, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute(CREATE_GNN_ACCOUNT_ASSESSMENTS_SQL)
                cur.execute(CREATE_GNN_NETWORK_ASSESSMENTS_SQL)
            conn.commit()
            print(f"  [OK] {bank}_db: gnn_account_assessments & gnn_network_assessments ready.")
            results[bank] = True
        except Exception as e:
            conn.rollback()
            print(f"  [ERROR] {bank}_db GNN table init failed: {e}")
            results[bank] = False

    return results


if __name__ == "__main__":
    initialize_gnn_tables()
