"""
Database connection manager for multi-bank simulation.
Provides direct psycopg2 connections to sbi_db, axis_db, and iob_db using .env configuration.
"""

import os
from typing import Dict
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Load environment variables from backend/.env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path)

BANK_NAMES = ["SBI", "AXIS", "IOB"]


def get_bank_connection(bank_name: str) -> psycopg2.extensions.connection:
    """
    Returns a live psycopg2 connection for the specified bank (SBI, AXIS, or IOB).
    """
    b = bank_name.upper()
    if b not in BANK_NAMES:
        raise ValueError(f"Unknown bank '{bank_name}'. Must be one of {BANK_NAMES}")

    env_var = f"{b}_DATABASE_URL"
    db_url = os.environ.get(env_var)

    if db_url:
        return psycopg2.connect(db_url)

    # Fallback to standard environment parameters
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    db_name = f"{b.lower()}_db"

    return psycopg2.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port
    )


def get_all_bank_connections() -> Dict[str, psycopg2.extensions.connection]:
    """
    Returns active connections for all 3 bank databases: sbi_db, axis_db, and iob_db.
    """
    return {
        "SBI": get_bank_connection("SBI"),
        "AXIS": get_bank_connection("AXIS"),
        "IOB": get_bank_connection("IOB"),
    }


def fetch_latest_transaction_timestamp(conns: Dict[str, psycopg2.extensions.connection]) -> datetime:
    """
    Finds the maximum transaction_timestamp recorded across all 3 databases
    to establish the chronological baseline for new live transactions.
    """
    max_ts = None
    for bank, conn in conns.items():
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(transaction_timestamp) FROM transactions")
            row = cur.fetchone()
            if row and row[0]:
                if max_ts is None or row[0] > max_ts:
                    max_ts = row[0]

    return max_ts or datetime.now()
