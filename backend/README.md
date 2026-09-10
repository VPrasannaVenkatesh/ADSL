# ADSL — Module 1 Database Layer (3 Independent Banks)

This backend implements three fully isolated PostgreSQL databases (`sbi_db`, `axis_db`, and `iob_db`) for the ADSL Module 1 simulation.

## Setup

1. Copy `.env.example` to `.env` and set your PostgreSQL credentials.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Provision databases: `python database/create_databases.py`
4. Generate accounts & 100k transactions: `python database/populate_databases.py`
5. Verify structure: `python scripts/verify_databases.py`
