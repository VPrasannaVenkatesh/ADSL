"""
Database connectivity helpers for PostgreSQL bank databases.
"""

import os
from typing import Dict, Optional
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


def get_connection(bank_name: str) -> psycopg2.extensions.connection:
    """
    Returns a psycopg2 connection for the specified bank (SBI, AXIS, IOB).
    """
    env_var = f"{bank_name.upper()}_DATABASE_URL"
    db_url = os.environ.get(env_var)
    if not db_url:
        # Fallback to standard PG connection parameters
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        db_name = f"{bank_name.lower()}_db"
        return psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
    return psycopg2.connect(db_url)


def get_all_connections() -> Dict[str, psycopg2.extensions.connection]:
    """
    Returns open connections for all 3 bank databases.
    """
    return {
        "SBI": get_connection("SBI"),
        "AXIS": get_connection("AXIS"),
        "IOB": get_connection("IOB"),
    }


def fetch_global_max_timestamp(conns: Dict[str, psycopg2.extensions.connection]) -> datetime:
    """
    Finds the latest transaction_timestamp across all 3 databases.
    """
    max_ts = None
    for bank, conn in conns.items():
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(transaction_timestamp) FROM transactions")
            res = cur.fetchone()[0]
            if res:
                if max_ts is None or res > max_ts:
                    max_ts = res
    if max_ts is None:
        max_ts = datetime.now()
    return max_ts
