import os
import sys
import psycopg2
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]

def run_validation():
    print("============================================================")
    print("DATASET VALIDATION REPORT")
    print("============================================================\n")
    
    all_accounts = {}
    transactions_by_bank = {}
    
    # Load all accounts to validate existence across DBs
    for bank in BANKS:
        try:
            conn = get_connection(bank)
            cursor = conn.cursor()
            cursor.execute("SELECT account_id, home_location FROM accounts")
            for acc, loc in cursor.fetchall():
                all_accounts[acc] = loc
            
            cursor.execute("SELECT COUNT(*) FROM transactions")
            tx_count = cursor.fetchone()[0]
            transactions_by_bank[bank] = tx_count
            print(f"[{bank}] Accounts: {len([a for a in all_accounts if a.startswith(bank)])} | Transactions: {tx_count}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error loading {bank}: {e}")
            
    print("\n--- TRANSACTION INTEGRITY CHECKS ---")
    
    for bank in BANKS:
        print(f"\nEvaluating {bank} Database...")
        invalid_senders = 0
        invalid_receivers = 0
        rx_bank_mismatches = 0
        missing_locations = 0
        invalid_amounts = 0
        self_transfers = 0
        balance_failures = 0
        invalid_types = 0
        invalid_status = 0
        invalid_source = 0
        dup_tx_ids = 0
        
        conn = get_connection(bank)
        cursor = conn.cursor()
        
        # We fetch everything (for 10k/30k rows it fits in memory easily)
        cursor.execute("""
            SELECT id, transaction_id, sender_account_id, receiver_account_id, receiver_bank,
                   amount, transaction_timestamp, transaction_type, 
                   sender_balance_before, sender_balance_after,
                   receiver_balance_before, receiver_balance_after,
                   location, transaction_status, simulation_source
            FROM transactions
            ORDER BY transaction_timestamp ASC
        """)
        
        transactions = cursor.fetchall()
        
        tx_id_set = set()
        
        for tx in transactions:
            (tid, tx_uid, sender, receiver, r_bank, amt, ts, t_type, 
             s_b_b, s_b_a, r_b_b, r_b_a, loc, status, source) = tx
             
            # Duplicate IDs
            if tx_uid in tx_id_set:
                dup_tx_ids += 1
            tx_id_set.add(tx_uid)
            
            # Senders/Receivers
            if sender not in all_accounts:
                invalid_senders += 1
            if receiver not in all_accounts:
                invalid_receivers += 1
                
            # Mismatches
            # If IOB-C0227, bank is IOB. Wait, we assume bank is derived from prefix?
            derived_r_bank = receiver.split('-')[0] if '-' in receiver else None
            if derived_r_bank and r_bank != derived_r_bank:
                rx_bank_mismatches += 1
                
            # Locations
            if not loc or loc.lower() == 'unknown':
                missing_locations += 1
                
            # Amounts
            if amt <= 0:
                invalid_amounts += 1
                
            # Self transfers
            if sender == receiver:
                self_transfers += 1
                
            # Arithmetic (Sender)
            if s_b_b - amt != s_b_a:
                balance_failures += 1
                
            # Types, Status, Source
            if t_type not in ["UPI", "IMPS", "NEFT", "BANK_TRANSFER"]:
                invalid_types += 1
            if status != 'COMPLETED':
                invalid_status += 1
            if source != 'HISTORICAL':
                invalid_source += 1
                
        print(f"  Invalid Senders: {invalid_senders}")
        print(f"  Invalid Receivers: {invalid_receivers}")
        print(f"  Receiver Bank Mismatches: {rx_bank_mismatches}")
        print(f"  Missing/Unknown Locations: {missing_locations}")
        print(f"  Invalid Amounts (<=0): {invalid_amounts}")
        print(f"  Self Transfers: {self_transfers}")
        print(f"  Arithmetic Failures (Sender): {balance_failures}")
        print(f"  Invalid Types/Status/Source: {invalid_types}/{invalid_status}/{invalid_source}")
        print(f"  Duplicate Transaction IDs: {dup_tx_ids}")
        
        # Check Continuity
        print("  Checking Balance Continuity... ", end="")
        cursor.execute("""
            SELECT sender_account_id, transaction_timestamp, sender_balance_before, sender_balance_after
            FROM transactions
            ORDER BY sender_account_id, transaction_timestamp ASC
        """)
        sender_tx = cursor.fetchall()
        
        continuity_fails = 0
        last_acc = None
        last_bal_after = None
        
        for acc, ts, b_b, b_a in sender_tx:
            if acc != last_acc:
                last_acc = acc
                last_bal_after = b_a
            else:
                if b_b != last_bal_after:
                    continuity_fails += 1
                last_bal_after = b_a
                
        print(f"Failures: {continuity_fails}")
        
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_validation()
