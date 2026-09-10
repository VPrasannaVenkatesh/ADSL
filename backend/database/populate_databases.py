import random
import datetime
import uuid
from collections import defaultdict
from psycopg2.extras import execute_values
from db_connection import get_connection

BANKS = ["SBI", "AXIS", "IOB"]
ACCOUNT_TYPES = ["SAVINGS", "CURRENT"]
TX_TYPES = ["UPI", "IMPS", "NEFT", "BANK_TRANSFER"]
DEVICE_TYPES = ["Mobile", "Desktop", "Laptop", "Tablet"]

NAMES = [
    "Arjun Kumar", "Prasanna Venkatesh", "Karthik Reddy", "Sandeep Nair",
    "Ananya Iyer", "Divya Krishnan", "Aarav Sharma", "Rohan Singh",
    "Aditya Verma", "Priya Gupta", "Neha Kapoor", "Ananya Banerjee",
    "Vikram Patel", "Sneha Desai", "Rahul Chatterjee", "Pooja Joshi",
    "Rajesh Khanna", "Amitabh Bachchan", "Shahrukh Khan", "Salman Khan",
    "Akshay Kumar", "Ajay Devgn", "Hrithik Roshan", "Ranbir Kapoor",
    "Ranveer Singh", "Varun Dhawan", "Tiger Shroff", "Ayushmann Khurrana",
    "Rajkummar Rao", "Vicky Kaushal", "Kartik Aaryan", "Sushant Singh Rajput",
    "R. Madhavan", "Suriya", "Vijay", "Ajith Kumar", "Dhanush", "Karthi"
]

LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur",
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]


def secs_to_readable(secs):
    if secs <= 0:
        return "0s"
    elif secs < 60:
        return f"{secs}s"
    elif secs < 3600:
        return f"{secs // 60}m {secs % 60}s"
    else:
        return f"{secs // 3600}h {(secs % 3600) // 60}m"


def generate_accounts():
    accounts_data = {bank: [] for bank in BANKS}
    for bank in BANKS:
        for i in range(1, 501):
            account_id = f"{bank}-{chr(65 + BANKS.index(bank))}{i:04d}"
            account_number = str(random.randint(1000000000, 9999999999))

            first_names = [n.split()[0] for n in NAMES]
            last_names = [n.split()[-1] for n in NAMES if len(n.split()) > 1]
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"

            prefix = random.choice(['6', '7', '8', '9'])
            phone_number = prefix + "".join([str(random.randint(0, 9)) for _ in range(9)])

            acc_type = random.choice(ACCOUNT_TYPES)
            initial_balance = random.randint(1000, 1000000)

            # Account creation date guaranteed to be earlier than transaction start (at least 200 to 1825 days ago)
            days_ago = random.randint(210, 1825)
            created_date = datetime.date.today() - datetime.timedelta(days=days_ago)

            accounts_data[bank].append({
                "account_id": account_id,
                "account_number": account_number,
                "customer_name": customer_name,
                "phone_number": phone_number,
                "account_type": acc_type,
                "current_balance": initial_balance,
                "account_created_date": created_date,
                "home_location": random.choice(LOCATIONS),
                "bank": bank
            })
    return accounts_data


def generate_transactions(accounts_data, total_tx=10000, days_history=180):
    all_accounts = []
    account_balances = {}

    for bank, accs in accounts_data.items():
        for acc in accs:
            all_accounts.append(acc)
            account_balances[acc["account_id"]] = acc["current_balance"]

    transactions_by_bank = {bank: [] for bank in BANKS}

    start_time = datetime.datetime.now() - datetime.timedelta(days=days_history)
    current_time = start_time

    for _ in range(total_tx):
        step_seconds = random.randint(1, 300) if random.random() > 0.1 else random.randint(300, 3600)
        current_time += datetime.timedelta(seconds=step_seconds)

        device_type = random.choice(DEVICE_TYPES)
        ip = f"{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
        # Combined column: "Mobile:192.168.1.1"
        device_ip = f"{device_type}:{ip}"

        sender = random.choice(all_accounts)

        is_burst = random.random() < 0.05
        burst_count = random.randint(3, 8) if is_burst else 1

        for _ in range(burst_count):
            receiver = random.choice(all_accounts)
            while receiver["account_id"] == sender["account_id"]:
                receiver = random.choice(all_accounts)

            amount = random.randint(100, 50000)

            if account_balances[sender["account_id"]] < amount:
                continue

            sender_bal_before = account_balances[sender["account_id"]]
            sender_bal_after = sender_bal_before - amount
            account_balances[sender["account_id"]] = sender_bal_after

            receiver_bal_before = account_balances[receiver["account_id"]]
            receiver_bal_after = receiver_bal_before + amount
            account_balances[receiver["account_id"]] = receiver_bal_after

            tx_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
            location = random.choice(LOCATIONS)
            recipient_is_new = random.choice([True, False])

            # Tuple indices:
            # 0:tx_id, 1:sender_id, 2:sender_bank, 3:receiver_id, 4:receiver_bank,
            # 5:amount, 6:ts, 7:tx_type,
            # 8:sender_bal_before, 9:sender_bal_after, 10:receiver_bal_before, 11:receiver_bal_after,
            # 12:device_ip, 13:location, 14:recipient_is_new, 15:status, 16:source
            tx_tuple = (
                tx_id, sender["account_id"], sender["bank"],
                receiver["account_id"], receiver["bank"],
                amount, current_time, random.choice(TX_TYPES),
                sender_bal_before, sender_bal_after, receiver_bal_before, receiver_bal_after,
                device_ip, location, recipient_is_new, 'COMPLETED', 'HISTORICAL'
            )

            transactions_by_bank[sender["bank"]].append(tx_tuple)

            if sender["bank"] != receiver["bank"]:
                transactions_by_bank[receiver["bank"]].append(tx_tuple)

            if is_burst:
                current_time += datetime.timedelta(seconds=random.randint(1, 10))

    for bank in BANKS:
        for acc in accounts_data[bank]:
            acc["current_balance"] = account_balances[acc["account_id"]]

    return accounts_data, transactions_by_bank


def compute_behaviour_history(transactions_by_bank):
    """
    Compute per-account per-day behaviour metrics from in-memory transactions.
    Returns a dict: {bank: [tuple, ...]} ready to INSERT into behaviour_history.
    """
    behaviour_by_bank = {bank: [] for bank in BANKS}

    for bank in BANKS:
        # Group transactions by (account_id, date)
        daily = defaultdict(lambda: {"sent": [], "recv": []})

        for txn in transactions_by_bank[bank]:
            tx_id      = txn[0]
            sender_id  = txn[1]
            sender_bank= txn[2]
            receiver_id= txn[3]
            receiver_bank = txn[4]
            amount     = txn[5]
            ts         = txn[6]
            s_bb, s_ba = txn[8], txn[9]
            r_bb, r_ba = txn[10], txn[11]
            device_ip  = txn[12]
            location   = txn[13]
            recip_new  = txn[14]

            date = ts.date()

            if sender_bank == bank:
                daily[(sender_id, date)]["sent"].append({
                    "tx_id": tx_id, "amount": amount, "ts": ts,
                    "peer_id": receiver_id, "peer_bank": receiver_bank,
                    "device_ip": device_ip, "location": location,
                    "recipient_is_new": recip_new,
                    "bal_before": s_bb, "bal_after": s_ba
                })

            if receiver_bank == bank:
                daily[(receiver_id, date)]["recv"].append({
                    "tx_id": tx_id, "amount": amount, "ts": ts,
                    "peer_id": sender_id, "peer_bank": sender_bank,
                    "device_ip": device_ip, "location": location,
                    "recipient_is_new": False,
                    "bal_before": r_bb, "bal_after": r_ba
                })

        # Track historically seen devices / locations / peers per account
        seen_devices    = defaultdict(set)
        seen_locations  = defaultdict(set)
        seen_recipients = defaultdict(set)
        seen_senders    = defaultdict(set)

        # Process in chronological order so "new" tracking is accurate
        for (account_id, date) in sorted(daily.keys(), key=lambda k: k[1]):
            s = daily[(account_id, date)]["sent"]
            r = daily[(account_id, date)]["recv"]

            all_txns = s + r
            all_ts_sorted = sorted(t["ts"] for t in all_txns)

            # --- Volume ---
            tx_count   = len(all_txns)
            sent_count = len(s)
            recv_count = len(r)

            # --- Amounts ---
            all_amounts = [t["amount"] for t in all_txns]
            total_sent  = sum(t["amount"] for t in s)
            total_recv  = sum(t["amount"] for t in r)
            avg_amt = sum(all_amounts) // len(all_amounts) if all_amounts else 0
            min_amt = min(all_amounts) if all_amounts else 0
            max_amt = max(all_amounts) if all_amounts else 0

            # --- Counterparty ---
            recipients    = [t["peer_id"] for t in s]
            senders_list  = [t["peer_id"] for t in r]
            unique_recipients  = len(set(recipients))
            unique_senders_cnt = len(set(senders_list))
            new_recipients_cnt = sum(1 for t in s if t["recipient_is_new"])
            new_senders_cnt    = len(set(senders_list) - seen_senders[account_id])

            # --- Velocity ---
            end_of_day = datetime.datetime.combine(date, datetime.time(23, 59, 59))
            txns_1h  = sum(1 for t in all_txns if (end_of_day - t["ts"]).total_seconds() <= 3600)
            txns_6h  = sum(1 for t in all_txns if (end_of_day - t["ts"]).total_seconds() <= 21600)
            txns_24h = tx_count

            # --- Intervals ---
            intervals = [
                int((all_ts_sorted[i] - all_ts_sorted[i - 1]).total_seconds())
                for i in range(1, len(all_ts_sorted))
                if (all_ts_sorted[i] - all_ts_sorted[i - 1]).total_seconds() > 0
            ]
            avg_interval = sum(intervals) // len(intervals) if intervals else 0
            min_interval = min(intervals) if intervals else 0

            # --- Time behaviour ---
            first_tx_time = all_ts_sorted[0].strftime('%H:%M:%S') if all_ts_sorted else None
            last_tx_time  = all_ts_sorted[-1].strftime('%H:%M:%S') if all_ts_sorted else None
            active_hours  = len(set(t.hour for t in all_ts_sorted))
            night_count   = sum(1 for t in all_ts_sorted if t.hour < 6 or t.hour >= 22)

            # --- Device behaviour ---
            all_device_types = [t["device_ip"].split(":")[0] for t in all_txns if t.get("device_ip")]
            unique_devs = set(all_device_types)
            new_devs    = unique_devs - seen_devices[account_id]
            dev_changes = sum(
                1 for i in range(1, len(all_device_types))
                if all_device_types[i] != all_device_types[i - 1]
            )
            primary_device = (
                max(set(all_device_types), key=all_device_types.count)
                if all_device_types else None
            )
            seen_devices[account_id].update(unique_devs)

            # --- Location behaviour ---
            all_locs   = [t["location"] for t in all_txns]
            unique_locs = set(all_locs)
            new_locs    = unique_locs - seen_locations[account_id]
            loc_changes = sum(
                1 for i in range(1, len(all_locs))
                if all_locs[i] != all_locs[i - 1]
            )
            seen_locations[account_id].update(unique_locs)

            # Update peer tracking
            seen_recipients[account_id].update(set(recipients))
            seen_senders[account_id].update(set(senders_list))

            # --- Mule / money-flow indicators ---
            fan_in  = unique_senders_cnt
            fan_out = unique_recipients

            recv_amt_set   = set(t["amount"] for t in r)
            forwarded_amt  = sum(t["amount"] for t in s if t["amount"] in recv_amt_set)
            same_day_fwd   = sum(1 for t in s if t["amount"] in recv_amt_set)

            # Short dwell: money received then sent within 1 hour
            short_dwell = 0
            for rt in r:
                for st in s:
                    delta = (st["ts"] - rt["ts"]).total_seconds()
                    if 0 < delta <= 3600:
                        short_dwell += 1
                        break

            # Amount split: one incoming split into multiple smaller outgoing
            amount_split = sum(
                1 for rt in r
                if len([st for st in s if st["amount"] < rt["amount"]]) > 1
            )

            cross_bank = (
                sum(1 for t in s if t["peer_bank"] != bank) +
                sum(1 for t in r if t["peer_bank"] != bank)
            )

            # --- Balance behaviour ---
            all_bal_events = sorted(
                [(t["ts"], t["bal_before"], t["bal_after"]) for t in all_txns],
                key=lambda x: x[0]
            )
            opening_bal = all_bal_events[0][1]  if all_bal_events else 0
            closing_bal = all_bal_events[-1][2] if all_bal_events else 0
            flat_bals   = [b for _, bb, ba in all_bal_events for b in (bb, ba)]
            min_bal = min(flat_bals) if flat_bals else 0
            max_bal = max(flat_bals) if flat_bals else 0
            avg_bal = sum(flat_bals) // len(flat_bals) if flat_bals else 0

            behaviour_by_bank[bank].append((
                account_id, date,
                tx_count, sent_count, recv_count,
                total_sent, total_recv, avg_amt, min_amt, max_amt,
                unique_recipients, unique_senders_cnt, new_recipients_cnt, new_senders_cnt,
                txns_1h, txns_6h, txns_24h,
                avg_interval, secs_to_readable(avg_interval),
                min_interval, secs_to_readable(min_interval),
                first_tx_time, last_tx_time, active_hours, night_count,
                len(unique_devs), len(new_devs), dev_changes, primary_device,
                len(unique_locs), len(new_locs), loc_changes,
                fan_in, fan_out, forwarded_amt, same_day_fwd, short_dwell, amount_split, cross_bank,
                opening_bal, closing_bal, min_bal, max_bal, avg_bal,
            ))

    return behaviour_by_bank


def insert_data():
    print("Generating accounts...")
    accounts_data = generate_accounts()

    print("Generating 10,000 transactions...")
    accounts_data, transactions_by_bank = generate_transactions(accounts_data, total_tx=10000)

    print("Computing behaviour history from transactions...")
    behaviour_by_bank = compute_behaviour_history(transactions_by_bank)

    for bank in BANKS:
        print(f"\nInserting data into {bank}...")
        conn = get_connection(bank)
        cursor = conn.cursor()

        # ── Accounts ──────────────────────────────────────────────────────────
        acc_tuples = [
            (
                a["account_id"], a["account_number"], a["customer_name"],
                a["phone_number"], a["account_type"], a["current_balance"],
                a["account_created_date"], a["home_location"]
            )
            for a in accounts_data[bank]
        ]
        execute_values(cursor, """
            INSERT INTO accounts (
                account_id, account_number, customer_name, phone_number,
                account_type, current_balance, account_created_date, home_location
            ) VALUES %s
        """, acc_tuples)
        print(f"  [{bank}] Inserted {len(acc_tuples)} accounts")

        # ── Transactions ──────────────────────────────────────────────────────
        execute_values(cursor, """
            INSERT INTO transactions (
                transaction_id, sender_account_id, sender_bank,
                receiver_account_id, receiver_bank,
                amount, transaction_timestamp, transaction_type,
                sender_balance_before, sender_balance_after,
                receiver_balance_before, receiver_balance_after,
                device_ip, location, recipient_is_new,
                transaction_status, simulation_source
            ) VALUES %s
        """, transactions_by_bank[bank])
        print(f"  [{bank}] Inserted {len(transactions_by_bank[bank])} transactions")

        # ── Behaviour History (computed) ──────────────────────────────────────
        if behaviour_by_bank[bank]:
            execute_values(cursor, """
                INSERT INTO behaviour_history (
                    account_id, behaviour_date,
                    transaction_count, sent_transaction_count, received_transaction_count,
                    total_amount_sent, total_amount_received,
                    avg_transaction_amount, min_transaction_amount, max_transaction_amount,
                    unique_recipients, unique_senders, new_recipients_count, new_senders_count,
                    transactions_1h, transactions_6h, transactions_24h,
                    avg_transaction_interval_seconds, avg_transaction_interval_readable,
                    min_transaction_interval_seconds, min_transaction_interval_readable,
                    first_transaction_time, last_transaction_time,
                    active_hours, night_transaction_count,
                    unique_device_count, new_device_count, device_change_count, primary_device,
                    unique_location_count, new_location_count, location_change_count,
                    fan_in, fan_out, forwarded_amount, same_day_forward_count,
                    short_dwell_count, amount_split_count, cross_bank_transaction_count,
                    opening_balance, closing_balance, min_balance, max_balance, avg_balance
                ) VALUES %s
                ON CONFLICT (account_id, behaviour_date) DO NOTHING
            """, behaviour_by_bank[bank])
            print(f"  [{bank}] Inserted {len(behaviour_by_bank[bank])} behaviour records")

        # ── Blank profiles for accounts with zero transactions ─────────────
        cursor.execute("""
            INSERT INTO behaviour_history (account_id, behaviour_date)
            SELECT account_id, CURRENT_DATE FROM accounts a
            WHERE NOT EXISTS (
                SELECT 1 FROM behaviour_history b WHERE b.account_id = a.account_id
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"  [{bank}] Done!")

    print("\nAll databases populated successfully!")


if __name__ == "__main__":
    insert_data()
