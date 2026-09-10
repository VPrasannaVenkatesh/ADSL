import os
import sys
import random

# Add parent directory to path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def migrate_db(bank):
    print(f"\n--- Migrating {bank} Database ---")
    conn = get_connection(bank)
    cursor = conn.cursor()
    
    # 1. Update Transactions Schema
    print("Updating transactions schema...")
    try:
        cursor.execute("ALTER TABLE transactions RENAME COLUMN device_id TO device_info;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        pass # Might already be renamed or doesn't exist
        
    # Generate realistic device info for existing transactions
    print("Synthesizing IP and Device Info for existing transactions...")
    # Instead of updating row by row in python, we can do it in SQL or just map it per account to simulate "most used device"
    # To do it quickly in SQL:
    cursor.execute("""
        UPDATE transactions 
        SET device_info = 
            CASE (id % 4)
                WHEN 0 THEN 'Mobile (' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || ')'
                WHEN 1 THEN 'Desktop (' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || ')'
                WHEN 2 THEN 'Laptop (' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || ')'
                ELSE 'Tablet (' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || '.' || (floor(random() * 255)::int) || ')'
            END
        WHERE device_info NOT LIKE '%(%)%' OR device_info IS NULL;
    """)
    conn.commit()
    
    # 2. Drop and Recreate Behaviour History table
    print("Dropping old behaviour_history and recreating from schema...")
    cursor.execute("DROP TABLE IF EXISTS behaviour_history CASCADE;")
    conn.commit()
    
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    cursor.execute(schema_sql)
    conn.commit()
    
    # 3. Initialize all accounts with 0-value behaviour profiles
    print("Initializing base behaviour profiles...")
    cursor.execute("""
        INSERT INTO behaviour_history (account_id)
        SELECT account_id FROM accounts
    """)
    conn.commit()
    
    # 4. Calculate full profile for all accounts by calling the new trigger function
    print("Recalculating complete dynamic profiles for all accounts...")
    cursor.execute("""
        SELECT update_behaviour_profile(a.account_id, CURRENT_TIMESTAMP::TIMESTAMP)
        FROM accounts a
    """)
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM behaviour_history")
    bh_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM behaviour_history WHERE sent_transaction_count > 0 OR received_transaction_count > 0")
    active_bh = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM accounts")
    acc_count = cursor.fetchone()[0]
    
    print(f"  Total Accounts: {acc_count}")
    print(f"  Total Behaviour Profiles: {bh_count}")
    print(f"  Profiles with Activity: {active_bh}")
    
    cursor.close()
    conn.close()
    print(f"Migration for {bank} complete.")

if __name__ == "__main__":
    for bank in BANKS:
        migrate_db(bank)
