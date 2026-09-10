"""
Feature extraction module for Bank-Level Behavioural Risk Scoring.
Extracts account attributes, today's behaviour history, and historical baseline
using ONLY the local bank's database.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
import psycopg2


def extract_account_features(
    conn: psycopg2.extensions.connection,
    bank: str,
    account_id: str,
    txn_timestamp: datetime,
    txn_amount: int,
    txn_type: str,
    device_ip: str,
    location: str,
    recipient_is_new: bool,
    role: str = "SENDER",
) -> Dict[str, Any]:
    """
    Extracts all local features for account_id from its bank database.
    No cross-bank customer information is accessed or leaked.
    """
    txn_date = txn_timestamp.date()

    with conn.cursor() as cur:
        # 1. Fetch Account Details
        cur.execute("""
            SELECT account_id, account_number, customer_name,
                   account_type, current_balance, account_created_date,
                   home_location, account_status
            FROM accounts
            WHERE account_id = %s
        """, (account_id,))
        acc_row = cur.fetchone()
        if not acc_row:
            return {}

        account_info = {
            "account_id": acc_row[0],
            "account_number": acc_row[1],
            "customer_name": acc_row[2],
            "account_type": acc_row[3],
            "current_balance": int(acc_row[4]),
            "account_created_date": acc_row[5],
            "home_location": acc_row[6] or "Chennai",
            "account_status": acc_row[7],
            "account_age_days": (txn_date - acc_row[5]).days if acc_row[5] else 365,
        }

        # 2. Fetch Today's Behaviour History Record
        cur.execute("""
            SELECT
                transaction_count, sent_transaction_count, received_transaction_count,
                total_amount_sent, total_amount_received,
                avg_transaction_amount, min_transaction_amount, max_transaction_amount,
                unique_recipients, unique_senders, new_recipients_count, new_senders_count,
                transactions_1h, transactions_6h, transactions_24h,
                avg_transaction_interval_seconds, min_transaction_interval_seconds,
                first_transaction_time, last_transaction_time,
                active_hours, night_transaction_count,
                unique_device_count, new_device_count, device_change_count, primary_device,
                unique_location_count, new_location_count, location_change_count,
                fan_in, fan_out, forwarded_amount, same_day_forward_count,
                short_dwell_count, amount_split_count, cross_bank_transaction_count,
                opening_balance, closing_balance, min_balance, max_balance, avg_balance
            FROM behaviour_history
            WHERE account_id = %s AND behaviour_date = %s
        """, (account_id, txn_date))
        today_bh = cur.fetchone()

        if today_bh:
            today_features = {
                "transaction_count": today_bh[0] or 1,
                "sent_count": today_bh[1] or (1 if role == "SENDER" else 0),
                "recv_count": today_bh[2] or (1 if role == "RECEIVER" else 0),
                "total_amount_sent": int(today_bh[3] or 0),
                "total_amount_received": int(today_bh[4] or 0),
                "avg_amount": int(today_bh[5] or txn_amount),
                "min_amount": int(today_bh[6] or txn_amount),
                "max_amount": int(today_bh[7] or txn_amount),
                "unique_recipients": today_bh[8] or 0,
                "unique_senders": today_bh[9] or 0,
                "new_recipients_count": today_bh[10] or (1 if recipient_is_new and role == "SENDER" else 0),
                "new_senders_count": today_bh[11] or 0,
                "transactions_1h": today_bh[12] or 1,
                "transactions_6h": today_bh[13] or 1,
                "transactions_24h": today_bh[14] or 1,
                "avg_interval_sec": int(today_bh[15] or 0),
                "min_interval_sec": int(today_bh[16] or 0),
                "first_tx_time": today_bh[17],
                "last_tx_time": today_bh[18],
                "active_hours": today_bh[19] or 1,
                "night_count": today_bh[20] or (1 if txn_timestamp.hour < 6 or txn_timestamp.hour >= 22 else 0),
                "unique_devices": today_bh[21] or 1,
                "new_device_count": today_bh[22] or 0,
                "device_change_count": today_bh[23] or 0,
                "primary_device": today_bh[24] or (device_ip.split(':')[0] if device_ip else "Mobile"),
                "unique_locations": today_bh[25] or 1,
                "new_location_count": today_bh[26] or 0,
                "location_change_count": today_bh[27] or 0,
                "fan_in": today_bh[28] or 0,
                "fan_out": today_bh[29] or 0,
                "forwarded_amount": int(today_bh[30] or 0),
                "same_day_forward_count": today_bh[31] or 0,
                "short_dwell_count": today_bh[32] or 0,
                "amount_split_count": today_bh[33] or 0,
                "cross_bank_count": today_bh[34] or 0,
                "opening_balance": int(today_bh[35] or account_info["current_balance"]),
                "closing_balance": int(today_bh[36] or account_info["current_balance"]),
                "min_balance": int(today_bh[37] or account_info["current_balance"]),
                "max_balance": int(today_bh[38] or account_info["current_balance"]),
                "avg_balance": int(today_bh[39] or account_info["current_balance"]),
            }
        else:
            today_features = {
                "transaction_count": 1,
                "sent_count": 1 if role == "SENDER" else 0,
                "recv_count": 1 if role == "RECEIVER" else 0,
                "total_amount_sent": txn_amount if role == "SENDER" else 0,
                "total_amount_received": txn_amount if role == "RECEIVER" else 0,
                "avg_amount": txn_amount,
                "min_amount": txn_amount,
                "max_amount": txn_amount,
                "unique_recipients": 1 if role == "SENDER" else 0,
                "unique_senders": 1 if role == "RECEIVER" else 0,
                "new_recipients_count": 1 if recipient_is_new and role == "SENDER" else 0,
                "new_senders_count": 0,
                "transactions_1h": 1,
                "transactions_6h": 1,
                "transactions_24h": 1,
                "avg_interval_sec": 0,
                "min_interval_sec": 0,
                "first_tx_time": txn_timestamp.strftime('%H:%M:%S'),
                "last_tx_time": txn_timestamp.strftime('%H:%M:%S'),
                "active_hours": 1,
                "night_count": 1 if (txn_timestamp.hour < 6 or txn_timestamp.hour >= 22) else 0,
                "unique_devices": 1,
                "new_device_count": 0,
                "device_change_count": 0,
                "primary_device": device_ip.split(':')[0] if device_ip else "Mobile",
                "unique_locations": 1,
                "new_location_count": 0,
                "location_change_count": 0,
                "fan_in": 0,
                "fan_out": 0,
                "forwarded_amount": 0,
                "same_day_forward_count": 0,
                "short_dwell_count": 0,
                "amount_split_count": 0,
                "cross_bank_count": 0,
                "opening_balance": account_info["current_balance"],
                "closing_balance": account_info["current_balance"],
                "min_balance": account_info["current_balance"],
                "max_balance": account_info["current_balance"],
                "avg_balance": account_info["current_balance"],
            }

        # 3. Fetch Historical Baseline Aggregates (Prior 90 Days)
        cur.execute("""
            SELECT
                COALESCE(AVG(avg_transaction_amount), 0),
                COALESCE(MAX(max_transaction_amount), 0),
                COALESCE(AVG(transaction_count), 1),
                COALESCE(MAX(transaction_count), 1),
                COALESCE(AVG(avg_balance), 0),
                COALESCE(COUNT(*), 0)
            FROM behaviour_history
            WHERE account_id = %s
              AND behaviour_date < %s
              AND behaviour_date >= %s
        """, (account_id, txn_date, txn_date - timedelta(days=90)))
        hist_row = cur.fetchone()

        historical_baseline = {
            "hist_avg_amount": int(hist_row[0]) if hist_row and hist_row[0] > 0 else txn_amount,
            "hist_max_amount": int(hist_row[1]) if hist_row and hist_row[1] > 0 else txn_amount,
            "hist_avg_daily_tx_count": float(hist_row[2]) if hist_row and hist_row[2] > 0 else 1.0,
            "hist_max_daily_tx_count": int(hist_row[3]) if hist_row and hist_row[3] > 0 else 1,
            "hist_avg_balance": int(hist_row[4]) if hist_row and hist_row[4] > 0 else account_info["current_balance"],
            "hist_active_days_count": int(hist_row[5]) if hist_row else 0,
        }

    return {
        "bank": bank,
        "account": account_info,
        "current_tx": {
            "amount": txn_amount,
            "tx_type": txn_type,
            "timestamp": txn_timestamp,
            "device_ip": device_ip,
            "location": location,
            "recipient_is_new": recipient_is_new,
            "role": role,
        },
        "today_behaviour": today_features,
        "historical_baseline": historical_baseline,
    }
