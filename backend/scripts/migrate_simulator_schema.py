import os, sys, random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.db_connection import get_bank_connection

BUSINESS_CATEGORIES = [
    ("Retail Merchant", "INR 5,000 - 1,50,000", "Continuous daily customer receipts"),
    ("Wholesale Supplier", "INR 1,00,000 - 15,00,000", "Weekly bulk B2B vendor settlements"),
    ("IT & Corporate Services", "INR 50,000 - 20,00,000", "Monthly payroll & vendor payouts"),
    ("Logistics & Transport", "INR 25,000 - 5,00,000", "Daily freight & fuel settlements"),
    ("Healthcare & Pharmacy", "INR 10,000 - 3,00,000", "Frequent high-volume supplier payments"),
]

def migrate():
    for bank in ["SBI", "AXIS", "IOB"]:
        print(f"Migrating {bank} database...")
        conn = get_bank_connection(bank)
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE transactions 
                ADD COLUMN IF NOT EXISTS honeypot_status VARCHAR DEFAULT 'NOT_TRANSFERRED',
                ADD COLUMN IF NOT EXISTS lien_status VARCHAR DEFAULT 'NO_LIEN';
            """)
            cur.execute("""
                ALTER TABLE accounts 
                ADD COLUMN IF NOT EXISTS business_category VARCHAR,
                ADD COLUMN IF NOT EXISTS expected_tx_range VARCHAR,
                ADD COLUMN IF NOT EXISTS tx_frequency_pattern VARCHAR;
            """)
            cur.execute("SELECT account_id FROM accounts WHERE account_type = 'BUSINESS' AND business_category IS NULL")
            biz_accounts = cur.fetchall()
            for acc in biz_accounts:
                cat, rng, freq = random.choice(BUSINESS_CATEGORIES)
                cur.execute("""
                    UPDATE accounts 
                    SET business_category = %s, expected_tx_range = %s, tx_frequency_pattern = %s 
                    WHERE account_id = %s
                """, (cat, rng, freq, acc[0]))
            cur.execute("""
                UPDATE transactions 
                SET honeypot_status = CASE 
                    WHEN transaction_status = 'HONEYPOT' THEN 'TRANSFERRED'
                    WHEN transaction_status IN ('RESTRICTED', 'FROZEN') THEN 'TRANSFERRED'
                    WHEN transaction_status = 'RELEASED' THEN 'RELEASED'
                    ELSE 'NOT_TRANSFERRED'
                END,
                lien_status = CASE
                    WHEN transaction_status IN ('LIEN_APPLIED', 'HONEYPOT', 'RESTRICTED', 'FROZEN') THEN 'LIEN_APPLIED'
                    WHEN transaction_status = 'RELEASED' THEN 'LIEN_RELEASED'
                    ELSE 'NO_LIEN'
                END
WHERE honeypot_status IS NULL OR lien_status IS NULL;
            """)
        conn.commit()
        conn.close()
        print(f"{bank} migrated successfully!")

if __name__ == '__main__':
    migrate()
