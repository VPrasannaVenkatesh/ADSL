import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from psycopg2.extras import execute_values

BANKS = ["SBI", "AXIS", "IOB"]

def process_bank(bank):
    print(f"\n--- Processing Behaviour History for {bank} ---")
    conn = get_connection(bank)
    cursor = conn.cursor()

    # Recreate behaviour_history schema
    cursor.execute("DROP TABLE IF EXISTS behaviour_history CASCADE;")
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    with open(schema_path, 'r') as f:
        # Extract only behaviour_history table part or just run the whole schema.sql 
        # Running whole schema.sql is safe since it uses IF NOT EXISTS for other tables
        schema_sql = f.read()
    cursor.execute(schema_sql)
    conn.commit()
    
    # 1. Fetch all accounts
    cursor.execute("SELECT account_id, current_balance FROM accounts")
    accounts = {row[0]: row[1] for row in cursor.fetchall()}

    # 2. Fetch all transactions (We need everything to process chronologically)
    print("Fetching transactions...")
    cursor.execute("""
        SELECT transaction_id, sender_account_id, sender_bank, receiver_account_id, receiver_bank,
               amount, transaction_timestamp, sender_balance_before, sender_balance_after,
               receiver_balance_before, receiver_balance_after, device_type, ip_address, location
        FROM transactions
        ORDER BY transaction_timestamp ASC
    """)
    transactions = cursor.fetchall()

    # Map transactions per account per day
    acc_txs_by_day = defaultdict(lambda: defaultdict(list))
    
    for tx in transactions:
        tx_id, sender, s_bank, receiver, r_bank, amount, ts, s_bb, s_ba, r_bb, r_ba, dev_type, ip, loc = tx
        day_str = ts.date()
        dev = f"{dev_type}-{ip}"
        
        # Sender perspective
        if sender in accounts:
            acc_txs_by_day[sender][day_str].append({
                'id': tx_id, 'is_sender': True, 'amount': amount, 'ts': ts,
                'bb': s_bb, 'ba': s_ba, 'dev': dev, 'loc': loc, 'other_acc': receiver,
                'is_cross': s_bank != r_bank
            })
            
        # Receiver perspective
        if receiver in accounts:
            acc_txs_by_day[receiver][day_str].append({
                'id': tx_id, 'is_sender': False, 'amount': amount, 'ts': ts,
                'bb': r_bb, 'ba': r_ba, 'dev': dev, 'loc': loc, 'other_acc': sender,
                'is_cross': s_bank != r_bank
            })

    # 3. Process Account Profiles
    print("Calculating daily metrics per account...")
    
    history_records = []
    
    for acc_id, days in acc_txs_by_day.items():
        # Historical memory for this account
        seen_recipients = set()
        seen_senders = set()
        seen_devices = set()
        seen_locations = set()
        last_device = None
        last_location = None
        
        # Sort days to ensure chronology
        sorted_days = sorted(days.keys())
        
        for day in sorted_days:
            day_txs = days[day]
            day_txs.sort(key=lambda x: x['ts'])  # Ensure chronological within day
            
            # Basic volume/amounts
            tx_count = len(day_txs)
            sent_txs = [tx for tx in day_txs if tx['is_sender']]
            recv_txs = [tx for tx in day_txs if not tx['is_sender']]
            
            sent_count = len(sent_txs)
            recv_count = len(recv_txs)
            tot_sent = sum(tx['amount'] for tx in sent_txs)
            tot_recv = sum(tx['amount'] for tx in recv_txs)
            all_amounts = [tx['amount'] for tx in day_txs]
            
            avg_amt = sum(all_amounts) // tx_count if tx_count > 0 else 0
            min_amt = min(all_amounts) if all_amounts else 0
            max_amt = max(all_amounts) if all_amounts else 0
            
            # Counterparty tracking
            day_recipients = set(tx['other_acc'] for tx in sent_txs)
            day_senders = set(tx['other_acc'] for tx in recv_txs)
            
            new_recipients = len(day_recipients - seen_recipients)
            new_senders = len(day_senders - seen_senders)
            
            seen_recipients.update(day_recipients)
            seen_senders.update(day_senders)
            
            # Devices & Locations
            day_devices = set(tx['dev'] for tx in day_txs)
            day_locations = set(tx['loc'] for tx in day_txs)
            
            new_devices = len(day_devices - seen_devices)
            new_locations = len(day_locations - seen_locations)
            
            seen_devices.update(day_devices)
            seen_locations.update(day_locations)
            
            dev_changes = 0
            loc_changes = 0
            for tx in day_txs:
                if last_device and tx['dev'] != last_device:
                    dev_changes += 1
                if last_location and tx['loc'] != last_location:
                    loc_changes += 1
                last_device = tx['dev']
                last_location = tx['loc']
                
            # Time & Velocity
            first_time = day_txs[0]['ts'].strftime('%H:%M') if day_txs else None
            last_time = day_txs[-1]['ts'].strftime('%H:%M') if day_txs else None
            hours = [tx['ts'].hour for tx in day_txs]
            active_hrs = len(set(hours))
            night_tx = sum(1 for h in hours if 0 <= h <= 5)
            
            intervals = [(day_txs[i]['ts'] - day_txs[i-1]['ts']).total_seconds() for i in range(1, tx_count)]
            avg_int = int(sum(intervals) / len(intervals)) if intervals else 0
            min_int = int(min(intervals)) if intervals else 0
            
            def make_readable(secs):
                if secs < 60: return f"{secs} seconds"
                return f"{secs // 60} minutes"
                
            avg_int_r = make_readable(avg_int) if tx_count > 1 else "0 seconds"
            min_int_r = make_readable(min_int) if tx_count > 1 else "0 seconds"
            
            # Simple rolling window approximation for 1h, 6h, 24h
            # Max transactions in any 1h/6h window
            max_1h, max_6h, max_24h = 0, 0, tx_count
            for i, start_tx in enumerate(day_txs):
                c_1h, c_6h = 0, 0
                for j in range(i, tx_count):
                    delta = (day_txs[j]['ts'] - start_tx['ts']).total_seconds()
                    if delta <= 3600: c_1h += 1
                    if delta <= 21600: c_6h += 1
                max_1h = max(max_1h, c_1h)
                max_6h = max(max_6h, c_6h)
                
            # Money Flow (Forwarding)
            same_day_fwd = 0
            fwd_amt = 0
            short_dwell = 0
            split_count = 0
            cross_bank = sum(1 for tx in day_txs if tx['is_cross'])
            
            # Very basic forward tracking: find receive, then find subsequent sends
            for i, r_tx in enumerate(recv_txs):
                subs_sends = [s_tx for s_tx in sent_txs if s_tx['ts'] > r_tx['ts']]
                if subs_sends:
                    same_day_fwd += 1
                    s_sum_total = sum(s['amount'] for s in subs_sends)
                    fwd_amt += min(r_tx['amount'], s_sum_total)
                    
                    # Short dwell check (5 mins = 300s)
                    dwell = (subs_sends[0]['ts'] - r_tx['ts']).total_seconds()
                    if dwell <= 300:
                        short_dwell += 1
                    # Amount split check (1 receive -> >=3 sends within 24h that sum to > 80% of received)
                    s_sum = sum(s['amount'] for s in subs_sends[:5]) # just check first 5
                    if len(subs_sends) >= 3 and s_sum >= r_tx['amount'] * 0.8:
                        split_count += 1
                        
            # Balances
            open_b = day_txs[0]['bb']
            close_b = day_txs[-1]['ba']
            bals = [tx['bb'] for tx in day_txs] + [day_txs[-1]['ba']]
            min_b = min(bals)
            max_b = max(bals)
            avg_b = sum(bals) // len(bals)

            history_records.append((
                acc_id, day, tx_count, sent_count, recv_count, tot_sent, tot_recv,
                avg_amt, min_amt, max_amt, len(day_recipients), len(day_senders),
                new_recipients, new_senders, max_1h, max_6h, max_24h,
                avg_int, avg_int_r, min_int, min_int_r, first_time, last_time, active_hrs, night_tx,
                len(day_devices), new_devices, dev_changes,
                len(day_locations), new_locations, loc_changes,
                len(day_senders), len(day_recipients), fwd_amt,
                same_day_fwd, short_dwell, split_count, cross_bank,
                open_b, close_b, min_b, max_b, avg_b
            ))

    print(f"Inserting {len(history_records)} daily profiles...")
    execute_values(cursor, """
        INSERT INTO behaviour_history (
            account_id, behaviour_date, transaction_count, sent_transaction_count, received_transaction_count,
            total_amount_sent, total_amount_received, avg_transaction_amount, min_transaction_amount, max_transaction_amount,
            unique_recipients, unique_senders, new_recipients_count, new_senders_count,
            transactions_1h, transactions_6h, transactions_24h, 
            avg_transaction_interval_seconds, avg_transaction_interval_readable, 
            min_transaction_interval_seconds, min_transaction_interval_readable,
            first_transaction_time, last_transaction_time, active_hours, night_transaction_count,
            unique_device_count, new_device_count, device_change_count,
            unique_location_count, new_location_count, location_change_count,
            fan_in, fan_out, forwarded_amount, same_day_forward_count, short_dwell_count, amount_split_count, cross_bank_transaction_count,
            opening_balance, closing_balance, min_balance, max_balance, avg_balance
        ) VALUES %s
        ON CONFLICT (account_id, behaviour_date) DO NOTHING
    """, history_records)
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Finished generating behaviour history for {bank}")

if __name__ == "__main__":
    for bank in BANKS:
        process_bank(bank)
