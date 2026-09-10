"""
Dynamic behaviour history updater for multi-bank simulation.
Recalculates all daily behavioural metrics for an account from real PostgreSQL transaction records.
"""

from datetime import date, datetime
import psycopg2


def secs_to_readable(secs: int) -> str:
    """Converts seconds into human-readable duration."""
    if secs <= 0:
        return "0s"
    elif secs < 60:
        return f"{secs}s"
    elif secs < 3600:
        return f"{secs // 60}m {secs % 60}s"
    else:
        return f"{secs // 3600}h {(secs % 3600) // 60}m"


def update_daily_account_behaviour(conn: psycopg2.extensions.connection, bank: str, account_id: str, txn_date: date):
    """
    Recalculates and upserts all daily behavioural metrics for account_id on txn_date
    using the full transaction history stored in the bank's PostgreSQL database.
    """
    with conn.cursor() as cur:
        # Fetch all transactions involving this account on this date in chronological order
        cur.execute("""
            SELECT
                sender_account_id, sender_bank,
                receiver_account_id, receiver_bank,
                amount, transaction_timestamp,
                sender_balance_before, sender_balance_after,
                receiver_balance_before, receiver_balance_after,
                device_ip, location, recipient_is_new
            FROM transactions
            WHERE transaction_timestamp::date = %s
              AND (sender_account_id = %s OR receiver_account_id = %s)
            ORDER BY transaction_timestamp ASC
        """, (txn_date, account_id, account_id))
        rows = cur.fetchall()

        if not rows:
            return

        sent = [r for r in rows if r[0] == account_id]
        recv = [r for r in rows if r[2] == account_id]
        all_ts = [r[5] for r in rows]

        # ── 1. Volume Metrics ────────────────────────────────────────────────
        tx_count = len(rows)
        sent_count = len(sent)
        recv_count = len(recv)

        # ── 2. Amount Metrics ────────────────────────────────────────────────
        all_amounts = [r[4] for r in rows]
        total_sent = sum(r[4] for r in sent)
        total_recv = sum(r[4] for r in recv)
        avg_amt = sum(all_amounts) // len(all_amounts) if all_amounts else 0
        min_amt = min(all_amounts) if all_amounts else 0
        max_amt = max(all_amounts) if all_amounts else 0

        # ── 3. Counterparties ────────────────────────────────────────────────
        recipients = [r[2] for r in sent]
        senders_list = [r[0] for r in recv]
        unique_recipients = len(set(recipients))
        unique_senders_cnt = len(set(senders_list))
        new_recip_cnt = sum(1 for r in sent if r[12])

        cur.execute("""
            SELECT DISTINCT sender_account_id
            FROM transactions
            WHERE receiver_account_id = %s
              AND transaction_timestamp::date < %s
        """, (account_id, txn_date))
        prior_senders = {r[0] for r in cur.fetchall()}
        new_senders_cnt = len(set(senders_list) - prior_senders)

        # ── 4. Velocity ──────────────────────────────────────────────────────
        latest_ts = all_ts[-1]
        txns_1h = sum(1 for r in rows if (latest_ts - r[5]).total_seconds() <= 3600)
        txns_6h = sum(1 for r in rows if (latest_ts - r[5]).total_seconds() <= 21600)
        txns_24h = tx_count

        # ── 5. Intervals ─────────────────────────────────────────────────────
        intervals = [
            int((all_ts[i] - all_ts[i - 1]).total_seconds())
            for i in range(1, len(all_ts))
            if (all_ts[i] - all_ts[i - 1]).total_seconds() > 0
        ]
        avg_interval = sum(intervals) // len(intervals) if intervals else 0
        min_interval = min(intervals) if intervals else 0

        # ── 6. Timing ────────────────────────────────────────────────────────
        first_tx_time = all_ts[0].strftime('%H:%M:%S') if all_ts else None
        last_tx_time = all_ts[-1].strftime('%H:%M:%S') if all_ts else None
        active_hours = len(set(t.hour for t in all_ts))
        night_count = sum(1 for t in all_ts if t.hour < 6 or t.hour >= 22)

        # ── 7. Device Behaviour ──────────────────────────────────────────────
        device_types = [r[10].split(':')[0] for r in rows if r[10]]
        unique_devs = set(device_types)
        cur.execute("""
            SELECT DISTINCT SPLIT_PART(device_ip, ':', 1)
            FROM transactions
            WHERE (sender_account_id = %s OR receiver_account_id = %s)
              AND transaction_timestamp::date < %s
              AND device_ip IS NOT NULL
        """, (account_id, account_id, txn_date))
        prior_devices = {r[0] for r in cur.fetchall()}
        new_dev_count = len(unique_devs - prior_devices)

        dev_changes = sum(
            1 for i in range(1, len(device_types))
            if device_types[i] != device_types[i - 1]
        )
        primary_dev = max(set(device_types), key=device_types.count) if device_types else None

        # ── 8. Location Behaviour ────────────────────────────────────────────
        all_locs = [r[11] for r in rows if r[11]]
        unique_locs = set(all_locs)
        cur.execute("""
            SELECT DISTINCT location
            FROM transactions
            WHERE (sender_account_id = %s OR receiver_account_id = %s)
              AND transaction_timestamp::date < %s
              AND location IS NOT NULL
        """, (account_id, account_id, txn_date))
        prior_locs = {r[0] for r in cur.fetchall()}
        new_loc_count = len(unique_locs - prior_locs)

        loc_changes = sum(
            1 for i in range(1, len(all_locs))
            if all_locs[i] != all_locs[i - 1]
        )

        # ── 9. Money Flow Signals ────────────────────────────────────────────
        fan_in = unique_senders_cnt
        fan_out = unique_recipients

        recv_amt_set = set(r[4] for r in recv)
        forwarded_amt = sum(r[4] for r in sent if r[4] in recv_amt_set)
        same_day_fwd = sum(1 for r in sent if r[4] in recv_amt_set)

        short_dwell = sum(
            1 for rt in recv
            if any(0 < (st[5] - rt[5]).total_seconds() <= 3600 for st in sent)
        )
        amount_split = sum(
            1 for rt in recv
            if len([st for st in sent if st[4] < rt[4]]) > 1
        )
        cross_bank = (
            sum(1 for r in sent if r[3] != bank) +
            sum(1 for r in recv if r[1] != bank)
        )

        # ── 10. Balance Behaviour ────────────────────────────────────────────
        bal_events = sorted(
            [(r[5], r[6], r[7]) for r in sent if r[6] is not None and r[7] is not None] +
            [(r[5], r[8], r[9]) for r in recv if r[8] is not None and r[9] is not None],
            key=lambda x: x[0]
        )

        if bal_events:
            opening_bal = bal_events[0][1]
            closing_bal = bal_events[-1][2]
            flat_bals = [b for _, bb, ba in bal_events for b in (bb, ba)]
            min_bal = min(flat_bals) if flat_bals else 0
            max_bal = max(flat_bals) if flat_bals else 0
            avg_bal = sum(flat_bals) // len(flat_bals) if flat_bals else 0
        else:
            opening_bal = closing_bal = min_bal = max_bal = avg_bal = 0

        # ── 11. Upsert into behaviour_history ────────────────────────────────
        cur.execute("""
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
            ) VALUES (
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (account_id, behaviour_date) DO UPDATE SET
                transaction_count = EXCLUDED.transaction_count,
                sent_transaction_count = EXCLUDED.sent_transaction_count,
                received_transaction_count = EXCLUDED.received_transaction_count,
                total_amount_sent = EXCLUDED.total_amount_sent,
                total_amount_received = EXCLUDED.total_amount_received,
                avg_transaction_amount = EXCLUDED.avg_transaction_amount,
                min_transaction_amount = EXCLUDED.min_transaction_amount,
                max_transaction_amount = EXCLUDED.max_transaction_amount,
                unique_recipients = EXCLUDED.unique_recipients,
                unique_senders = EXCLUDED.unique_senders,
                new_recipients_count = EXCLUDED.new_recipients_count,
                new_senders_count = EXCLUDED.new_senders_count,
                transactions_1h = EXCLUDED.transactions_1h,
                transactions_6h = EXCLUDED.transactions_6h,
                transactions_24h = EXCLUDED.transactions_24h,
                avg_transaction_interval_seconds = EXCLUDED.avg_transaction_interval_seconds,
                avg_transaction_interval_readable = EXCLUDED.avg_transaction_interval_readable,
                min_transaction_interval_seconds = EXCLUDED.min_transaction_interval_seconds,
                min_transaction_interval_readable = EXCLUDED.min_transaction_interval_readable,
                first_transaction_time = EXCLUDED.first_transaction_time,
                last_transaction_time = EXCLUDED.last_transaction_time,
                active_hours = EXCLUDED.active_hours,
                night_transaction_count = EXCLUDED.night_transaction_count,
                unique_device_count = EXCLUDED.unique_device_count,
                new_device_count = EXCLUDED.new_device_count,
                device_change_count = EXCLUDED.device_change_count,
                primary_device = EXCLUDED.primary_device,
                unique_location_count = EXCLUDED.unique_location_count,
                new_location_count = EXCLUDED.new_location_count,
                location_change_count = EXCLUDED.location_change_count,
                fan_in = EXCLUDED.fan_in,
                fan_out = EXCLUDED.fan_out,
                forwarded_amount = EXCLUDED.forwarded_amount,
                same_day_forward_count = EXCLUDED.same_day_forward_count,
                short_dwell_count = EXCLUDED.short_dwell_count,
                amount_split_count = EXCLUDED.amount_split_count,
                cross_bank_transaction_count = EXCLUDED.cross_bank_transaction_count,
                opening_balance = EXCLUDED.opening_balance,
                closing_balance = EXCLUDED.closing_balance,
                min_balance = EXCLUDED.min_balance,
                max_balance = EXCLUDED.max_balance,
                avg_balance = EXCLUDED.avg_balance
        """, (
            account_id, txn_date,
            tx_count, sent_count, recv_count,
            total_sent, total_recv,
            avg_amt, min_amt, max_amt,
            unique_recipients, unique_senders_cnt, new_recip_cnt, new_senders_cnt,
            txns_1h, txns_6h, txns_24h,
            avg_interval, secs_to_readable(avg_interval),
            min_interval, secs_to_readable(min_interval),
            first_tx_time, last_tx_time,
            active_hours, night_count,
            len(unique_devs), new_dev_count, dev_changes, primary_dev,
            len(unique_locs), new_loc_count, loc_changes,
            fan_in, fan_out, forwarded_amt, same_day_fwd,
            short_dwell, amount_split, cross_bank,
            opening_bal, closing_bal, min_bal, max_bal, avg_bal
        ))
    conn.commit()

    # ── Smart Risk Profile Recalculation Hook ──────────────────────────────────
    # Check if meaningful behavioural changes occurred before recalculating
    try:
        from risk_engine.account_risk_profile import (
            check_meaningful_behaviour_change,
            recalculate_and_store_profile,
            get_stored_account_risk_profile,
        )
        from risk_engine.feature_extractor import extract_account_features

        stored_prof = get_stored_account_risk_profile(conn, bank, account_id)
        latest_row = rows[-1] if rows else None
        if latest_row:
            features = extract_account_features(
                conn=conn,
                bank=bank,
                account_id=account_id,
                txn_timestamp=latest_row[5],
                txn_amount=int(latest_row[4]),
                txn_type="TRANSFER",
                device_ip=latest_row[10] or "Mobile:192.168.1.1",
                location=latest_row[11] or "Chennai",
                recipient_is_new=bool(latest_row[12]),
                role="SENDER" if latest_row[0] == account_id else "RECEIVER",
            )
            should_recalc, reason = check_meaningful_behaviour_change(features, stored_prof)
            if should_recalc:
                recalculate_and_store_profile(
                    conn=conn,
                    bank_name=bank,
                    account_id=account_id,
                    trigger_reason=reason or "MEANINGFUL_CHANGE",
                    features=features,
                    role="SENDER" if latest_row[0] == account_id else "RECEIVER",
                    transaction_id=f"TX_{account_id}_{int(txn_date.strftime('%Y%m%d'))}",
                )
    except Exception as _recalc_err:
        # Non-fatal — risk profile preservation should never crash transaction recording
        pass

