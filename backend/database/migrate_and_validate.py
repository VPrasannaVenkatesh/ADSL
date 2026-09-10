#!/usr/bin/env python3
"""
migrate_and_validate.py
════════════════════════════════════════════════════════════════════════════════
Validates and migrates  sbi_db / axis_db / iob_db  to be fully ready for the
bank-level behavioural risk scoring engine.

All operations are IDEMPOTENT — safe to run multiple times.
No existing valid data is deleted or overwritten arbitrarily.

Steps
─────
  1. Schema guard   – verify every required column exists; add any missing ones;
                      remove legacy split columns (device_type / ip_address).
  2. Date fix       – ensure account_created_date < first-transaction date for
                      every account.  Only violating rows are touched.
  3. Indices        – create composite indices for the risk engine's hot queries
                      (account + timestamp lookups, behaviour-history lookups).
  4. Timestamp check– report timestamp coverage; flag any NULL timestamps.
  5. Behaviour fix  – recompute any behaviour_history rows that still show
                      transaction_count=0 despite having real transactions on
                      that date (handles any edge-cases from previous runs).
  6. Summary report – print final counts and validation status per bank.
"""

import os
import sys
import random
from datetime import date, timedelta, datetime
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv

# ── env ───────────────────────────────────────────────────────────────────────
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

BANKS = ['SBI', 'AXIS', 'IOB']
DB_URLS = {
    'SBI':  os.environ.get('SBI_DATABASE_URL'),
    'AXIS': os.environ.get('AXIS_DATABASE_URL'),
    'IOB':  os.environ.get('IOB_DATABASE_URL'),
}


def get_conn(bank: str) -> psycopg2.extensions.connection:
    url = DB_URLS[bank]
    if not url:
        raise ValueError(f"Environment variable {bank}_DATABASE_URL is not set.")
    return psycopg2.connect(url)


def secs_to_readable(secs: int) -> str:
    if secs <= 0:    return "0s"
    if secs < 60:    return f"{secs}s"
    if secs < 3600:  return f"{secs // 60}m {secs % 60}s"
    return f"{secs // 3600}h {(secs % 3600) // 60}m"


# ════════════════════════════════════════════════════════════════════════════════
# Step 1 – Schema guard
# ════════════════════════════════════════════════════════════════════════════════

def step1_verify_schema(conn, cur, bank: str):
    print("  [1/6] Schema verification …")

    def cols(table: str) -> set:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s",
            (table,)
        )
        return {r[0] for r in cur.fetchall()}

    txn_cols = cols('transactions')
    acc_cols = cols('accounts')
    bh_cols  = cols('behaviour_history')
    changes  = []

    # transactions ────────────────────────────────────────────────────────────
    if 'transaction_timestamp' not in txn_cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN transaction_timestamp TIMESTAMP")
        changes.append("ADD  transactions.transaction_timestamp")

    if 'device_ip' not in txn_cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN device_ip VARCHAR")
        changes.append("ADD  transactions.device_ip")

    # remove legacy split columns if they were re-introduced
    for old in ('device_type', 'ip_address'):
        if old in txn_cols:
            cur.execute(f"ALTER TABLE transactions DROP COLUMN {old}")
            changes.append(f"DROP transactions.{old}")

    # accounts ────────────────────────────────────────────────────────────────
    if 'account_created_date' not in acc_cols:
        cur.execute("ALTER TABLE accounts ADD COLUMN account_created_date DATE")
        changes.append("ADD  accounts.account_created_date")

    # behaviour_history ───────────────────────────────────────────────────────
    if 'primary_device' not in bh_cols:
        cur.execute("ALTER TABLE behaviour_history ADD COLUMN primary_device VARCHAR")
        changes.append("ADD  behaviour_history.primary_device")

    conn.commit()

    if changes:
        for c in changes:
            print(f"      PATCHED  {c}")
    else:
        print("      OK — schema is complete, no changes needed")


# ════════════════════════════════════════════════════════════════════════════════
# Step 2 – Fix account_created_date
# ════════════════════════════════════════════════════════════════════════════════

def step2_fix_account_dates(conn, cur, bank: str):
    print("  [2/6] Validating account_created_date …")

    # Find accounts where created_date IS NULL or >= their first transaction date
    cur.execute("""
        SELECT  a.account_id,
                a.account_created_date,
                MIN(t.transaction_timestamp)::date  AS first_tx_date
        FROM    accounts a
        JOIN    transactions t
                ON  t.sender_account_id   = a.account_id
                OR  t.receiver_account_id = a.account_id
        GROUP   BY a.account_id, a.account_created_date
        HAVING  a.account_created_date IS NULL
            OR  a.account_created_date >= MIN(t.transaction_timestamp)::date
        ORDER   BY a.account_id
    """)
    violations = cur.fetchall()

    if violations:
        print(f"      FIXING   {len(violations)} account(s) with invalid created_date …")
        for account_id, _old_date, first_tx_date in violations:
            # Assign a date 30–730 days before the account's first transaction
            days_before = random.randint(30, 730)
            new_date = first_tx_date - timedelta(days=days_before)
            cur.execute(
                "UPDATE accounts SET account_created_date = %s WHERE account_id = %s",
                (new_date, account_id)
            )
        conn.commit()
        print(f"      FIXED    {len(violations)} account(s)")
    else:
        print("      OK — all account creation dates precede their first transaction")

    # Accounts with no transactions and still NULL created_date
    cur.execute("""
        UPDATE accounts
        SET    account_created_date =
               (CURRENT_DATE - (random() * 1825)::int * INTERVAL '1 day')::date
        WHERE  account_created_date IS NULL
    """)
    affected = cur.rowcount
    if affected:
        print(f"      SEEDED   {affected} account(s) with no transactions given random dates")
    conn.commit()


# ════════════════════════════════════════════════════════════════════════════════
# Step 3 – Risk-engine indices
# ════════════════════════════════════════════════════════════════════════════════

def step3_ensure_indices(conn, cur, bank: str):
    print("  [3/6] Creating risk-engine indices …")

    indices = [
        # Hot paths for "get last N transactions for account X" (live risk scoring)
        ("idx_txn_sender_ts",
         "transactions(sender_account_id,   transaction_timestamp DESC)"),
        ("idx_txn_receiver_ts",
         "transactions(receiver_account_id, transaction_timestamp DESC)"),
        # Timestamp range scans (velocity windows, chronological network analysis)
        ("idx_txn_timestamp",
         "transactions(transaction_timestamp)"),
        # Behaviour-history lookup: latest N days for an account
        ("idx_bh_account_date",
         "behaviour_history(account_id, behaviour_date DESC)"),
        # Account age calculation (account_created_date used at query time)
        ("idx_acc_id",
         "accounts(account_id)"),
        ("idx_acc_created",
         "accounts(account_id, account_created_date)"),
    ]

    for name, definition in indices:
        cur.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {definition}")
        print(f"      IDX      {name}")

    conn.commit()


# ════════════════════════════════════════════════════════════════════════════════
# Step 4 – Timestamp validation report
# ════════════════════════════════════════════════════════════════════════════════

def step4_validate_timestamps(cur, bank: str):
    print("  [4/6] Validating transaction timestamps …")

    cur.execute("""
        SELECT  COUNT(*)                                              AS total,
                COUNT(*) FILTER (WHERE transaction_timestamp IS NULL) AS nulls,
                MIN(transaction_timestamp)                            AS earliest,
                MAX(transaction_timestamp)                            AS latest,
                COUNT(DISTINCT transaction_timestamp::date)           AS distinct_days
        FROM    transactions
    """)
    total, nulls, earliest, latest, distinct_days = cur.fetchone()

    print(f"      TOTAL    {total:,} transactions  |  {distinct_days} distinct calendar days")
    print(f"      RANGE    {earliest}  →  {latest}")
    if nulls:
        print(f"      WARN     {nulls} transaction(s) have NULL timestamp!")
    else:
        print("      OK — no NULL timestamps")

    # Chronological order check per sender account (sample 5 accounts)
    cur.execute("""
        SELECT sender_account_id
        FROM   transactions
        GROUP  BY sender_account_id
        HAVING COUNT(*) >= 3
        ORDER  BY random()
        LIMIT  5
    """)
    sample_accounts = [r[0] for r in cur.fetchall()]

    order_ok = True
    for acct in sample_accounts:
        cur.execute("""
            SELECT transaction_timestamp
            FROM   transactions
            WHERE  sender_account_id = %s
            ORDER  BY id
        """, (acct,))
        timestamps = [r[0] for r in cur.fetchall()]
        if timestamps != sorted(timestamps):
            print(f"      WARN     {acct}: transactions not in chronological order by id!")
            order_ok = False

    if order_ok:
        print("      OK — sampled accounts have chronological transaction order")


# ════════════════════════════════════════════════════════════════════════════════
# Step 5 – Recompute any stale zero-metric behaviour_history rows
# ════════════════════════════════════════════════════════════════════════════════

def step5_recompute_zero_behaviour(conn, cur, bank: str):
    print("  [5/6] Checking for stale zero-metric behaviour_history rows …")

    cur.execute("""
        SELECT  bh.id, bh.account_id, bh.behaviour_date
        FROM    behaviour_history bh
        WHERE   bh.transaction_count = 0
          AND   EXISTS (
                    SELECT 1 FROM transactions t
                    WHERE  t.transaction_timestamp::date = bh.behaviour_date
                      AND (t.sender_account_id   = bh.account_id
                           OR t.receiver_account_id = bh.account_id)
                )
        ORDER   BY bh.account_id, bh.behaviour_date
    """)
    stale = cur.fetchall()

    if not stale:
        print("      OK — no stale zero-metric rows found")
        return

    print(f"      FIXING   {len(stale)} stale row(s) …")

    for record_id, account_id, behaviour_date in stale:
        _recompute_one_row(conn, cur, bank, record_id, account_id, behaviour_date)

    conn.commit()
    print(f"      FIXED    {len(stale)} row(s) recomputed from real transactions")


def _recompute_one_row(conn, cur, bank, record_id, account_id, behaviour_date):
    """Pull transactions for (account_id, behaviour_date) and UPDATE the row."""
    cur.execute("""
        SELECT
            sender_account_id,  sender_bank,
            receiver_account_id, receiver_bank,
            amount,             transaction_timestamp,
            sender_balance_before,   sender_balance_after,
            receiver_balance_before, receiver_balance_after,
            device_ip,          location,   recipient_is_new
        FROM   transactions
        WHERE  transaction_timestamp::date = %s
          AND (sender_account_id = %s OR receiver_account_id = %s)
        ORDER  BY transaction_timestamp
    """, (behaviour_date, account_id, account_id))
    rows = cur.fetchall()

    sent = [r for r in rows if r[0] == account_id]
    recv = [r for r in rows if r[2] == account_id]
    all_ts = sorted(r[5] for r in rows)

    tx_count   = len(rows)
    sent_count = len(sent)
    recv_count = len(recv)

    all_amounts = [r[4] for r in rows]
    total_sent  = sum(r[4] for r in sent)
    total_recv  = sum(r[4] for r in recv)
    avg_amt     = sum(all_amounts) // len(all_amounts) if all_amounts else 0
    min_amt     = min(all_amounts) if all_amounts else 0
    max_amt     = max(all_amounts) if all_amounts else 0

    unique_recipients  = len(set(r[2] for r in sent))
    unique_senders_cnt = len(set(r[0] for r in recv))
    new_recip_cnt      = sum(1 for r in sent if r[12])

    end_of_day = datetime.combine(behaviour_date, datetime.max.time())
    txns_1h  = sum(1 for r in rows if (end_of_day - r[5]).total_seconds() <= 3_600)
    txns_6h  = sum(1 for r in rows if (end_of_day - r[5]).total_seconds() <= 21_600)

    intervals = [
        int((all_ts[i] - all_ts[i - 1]).total_seconds())
        for i in range(1, len(all_ts))
        if (all_ts[i] - all_ts[i - 1]).total_seconds() > 0
    ]
    avg_interval = sum(intervals) // len(intervals) if intervals else 0
    min_interval = min(intervals) if intervals else 0

    first_tx_time = all_ts[0].strftime('%H:%M:%S') if all_ts else None
    last_tx_time  = all_ts[-1].strftime('%H:%M:%S') if all_ts else None
    active_hours  = len(set(t.hour for t in all_ts))
    night_count   = sum(1 for t in all_ts if t.hour < 6 or t.hour >= 22)

    device_types  = [r[10].split(':')[0] for r in rows if r[10]]
    unique_devs   = set(device_types)
    dev_changes   = sum(
        1 for i in range(1, len(device_types))
        if device_types[i] != device_types[i - 1]
    )
    primary_dev   = max(set(device_types), key=device_types.count) if device_types else None

    all_locs      = [r[11] for r in rows if r[11]]
    unique_locs   = set(all_locs)
    loc_changes   = sum(
        1 for i in range(1, len(all_locs))
        if all_locs[i] != all_locs[i - 1]
    )

    cross_bank = (
        sum(1 for r in sent if r[3] != bank) +
        sum(1 for r in recv if r[1] != bank)
    )
    fan_in  = unique_senders_cnt
    fan_out = unique_recipients

    recv_amt_set  = set(r[4] for r in recv)
    forwarded_amt = sum(r[4] for r in sent if r[4] in recv_amt_set)
    same_day_fwd  = sum(1 for r in sent if r[4] in recv_amt_set)
    short_dwell   = sum(
        1 for rt in recv
        if any(0 < (st[5] - rt[5]).total_seconds() <= 3600 for st in sent)
    )
    amount_split  = sum(
        1 for rt in recv
        if len([st for st in sent if st[4] < rt[4]]) > 1
    )

    # Balance timeline (chronological)
    bal_events = sorted(
        [(r[5], r[6], r[7]) for r in sent] +
        [(r[5], r[8], r[9]) for r in recv],
        key=lambda x: x[0]
    )
    opening_bal = bal_events[0][1]  if bal_events else 0
    closing_bal = bal_events[-1][2] if bal_events else 0
    flat_bals   = [b for _, bb, ba in bal_events for b in (bb, ba) if bb and ba]
    min_bal     = min(flat_bals) if flat_bals else 0
    max_bal     = max(flat_bals) if flat_bals else 0
    avg_bal     = sum(flat_bals) // len(flat_bals) if flat_bals else 0

    cur.execute("""
        UPDATE behaviour_history SET
            transaction_count                = %s,
            sent_transaction_count           = %s,
            received_transaction_count       = %s,
            total_amount_sent                = %s,
            total_amount_received            = %s,
            avg_transaction_amount           = %s,
            min_transaction_amount           = %s,
            max_transaction_amount           = %s,
            unique_recipients                = %s,
            unique_senders                   = %s,
            new_recipients_count             = %s,
            transactions_1h                  = %s,
            transactions_6h                  = %s,
            transactions_24h                 = %s,
            avg_transaction_interval_seconds = %s,
            avg_transaction_interval_readable= %s,
            min_transaction_interval_seconds = %s,
            min_transaction_interval_readable= %s,
            first_transaction_time           = %s,
            last_transaction_time            = %s,
            active_hours                     = %s,
            night_transaction_count          = %s,
            unique_device_count              = %s,
            device_change_count              = %s,
            primary_device                   = %s,
            unique_location_count            = %s,
            location_change_count            = %s,
            fan_in                           = %s,
            fan_out                          = %s,
            forwarded_amount                 = %s,
            same_day_forward_count           = %s,
            short_dwell_count                = %s,
            amount_split_count               = %s,
            cross_bank_transaction_count     = %s,
            opening_balance                  = %s,
            closing_balance                  = %s,
            min_balance                      = %s,
            max_balance                      = %s,
            avg_balance                      = %s
        WHERE id = %s
    """, (
        tx_count, sent_count, recv_count,
        total_sent, total_recv, avg_amt, min_amt, max_amt,
        unique_recipients, unique_senders_cnt, new_recip_cnt,
        txns_1h, txns_6h, tx_count,
        avg_interval, secs_to_readable(avg_interval),
        min_interval, secs_to_readable(min_interval),
        first_tx_time, last_tx_time, active_hours, night_count,
        len(unique_devs), dev_changes, primary_dev,
        len(unique_locs), loc_changes,
        fan_in, fan_out, forwarded_amt, same_day_fwd, short_dwell, amount_split, cross_bank,
        opening_bal, closing_bal, min_bal, max_bal, avg_bal,
        record_id,
    ))


# ════════════════════════════════════════════════════════════════════════════════
# Step 6 – Final summary report
# ════════════════════════════════════════════════════════════════════════════════

def step6_summary(cur, bank: str):
    print("  [6/6] Summary …")

    cur.execute("SELECT COUNT(*) FROM accounts")
    total_accs = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM accounts
        WHERE account_created_date IS NOT NULL
    """)
    accs_with_date = cur.fetchone()[0]

    cur.execute("""
        SELECT  COUNT(*),
                MIN(transaction_timestamp),
                MAX(transaction_timestamp),
                COUNT(DISTINCT transaction_timestamp::date)
        FROM    transactions
    """)
    total_txns, ts_min, ts_max, distinct_days = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) FROM transactions WHERE transaction_timestamp IS NOT NULL
    """)
    txns_with_ts = cur.fetchone()[0]

    cur.execute("""
        SELECT  COUNT(*) FILTER (WHERE transaction_count > 0)  AS real_rows,
                COUNT(*) FILTER (WHERE transaction_count = 0)  AS zero_rows
        FROM    behaviour_history
    """)
    bh_real, bh_zero = cur.fetchone()

    # Date-integrity check (should be 0 after our fix)
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT a.account_id
            FROM   accounts a
            JOIN   transactions t
                   ON  t.sender_account_id   = a.account_id
                   OR  t.receiver_account_id = a.account_id
            GROUP  BY a.account_id, a.account_created_date
            HAVING a.account_created_date IS NULL
                OR a.account_created_date >= MIN(t.transaction_timestamp)::date
        ) sub
    """)
    remaining_violations = cur.fetchone()[0]

    print(f"      accounts            : {total_accs:>6,}  "
          f"({accs_with_date:,} with account_created_date)")
    print(f"      transactions        : {total_txns:>6,}  "
          f"({txns_with_ts:,} with timestamp  |  {distinct_days} days covered)")
    print(f"      timestamp range     : {ts_min}  →  {ts_max}")
    print(f"      behaviour_history   : {bh_real:>6,} real rows  +  {bh_zero:,} zero-profile rows")
    if remaining_violations:
        print(f"      WARN  {remaining_violations} date violation(s) still remain!")
    else:
        print("      OK    account_created_date integrity: PASS")


# ════════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 68)
    print("  DB Migration & Validation — Behavioural Risk Engine Prep")
    print("=" * 68)

    for bank in BANKS:
        print(f"\n{'─' * 55}")
        print(f"  Bank: {bank}")
        print(f"{'─' * 55}")
        conn = get_conn(bank)
        cur  = conn.cursor()
        try:
            step1_verify_schema(conn, cur, bank)
            step2_fix_account_dates(conn, cur, bank)
            step3_ensure_indices(conn, cur, bank)
            step4_validate_timestamps(cur, bank)
            step5_recompute_zero_behaviour(conn, cur, bank)
            step6_summary(cur, bank)
        except Exception as exc:
            conn.rollback()
            print(f"  ERROR [{bank}]: {exc}")
            raise
        finally:
            cur.close()
            conn.close()

    print(f"\n{'=' * 68}")
    print("  Migration complete — databases are ready for risk scoring.")
    print(f"{'=' * 68}\n")


if __name__ == "__main__":
    main()
