import os
import sys
import datetime
import random
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from psycopg2.extras import execute_values

BANKS = ["SBI", "AXIS", "IOB"]

def inject_mules():
    for bank in BANKS:
        print(f"\n--- Injecting Mule Behaviour for {bank} ---")
        conn = get_connection(bank)
        cursor = conn.cursor()
        
        # 1. Get max timestamp and a few normal accounts to act as counterparties
        cursor.execute("SELECT MAX(transaction_timestamp) FROM transactions")
        max_ts = cursor.fetchone()[0] or datetime.datetime.now()
        
        cursor.execute("SELECT account_id FROM accounts LIMIT 50")
        normal_accs = [row[0] for row in cursor.fetchall()]
        
        # 2. Identify 10 existing mules
        cursor.execute("""
            SELECT account_id, current_balance 
            FROM accounts 
            WHERE mod(abs(('x' || substr(md5(account_id), 1, 8))::bit(32)::int), 100) < 5
            LIMIT 10
        """)
        mules = cursor.fetchall()
        
        new_txs = []
        
        for mule_id, balance in mules:
            # We will advance max_ts slightly for each mule event to avoid collisions
            
            # Behavior 1: Short Dwell Forwarding (Receive and send within 2 mins)
            max_ts += datetime.timedelta(hours=1)
            sender = random.choice([acc for acc in normal_accs if acc != mule_id])
            receive_amt = 50000
            
            tx1 = str(uuid.uuid4())
            new_txs.append((
                tx1, sender, bank, mule_id, bank, receive_amt, max_ts, 'UPI',
                0, 0, balance, balance + receive_amt, 'Mobile', '1.1.1.1', 'Delhi', False, 'COMPLETED', 'SYNTHETIC_MULE'
            ))
            
            balance += receive_amt
            
            # Send it out in 2 minutes
            max_ts += datetime.timedelta(minutes=2)
            send_amt = 48000
            receiver = random.choice([acc for acc in normal_accs if acc != mule_id])
            
            tx2 = str(uuid.uuid4())
            new_txs.append((
                tx2, mule_id, bank, receiver, bank, send_amt, max_ts, 'UPI',
                balance, balance - send_amt, 0, 0, 'Mobile', '1.1.1.1', 'Kolkata', False, 'COMPLETED', 'SYNTHETIC_MULE'
            ))
            
            balance -= send_amt
            
            # Behavior 2: Amount Split (Receive large, split to 3+ accounts in 10 mins)
            max_ts += datetime.timedelta(days=1)
            sender = random.choice([acc for acc in normal_accs if acc != mule_id])
            receive_amt = 100000
            
            tx3 = str(uuid.uuid4())
            new_txs.append((
                tx3, sender, bank, mule_id, bank, receive_amt, max_ts, 'UPI',
                0, 0, balance, balance + receive_amt, 'Mobile', '1.1.1.1', 'Delhi', False, 'COMPLETED', 'SYNTHETIC_MULE'
            ))
            balance += receive_amt
            
            # Split into 3
            split_amt = 30000
            for i in range(3):
                max_ts += datetime.timedelta(minutes=3)
                receiver = random.choice([acc for acc in normal_accs if acc != mule_id])
                tx_split = str(uuid.uuid4())
                new_txs.append((
                    tx_split, mule_id, bank, receiver, bank, split_amt, max_ts, 'UPI',
                    balance, balance - split_amt, 0, 0, 'Mobile', '1.1.1.1', 'Kolkata', False, 'COMPLETED', 'SYNTHETIC_MULE'
                ))
                balance -= split_amt
                
            # Update mule balance
            cursor.execute("UPDATE accounts SET current_balance = %s WHERE account_id = %s", (balance, mule_id))
            
        print(f"Injecting {len(new_txs)} targeted mule transactions...")
        execute_values(cursor, """
            INSERT INTO transactions (
                transaction_id, sender_account_id, sender_bank, receiver_account_id, receiver_bank,
                amount, transaction_timestamp, transaction_type,
                sender_balance_before, sender_balance_after, receiver_balance_before, receiver_balance_after,
                device_type, ip_address, location, recipient_is_new, transaction_status, simulation_source
            ) VALUES %s
        """, new_txs)
        
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    inject_mules()
