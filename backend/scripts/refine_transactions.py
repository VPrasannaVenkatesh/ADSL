import os
import sys
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def refine_db(bank):
    print(f"\n--- Refining {bank} Database ---")
    conn = get_connection(bank)
    cursor = conn.cursor()
    
    # 1. Backdate transactions and accounts
    print("Backdating transactions and accounts...")
    cursor.execute("SELECT MAX(transaction_timestamp) FROM transactions")
    max_ts = cursor.fetchone()[0]
    
    if max_ts:
        now = datetime.datetime.now()
        # Calculate diff in seconds
        delta_seconds = (now - max_ts).total_seconds()
        
        # Shift transactions
        cursor.execute("""
            UPDATE transactions 
            SET transaction_timestamp = transaction_timestamp + interval '%s seconds'
        """, (delta_seconds,))
        
        # Shift accounts
        delta_days = int(delta_seconds / 86400)
        cursor.execute("""
            UPDATE accounts 
            SET account_created_date = account_created_date + interval '%s days'
        """, (delta_days,))
        
        conn.commit()

    # 2. Split device info
    print("Splitting device info...")
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS device_type VARCHAR;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS ip_address VARCHAR;")
        conn.commit()
        
        cursor.execute("""
            UPDATE transactions 
            SET device_type = split_part(device_info, ' (', 1),
                ip_address = replace(split_part(device_info, ' (', 2), ')', '')
            WHERE device_info IS NOT NULL;
        """)
        conn.commit()
        
        # Only drop after successful parsing
        cursor.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS device_info;")
        conn.commit()
    except Exception as e:
        print(f"Error splitting device info: {e}")
        conn.rollback()

    # 3. Simulate Mule Locations
    print("Injecting mule location anomalies (5% accounts)...")
    # We assign 5% of accounts to have a random location for their transactions based on the tx id
    cursor.execute("""
        UPDATE transactions t
        SET location = (
            ARRAY['Chennai', 'Bengaluru', 'Delhi', 'Mumbai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Indore', 'Kochi']
        )[mod(abs(('x' || substr(md5(t.transaction_id), 1, 8))::bit(32)::int), 12) + 1]
        FROM accounts a
        WHERE t.sender_account_id = a.account_id 
        AND mod(abs(('x' || substr(md5(a.account_id), 1, 8))::bit(32)::int), 100) < 5;
    """)
    conn.commit()
    
    cursor.close()
    conn.close()
    print(f"Refinement for {bank} complete.")

if __name__ == "__main__":
    for bank in BANKS:
        refine_db(bank)
