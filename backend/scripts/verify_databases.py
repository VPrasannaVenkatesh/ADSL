import os
import sys

# Add parent directory to path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def verify():
    for bank in BANKS:
        print(f"--- Verifying {bank}_DB ---")
        try:
            conn = get_connection(bank)
            cursor = conn.cursor()
            
            # Check accounts
            cursor.execute("SELECT COUNT(*) FROM accounts")
            acc_count = cursor.fetchone()[0]
            print(f"  Accounts: {acc_count}")
            
            # Check transactions
            cursor.execute("SELECT COUNT(*) FROM transactions")
            tx_count = cursor.fetchone()[0]
            print(f"  Transactions: {tx_count}")
            
            # Check behaviour history
            cursor.execute("SELECT COUNT(*) FROM behaviour_history")
            bh_count = cursor.fetchone()[0]
            print(f"  Behaviour History Records: {bh_count}")
            
            if acc_count == 500:
                print("  ✅ Account count is correct.")
            else:
                print(f"  ❌ Account count incorrect! Expected 500, got {acc_count}")
                
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"  ❌ Failed to verify {bank}_DB: {e}")
            
    print("\n✅ Verification complete.")

if __name__ == "__main__":
    verify()
