import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def fix_transactions():
    for bank in BANKS:
        print(f"\n--- Fixing Transactions in {bank} ---")
        try:
            conn = get_connection(bank)
            cursor = conn.cursor()
            
            # 1. Recreate behaviour_history schema according to new massive table structure
            print("Dropping old behaviour_history schema (including triggers) and applying new schema...")
            # We first drop the trigger we added earlier
            cursor.execute("DROP TRIGGER IF EXISTS trg_tx_insert ON transactions CASCADE;")
            cursor.execute("DROP FUNCTION IF EXISTS trg_update_behaviour_on_tx() CASCADE;")
            cursor.execute("DROP FUNCTION IF EXISTS update_behaviour_profile(VARCHAR, TIMESTAMP) CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS behaviour_history CASCADE;")
            conn.commit()
            
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            cursor.execute(schema_sql)
            conn.commit()

            # 2. Add sender_bank
            print("Adding sender_bank column...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN IF NOT EXISTS sender_bank VARCHAR;
            """)
            conn.commit()
            
            print("Populating sender_bank...")
            cursor.execute("""
                UPDATE transactions 
                SET sender_bank = split_part(sender_account_id, '-', 1)
                WHERE sender_bank IS NULL;
            """)
            
            # 3. Fix unknown locations deterministically
            print("Fixing unknown locations...")
            cursor.execute("""
                UPDATE transactions
                SET location = (
                    ARRAY['Chennai', 'Bengaluru', 'Delhi', 'Mumbai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Indore', 'Kochi']
                )[mod(abs(('x' || substr(md5(sender_account_id), 1, 8))::bit(32)::int), 12) + 1]
                WHERE location = 'Unknown' OR location IS NULL;
            """)
            
            # Make sender_bank NOT NULL now that it is populated
            cursor.execute("ALTER TABLE transactions ALTER COLUMN sender_bank SET NOT NULL;")
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Fixed {bank}.")
        except Exception as e:
            print(f"Error fixing {bank}: {e}")
            if 'conn' in locals():
                conn.rollback()

if __name__ == "__main__":
    fix_transactions()
