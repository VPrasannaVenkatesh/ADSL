import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def fix_feedback():
    for bank in BANKS:
        conn = get_connection(bank)
        cursor = conn.cursor()
        
        # Set interval readable to N/A for single transactions
        cursor.execute("""
            UPDATE behaviour_history 
            SET avg_transaction_interval_readable = 'N/A (Single TX)', 
                min_transaction_interval_readable = 'N/A (Single TX)'
            WHERE transaction_count = 1;
        """)
        
        # Check if we have non-zero short_dwell_count
        cursor.execute("SELECT COUNT(*) FROM behaviour_history WHERE short_dwell_count > 0;")
        dwell_count = cursor.fetchone()[0]
        
        # Check if we have non-zero amount_split_count
        cursor.execute("SELECT COUNT(*) FROM behaviour_history WHERE amount_split_count > 0;")
        split_count = cursor.fetchone()[0]
        
        # Check total profiles
        cursor.execute("SELECT COUNT(*) FROM behaviour_history;")
        total_count = cursor.fetchone()[0]
        
        print(f"[{bank}] Total profiles: {total_count}")
        print(f"[{bank}] Fixed intervals.")
        print(f"[{bank}] Profiles with short dwell > 0: {dwell_count}")
        print(f"[{bank}] Profiles with amount split > 0: {split_count}")
        print("-" * 40)
        
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_feedback()
