import os
import sys
import random
import datetime

# Add parent directory to path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

DEVICE_TYPES = ["mobile", "desktop", "tablet", "atm", "branch_terminal"]

def get_realistic_creation_date(min_tx_date):
    """
    Generate a realistic creation date before min_tx_date.
    Distribution:
    - 20% 5-10 years ago (1825 - 3650 days)
    - 40% 2-5 years ago (730 - 1825 days)
    - 30% 1-2 years ago (365 - 730 days)
    - 10% recent (30 - 365 days)
    """
    rand = random.random()
    if rand < 0.20:
        days_ago = random.randint(1825, 3650)
    elif rand < 0.60:
        days_ago = random.randint(730, 1825)
    elif rand < 0.90:
        days_ago = random.randint(365, 730)
    else:
        days_ago = random.randint(30, 365)
        
    created_date = datetime.date.today() - datetime.timedelta(days=days_ago)
    
    # Ensure it's before the first transaction
    if min_tx_date:
        min_tx_date_only = min_tx_date.date()
        if created_date >= min_tx_date_only:
            created_date = min_tx_date_only - datetime.timedelta(days=random.randint(10, 100))
            
    return created_date

def fix_db(bank):
    print(f"\n--- Fixing {bank} Database ---")
    conn = get_connection(bank)
    cursor = conn.cursor()
    
    # 1. Update Accounts (account_created_date and created_at)
    cursor.execute("""
        SELECT a.account_id, MIN(t.transaction_timestamp) 
        FROM accounts a
        LEFT JOIN transactions t ON a.account_id = t.sender_account_id
        GROUP BY a.account_id
    """)
    accounts = cursor.fetchall()
    
    print("Updating accounts...")
    for account_id, min_tx_time in accounts:
        new_date = get_realistic_creation_date(min_tx_time)
        # Create a static random time for created_at
        rand_time = datetime.time(random.randint(8, 20), random.randint(0, 59), random.randint(0, 59))
        created_at_ts = datetime.datetime.combine(new_date, rand_time)
        
        cursor.execute("""
            UPDATE accounts 
            SET account_created_date = %s, created_at = %s, updated_at = %s
            WHERE account_id = %s
        """, (new_date, created_at_ts, created_at_ts, account_id))
    
    # 2. Update Transactions (location, device, created_at)
    print("Updating transactions...")
    # Map each account to its home_location
    cursor.execute("SELECT account_id, home_location FROM accounts")
    acc_locations = dict(cursor.fetchall())
    
    cursor.execute("SELECT id, sender_account_id, transaction_timestamp FROM transactions")
    transactions = cursor.fetchall()
    
    for tx_id, sender_acc, tx_time in transactions:
        loc = acc_locations.get(sender_acc, "Unknown")
        dev = random.choice(DEVICE_TYPES)
        # created_at for transaction matches its timestamp (when it happened)
        cursor.execute("""
            UPDATE transactions 
            SET location = %s, device_id = %s, created_at = %s
            WHERE id = %s
        """, (loc, dev, tx_time, tx_id))
        
    # 3. Update Behaviour History (created_at)
    print("Updating behaviour history...")
    cursor.execute("SELECT id, behaviour_date FROM behaviour_history")
    histories = cursor.fetchall()
    
    for bh_id, b_date in histories:
        # created_at is end of the behaviour day (e.g. 23:59:59)
        created_at_ts = datetime.datetime.combine(b_date, datetime.time(23, 59, 59))
        cursor.execute("""
            UPDATE behaviour_history 
            SET created_at = %s
            WHERE id = %s
        """, (created_at_ts, bh_id))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Fixed {bank} Database.")

if __name__ == "__main__":
    for bank in BANKS:
        fix_db(bank)
