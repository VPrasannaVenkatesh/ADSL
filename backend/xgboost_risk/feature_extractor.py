"""
Feature extraction module for XGBoost Continuous Transaction Risk Prediction.
Extracts and computes all canonical features:
1. Transaction attributes (amount, type, hour, unusual hour, cross-bank, beneficiary status)
2. Device information (device type, new device, device changes)
3. Location information (deviation, location changes, anomaly combination)
4. Account context & amount analysis (personal vs business, turnover ratio, balance percentage, avg ratio)
5. Sender dynamic behavioural history & velocity (1h, 6h, 24h, burst ratio, interval, fan-out, splitting)
6. Receiver dynamic behavioural history (fan-in, short dwell, received counts, unique senders)
7. Topological & mule indicators (rapid forwarding, short dwell, splitting, cycles, surges)
"""

from datetime import datetime, time
from typing import Dict, Any, List, Optional
import psycopg2

from .config import FEATURE_NAMES


def extract_features_for_transaction(
    conns: Dict[str, psycopg2.extensions.connection],
    sender_bank: str,
    sender_account_id: str,
    receiver_bank: str,
    receiver_account_id: str,
    amount: int,
    tx_type: str,
    timestamp: datetime,
    device_ip: str,
    location: str,
    recipient_is_new: bool,
    sender_risk_score: float = 0.0,
    receiver_risk_score: float = 0.0,
    dwell_sec: float = -1.0,
    network_signals: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    Extracts all feature values for a live transaction.
    Queries sender and receiver bank DBs for profile and historical behaviour.
    Returns a dictionary of {feature_name: float_value}.
    """
    txn_date = timestamp.date()
    hour = timestamp.hour
    is_night = 1.0 if (hour >= 23 or hour <= 5) else 0.0
    is_cross = 1.0 if (sender_bank.upper() != receiver_bank.upper()) else 0.0
    is_new = 1.0 if recipient_is_new else 0.0

    # Device type encoding
    device_lower = (device_ip or "").lower()
    dev_mobile = 1.0 if "mobile" in device_lower else 0.0
    dev_laptop = 1.0 if "laptop" in device_lower else 0.0
    dev_tablet = 1.0 if "tablet" in device_lower else 0.0
    dev_other = 1.0 if (not dev_mobile and not dev_laptop and not dev_tablet) else 0.0

    # Tx type encoding
    tx_type_upper = (tx_type or "UPI").upper()
    type_upi = 1.0 if tx_type_upper == "UPI" else 0.0
    type_imps = 1.0 if tx_type_upper == "IMPS" else 0.0
    type_neft = 1.0 if tx_type_upper == "NEFT" else 0.0
    type_bt = 1.0 if tx_type_upper in ("BANK_TRANSFER", "TRANSFER") else 0.0

    # Fetch Sender Today Behaviour & Profile
    sender_conn = conns.get(sender_bank)
    sender_bh = _fetch_account_behaviour(sender_conn, sender_account_id, txn_date)
    sender_prof = _fetch_account_profile(sender_conn, sender_account_id)

    # Fetch Receiver Today Behaviour & Profile
    receiver_conn = conns.get(receiver_bank)
    receiver_bh = _fetch_account_behaviour(receiver_conn, receiver_account_id, txn_date)

    # Beneficiary frequency analysis
    beneficiary_freq = 0.0
    if not recipient_is_new and sender_conn:
        beneficiary_freq = _check_beneficiary_frequency(sender_conn, sender_account_id, receiver_account_id)
    elif not recipient_is_new:
        beneficiary_freq = 2.0  # familiar if not marked new

    # Sender Behavioural Metrics
    s_sent_count = float(sender_bh.get("sent_transaction_count", 0))
    s_recv_count = float(sender_bh.get("received_transaction_count", 0))
    s_amt_sent = float(sender_bh.get("total_amount_sent", 0))
    s_amt_recv = float(sender_bh.get("total_amount_received", 0))
    s_avg_amt = float(sender_bh.get("avg_transaction_amount", 0.0))
    s_max_amt = float(sender_bh.get("max_transaction_amount", 0.0))
    s_uniq_rec = float(sender_bh.get("unique_recipients", 0))
    s_uniq_sen = float(sender_bh.get("unique_senders", 0))
    s_tx_1h = float(sender_bh.get("transactions_1h", 0))
    s_tx_6h = float(sender_bh.get("transactions_6h", 0))
    s_tx_24h = float(sender_bh.get("transactions_24h", 0))
    s_avg_int = float(sender_bh.get("avg_transaction_interval_seconds", 3600.0))
    s_min_int = float(sender_bh.get("min_transaction_interval_seconds", 3600.0))
    s_night_tx = float(sender_bh.get("night_transaction_count", 0))
    s_dev_chg = float(sender_bh.get("device_change_count", 0))
    s_loc_chg = float(sender_bh.get("location_change_count", 0))
    s_fan_in = float(sender_bh.get("fan_in", 0))
    s_fan_out = float(sender_bh.get("fan_out", 0))
    s_fwd_amt = float(sender_bh.get("forwarded_amount", 0))
    s_short_dwell = float(sender_bh.get("short_dwell_count", 0))
    s_split_cnt = float(sender_bh.get("amount_split_count", 0))

    # Device & Location Analysis
    is_new_dev = 1.0 if (s_dev_chg > 0 or "new" in device_lower or dev_other == 1.0) else 0.0
    normal_city = sender_prof.get("primary_location", "").strip().lower()
    loc_current = (location or "").strip().lower()
    is_loc_dev = 1.0 if (s_loc_chg > 0 or (normal_city and loc_current and normal_city not in loc_current and loc_current not in normal_city)) else 0.0
    dev_loc_anomaly = 1.0 if (is_new_dev == 1.0 and is_loc_dev == 1.0) else 0.0

    # Account Profile Context & Amount Analysis
    is_biz = 1.0 if sender_prof.get("is_business") else 0.0
    expected_vol = float(sender_prof.get("expected_volume", 50000.0 if not is_biz else 1500000.0))
    op_start = int(sender_prof.get("operating_hours_start", 8))
    op_end = int(sender_prof.get("operating_hours_end", 22))
    balance = float(sender_prof.get("balance", max(amount * 2.5, 50000.0)))

    amt_turnover_ratio = round(float(amount) / max(expected_vol, 1000.0), 3)
    is_within_hours = 1.0 if (op_start <= hour <= op_end) else 0.0
    is_unusual_hour = 1.0 if (is_within_hours == 0.0 or is_night == 1.0) else 0.0
    balance_pct = round(float(amount) / max(balance, 1000.0), 3)

    # Sender Ratios: compute baseline average transaction amount when no transactions recorded today
    typ_size = float(sender_prof.get("typical_size", 120000.0 if is_biz else 2500.0))
    baseline_avg = s_avg_amt if s_avg_amt >= 500.0 else typ_size
    baseline_max = s_max_amt if s_max_amt >= 500.0 else (baseline_avg * 2.5)

    amt_vs_avg = round(float(amount) / max(baseline_avg, 500.0), 2)
    amt_vs_max = round(float(amount) / max(baseline_max, 500.0), 2)
    s_burst_ratio = round((s_tx_1h * 6.0) / max(s_tx_6h, 1.0), 2)
    s_velocity_ratio = round((s_tx_1h * 24.0) / max(s_tx_24h, 1.0), 2)

    # Receiver Behavioural Metrics
    r_recv_count = float(receiver_bh.get("received_transaction_count", 0))
    r_sent_count = float(receiver_bh.get("sent_transaction_count", 0))
    r_amt_recv = float(receiver_bh.get("total_amount_received", 0))
    r_avg_amt = float(receiver_bh.get("avg_transaction_amount", 0.0))
    r_max_amt = float(receiver_bh.get("max_transaction_amount", 0.0))
    r_uniq_sen = float(receiver_bh.get("unique_senders", 0))
    r_tx_1h = float(receiver_bh.get("transactions_1h", 0))
    r_tx_24h = float(receiver_bh.get("transactions_24h", 0))
    r_fan_in = float(receiver_bh.get("fan_in", 0))
    r_fan_out = float(receiver_bh.get("fan_out", 0))
    r_short_dwell = float(receiver_bh.get("short_dwell_count", 0))

    # Graph & Topological Mule Indicators
    net_sig = network_signals or {}
    rapid_fwd = 1.0 if (net_sig.get("rapid_forwarding") or (0 < dwell_sec <= 180.0 and s_amt_recv > 0) or s_fwd_amt > 0) else 0.0
    short_dwell_flag = 1.0 if (0 < dwell_sec <= 300.0 or s_short_dwell > 0 or r_short_dwell > 0) else 0.0
    amount_split = 1.0 if (net_sig.get("amount_splitting") or s_split_cnt > 0) else 0.0
    cycle_det = 1.0 if net_sig.get("cycle_detected") else 0.0
    multihop = 1.0 if net_sig.get("multihop_flow") else 0.0
    sudden_surge = 1.0 if (s_tx_1h >= 4 or r_tx_1h >= 4 or (s_amt_sent > 0 and s_amt_recv > 0 and abs(s_amt_sent - s_amt_recv) < 5000)) else 0.0

    feature_dict = {
        # 1. Transaction attributes
        "amount": float(amount),
        "is_cross_bank": is_cross,
        "recipient_is_new": is_new,
        "beneficiary_usage_frequency": beneficiary_freq,
        "is_night": is_night,
        "hour_of_day": float(hour),
        "is_unusual_hour": is_unusual_hour,
        "tx_type_upi": type_upi,
        "tx_type_imps": type_imps,
        "tx_type_neft": type_neft,
        "tx_type_bank_transfer": type_bt,
        
        # 2. Device information
        "device_is_mobile": dev_mobile,
        "device_is_laptop": dev_laptop,
        "device_is_tablet": dev_tablet,
        "device_is_other": dev_other,
        "is_new_device": is_new_dev,
        "sender_device_changes": s_dev_chg,
        
        # 3. Location information
        "is_location_deviation": is_loc_dev,
        "sender_location_changes": s_loc_chg,
        "device_location_anomaly": dev_loc_anomaly,
        
        # 4. Account Profile Context & Amount Analysis
        "is_business": is_biz,
        "expected_turnover_or_volume": expected_vol,
        "amount_vs_turnover_ratio": amt_turnover_ratio,
        "is_within_operating_hours": is_within_hours,
        "sender_balance": balance,
        "transfer_percentage_of_balance": balance_pct,
        "sender_amount_vs_avg_ratio": amt_vs_avg,
        "sender_amount_vs_max_ratio": amt_vs_max,
        
        # 5. Sender behavioural metrics & Velocity
        "sender_sent_count": s_sent_count,
        "sender_received_count": s_recv_count,
        "sender_total_amount_sent": s_amt_sent,
        "sender_total_amount_received": s_amt_recv,
        "sender_avg_tx_amount": s_avg_amt,
        "sender_max_tx_amount": s_max_amt,
        "sender_unique_recipients": s_uniq_rec,
        "sender_unique_senders": s_uniq_sen,
        "sender_tx_1h": s_tx_1h,
        "sender_tx_6h": s_tx_6h,
        "sender_tx_24h": s_tx_24h,
        "sender_avg_interval_sec": s_avg_int,
        "sender_min_interval_sec": s_min_int,
        "sender_burst_ratio": s_burst_ratio,
        "sender_velocity_ratio": s_velocity_ratio,
        "sender_night_tx_count": s_night_tx,
        "sender_fan_out": s_fan_out,
        "sender_fan_in": s_fan_in,
        "sender_forwarded_amount": s_fwd_amt,
        "sender_short_dwell_count": s_short_dwell,
        "sender_amount_split_count": s_split_cnt,
        "sender_behavioural_risk_score": float(sender_risk_score),
        
        # 6. Receiver behavioural metrics
        "receiver_received_count": r_recv_count,
        "receiver_sent_count": r_sent_count,
        "receiver_total_amount_received": r_amt_recv,
        "receiver_avg_tx_amount": r_avg_amt,
        "receiver_max_tx_amount": r_max_amt,
        "receiver_unique_senders": r_uniq_sen,
        "receiver_tx_1h": r_tx_1h,
        "receiver_tx_24h": r_tx_24h,
        "receiver_fan_in": r_fan_in,
        "receiver_fan_out": r_fan_out,
        "receiver_short_dwell_count": r_short_dwell,
        "receiver_behavioural_risk_score": float(receiver_risk_score),
        
        # 7. Graph & Topological Mule Indicators
        "network_rapid_forwarding": rapid_fwd,
        "network_short_dwell_flag": short_dwell_flag,
        "network_amount_splitting": amount_split,
        "network_cycle_detected": cycle_det,
        "mule_multihop_signal": multihop,
        "sudden_in_out_surge": sudden_surge,
    }

    # Ensure all canonical FEATURE_NAMES exist and are clean floats
    safe_dict = {}
    for name in FEATURE_NAMES:
        val = feature_dict.get(name, 0.0)
        safe_dict[name] = 0.0 if (val is None or val != val) else float(val)

    return safe_dict


def features_to_vector(features_dict: Dict[str, float]) -> List[float]:
    """Converts feature dictionary into an ordered list strictly matching FEATURE_NAMES."""
    return [float(features_dict.get(fname, 0.0)) for fname in FEATURE_NAMES]


def _fetch_account_profile(
    conn: Optional[psycopg2.extensions.connection],
    account_id: str,
) -> Dict[str, Any]:
    """Retrieves account type, balance, turnover/volume, and typical operating hours."""
    if not conn:
        return {}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT account_type, current_balance, home_location, business_category
                FROM accounts WHERE account_id = %s
            """, (account_id,))
            row = cur.fetchone()
            if not row:
                return {}
            acc_type = str(row[0] or "PERSONAL").upper()
            bal = float(row[1] or 50000.0)
            loc = str(row[2] or "Chennai")
            biz_cat = str(row[3] or "")
            is_biz = (acc_type == "BUSINESS")
            
            if is_biz:
                cur.execute("""
                    SELECT expected_monthly_turnover, avg_transaction_amount, operating_hours_start, operating_hours_end 
                    FROM business_profiles WHERE account_id = %s
                """, (account_id,))
                b_row = cur.fetchone()
                exp_turnover = float(b_row[0] or 1500000.0) if b_row else 1500000.0
                typ_size = float(b_row[1] or 150000.0) if b_row else 150000.0
                op_s = int(b_row[2] or 9) if b_row else 9
                op_e = int(b_row[3] or 20) if b_row else 20
                return {
                    "is_business": True,
                    "balance": bal,
                    "primary_location": loc,
                    "expected_volume": exp_turnover,
                    "typical_size": typ_size,
                    "operating_hours_start": op_s,
                    "operating_hours_end": op_e,
                    "business_category": biz_cat,
                }
            else:
                cur.execute("""
                    SELECT expected_monthly_volume, typical_hours_start, typical_hours_end 
                    FROM personal_profiles WHERE account_id = %s
                """, (account_id,))
                p_row = cur.fetchone()
                exp_vol = float(p_row[0] or 50000.0) if p_row else 50000.0
                op_s = int(p_row[1] or 8) if p_row else 8
                op_e = int(p_row[2] or 22) if p_row else 22
                return {
                    "is_business": False,
                    "balance": bal,
                    "primary_location": loc,
                    "expected_volume": exp_vol,
                    "typical_size": exp_vol / 20.0,
                    "operating_hours_start": op_s,
                    "operating_hours_end": op_e,
                }
    except Exception as e:
        print(f"[FeatureExtractor] Error fetching profile for {account_id}: {e}")
        return {}


def _check_beneficiary_frequency(
    conn: psycopg2.extensions.connection,
    sender_account_id: str,
    receiver_account_id: str,
) -> float:
    """Returns 0.0 (new), 1.0 (rare: 1-2 tx), or 2.0 (frequent: >=3 tx)."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE sender_account_id = %s AND receiver_account_id = %s
            """, (sender_account_id, receiver_account_id))
            r = cur.fetchone()
            cnt = int(r[0] or 0) if r else 0
            if cnt == 0:
                return 0.0
            elif cnt < 3:
                return 1.0
            else:
                return 2.0
    except Exception:
        return 1.0


def _fetch_account_behaviour(
    conn: Optional[psycopg2.extensions.connection],
    account_id: str,
    target_date: Any,
) -> Dict[str, Any]:
    """Safely retrieves behaviour_history for an account on the target date."""
    if not conn:
        return {}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    sent_transaction_count, received_transaction_count,
                    total_amount_sent, total_amount_received,
                    avg_transaction_amount, max_transaction_amount,
                    unique_recipients, unique_senders,
                    transactions_1h, transactions_6h, transactions_24h,
                    avg_transaction_interval_seconds, min_transaction_interval_seconds,
                    night_transaction_count,
                    device_change_count, location_change_count,
                    fan_in, fan_out, forwarded_amount,
                    short_dwell_count, amount_split_count
                FROM behaviour_history
                WHERE account_id = %s AND behaviour_date = %s
            """, (account_id, target_date))
            row = cur.fetchone()
            if row:
                return {
                    "sent_transaction_count": row[0] or 0,
                    "received_transaction_count": row[1] or 0,
                    "total_amount_sent": row[2] or 0,
                    "total_amount_received": row[3] or 0,
                    "avg_transaction_amount": row[4] or 0.0,
                    "max_transaction_amount": row[5] or 0.0,
                    "unique_recipients": row[6] or 0,
                    "unique_senders": row[7] or 0,
                    "transactions_1h": row[8] or 0,
                    "transactions_6h": row[9] or 0,
                    "transactions_24h": row[10] or 0,
                    "avg_transaction_interval_seconds": row[11] or 3600.0,
                    "min_transaction_interval_seconds": row[12] or 3600.0,
                    "night_transaction_count": row[13] or 0,
                    "device_change_count": row[14] or 0,
                    "location_change_count": row[15] or 0,
                    "fan_in": row[16] or 0,
                    "fan_out": row[17] or 0,
                    "forwarded_amount": row[18] or 0,
                    "short_dwell_count": row[19] or 0,
                    "amount_split_count": row[20] or 0,
                }
    except Exception:
        pass
    return {}
