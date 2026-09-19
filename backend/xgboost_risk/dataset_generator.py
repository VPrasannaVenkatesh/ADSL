"""
Dataset preparation module for Continuous XGBoost Transaction Risk Prediction.
Extracts historical transactions from bank PostgreSQL databases (SBI, AXIS, IOB),
derives rich behavioural features, and generates balanced continuous risk targets (0.0 to 100.0)
covering:
  1. Genuine Personal Transactions (Scores 5 to 28)
  2. Legitimate High-Value Business Payments (Scores 8 to 30)
  3. Medium-Risk Borderline Scenarios (Scores 31 to 58)
  4. High-Risk Mule / Fraud Patterns (Scores 61 to 98)
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.db_connection import get_all_bank_connections, BANK_NAMES
from .config import FEATURE_NAMES
from .feature_extractor import extract_features_for_transaction, features_to_vector


def compute_continuous_target(feat: Dict[str, float]) -> float:
    """
    Computes a realistic, multi-factor continuous ground-truth risk score (0.0 to 100.0).
    No single feature dictates the outcome:
    - Large business payments do NOT automatically produce high risk.
    - Risk is evaluated as an organic combination of amount vs baseline, velocity,
      beneficiary familiarity, device/location anomaly, and topological mule flow.
    """
    is_biz = feat.get("is_business", 0.0) == 1.0
    turnover_ratio = feat.get("amount_vs_turnover_ratio", 0.0)
    amt_vs_avg = feat.get("sender_amount_vs_avg_ratio", 1.0)
    balance_pct = feat.get("transfer_percentage_of_balance", 0.0)
    
    # 1. Amount Signal relative to Account Profile
    amount_signal = 0.0
    if is_biz:
        # Legitimate business transactions: low turnover ratio is completely normal
        if turnover_ratio <= 0.25:
            amount_signal = turnover_ratio * 15.0  # max ~3.75
        elif turnover_ratio <= 0.60:
            amount_signal = 4.0 + (turnover_ratio - 0.25) * 20.0
        else:
            amount_signal = 11.0 + min((turnover_ratio - 0.60) * 30.0, 20.0)
    else:
        # Personal transactions: compare with historical average
        if amt_vs_avg <= 1.5:
            amount_signal = amt_vs_avg * 4.0  # max ~6.0
        elif amt_vs_avg <= 3.5:
            amount_signal = 6.0 + (amt_vs_avg - 1.5) * 6.5  # max ~19.0
        else:
            amount_signal = 19.0 + min((amt_vs_avg - 3.5) * 3.5, 18.0)

    # Balance percentage signal (draining >75% of account balance)
    bal_signal = 0.0
    if balance_pct >= 0.85:
        bal_signal = 9.0
    elif balance_pct >= 0.60:
        bal_signal = 4.5

    # 2. Timing & Operating Hour Signal
    time_signal = 0.0
    if feat.get("is_unusual_hour", 0.0) == 1.0:
        time_signal = 8.0 if is_biz else 10.0
    elif feat.get("is_night", 0.0) == 1.0:
        time_signal = 5.0

    # 3. Device & Location Signal
    dev_loc_signal = 0.0
    dev_changes = feat.get("sender_device_changes", 0.0)
    loc_changes = feat.get("sender_location_changes", 0.0)
    is_new_dev = feat.get("is_new_device", 0.0)
    is_loc_dev = feat.get("is_location_deviation", 0.0)
    
    if feat.get("device_location_anomaly", 0.0) == 1.0:
        dev_loc_signal = 20.0
    else:
        if is_new_dev:
            dev_loc_signal += 6.5
        if is_loc_dev:
            dev_loc_signal += 6.5
        dev_loc_signal += min(dev_changes * 2.5 + loc_changes * 2.5, 8.0)

    # 4. Beneficiary Familiarity Signal
    beneficiary_signal = 0.0
    bene_freq = feat.get("beneficiary_usage_frequency", 1.0)
    is_new_bene = feat.get("recipient_is_new", 0.0)
    if is_new_bene == 1.0:
        beneficiary_signal = 9.5  # Moderate risk signal, NOT forcing HIGH alone
    elif bene_freq == 1.0:
        beneficiary_signal = 3.0
    elif bene_freq >= 2.0:
        beneficiary_signal = 0.0

    # 5. Velocity & Burst Signal
    velocity_signal = 0.0
    tx_1h = feat.get("sender_tx_1h", 0.0)
    burst_ratio = feat.get("sender_burst_ratio", 1.0)
    min_int = feat.get("sender_min_interval_sec", 3600.0)
    
    if tx_1h >= 6 or (min_int <= 45.0 and tx_1h >= 3):
        velocity_signal = 24.0
    elif tx_1h >= 4 or burst_ratio >= 3.0:
        velocity_signal = 15.0
    elif tx_1h >= 2 or burst_ratio >= 1.8:
        velocity_signal = 7.0

    # 6. Topological Mule Flow Signals
    mule_signal = 0.0
    if feat.get("network_rapid_forwarding", 0.0) == 1.0:
        mule_signal += 24.0
    if feat.get("network_short_dwell_flag", 0.0) == 1.0:
        mule_signal += 16.0
    if feat.get("network_amount_splitting", 0.0) == 1.0 or feat.get("sender_amount_split_count", 0.0) >= 2:
        mule_signal += 16.0
    if feat.get("receiver_fan_in", 0.0) >= 4 or feat.get("sender_fan_out", 0.0) >= 4:
        mule_signal += 18.0
    elif feat.get("receiver_fan_in", 0.0) >= 2 or feat.get("sender_fan_out", 0.0) >= 2:
        mule_signal += 8.0
    if feat.get("network_cycle_detected", 0.0) == 1.0:
        mule_signal += 18.0
    if feat.get("sudden_in_out_surge", 0.0) == 1.0:
        mule_signal += 10.0

    # 7. Historical Context
    s_hist = feat.get("sender_behavioural_risk_score", 0.0)
    r_hist = feat.get("receiver_behavioural_risk_score", 0.0)
    hist_signal = (s_hist * 0.12) + (r_hist * 0.08)

    # Base baseline
    base = 5.0
    raw_score = base + amount_signal + bal_signal + time_signal + dev_loc_signal + beneficiary_signal + velocity_signal + mule_signal + hist_signal
    
    # Natural Gaussian jitter (+/- 1.5) to ensure smooth continuity
    noise = random.gauss(0, 1.2)
    final_score = round(max(2.0, min(98.5, raw_score + noise)), 1)
    return final_score


def generate_training_dataset(
    sample_limit: int = 24000,
    synthetic_ratio: float = 0.35,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generates training dataset (X, y) with continuous ground-truth risk scores [0.0, 100.0]
    extracted from real bank databases and augmented with diverse synthetic profiles.
    """
    conns = get_all_bank_connections()
    records = []
    targets = []

    per_bank_limit = min(sample_limit // max(len(conns), 1), 400)
    print(f"[DatasetGenerator] Extracting up to {per_bank_limit} sample transactions per bank database...")

    for bank, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        t.transaction_id, t.sender_account_id, t.receiver_account_id,
                        t.sender_bank, t.receiver_bank, t.amount, t.transaction_type,
                        t.transaction_timestamp, t.device_ip, t.location,
                        t.recipient_is_new,
                        COALESCE(ra.final_risk_score, 0.0) as sender_risk
                    FROM transactions t
                    LEFT JOIN risk_assessments ra
                        ON t.transaction_id = ra.transaction_id AND ra.role = 'SENDER'
                    ORDER BY t.transaction_timestamp DESC
                    LIMIT %s
                """, (per_bank_limit,))
                rows = cur.fetchall()

                for r in rows:
                    tx_id, s_acc, r_acc = r[0], r[1], r[2]
                    s_bank, r_bank = r[3] or bank, r[4] or bank
                    amt, tx_type = int(r[5]), r[6]
                    ts = r[7]
                    dev, loc = r[8] or "Mobile:192.168.1.1", r[9] or "Chennai"
                    is_new = bool(r[10])
                    s_risk = float(r[11] or 0.0)

                    feat_dict = extract_features_for_transaction(
                        conns=conns,
                        sender_bank=bank,
                        sender_account_id=s_acc,
                        receiver_bank=r_bank,
                        receiver_account_id=r_acc,
                        amount=amt,
                        tx_type=tx_type,
                        timestamp=ts,
                        device_ip=dev,
                        location=loc,
                        recipient_is_new=is_new,
                        sender_risk_score=s_risk,
                        receiver_risk_score=0.0,
                    )

                    score = compute_continuous_target(feat_dict)
                    records.append(features_to_vector(feat_dict))
                    targets.append(score)

        except Exception as e:
            print(f"  Warning: failed reading from {bank}: {e}")

    # Generate synthetic diverse profiles for balanced coverage across all 3 tiers
    num_synthetic = max(int(len(records) * synthetic_ratio), 6000)
    print(f"[DatasetGenerator] Generating {num_synthetic} balanced continuous synthetic examples...")
    syn_records, syn_targets = _generate_synthetic_continuous_examples(num_synthetic)

    records.extend(syn_records)
    targets.extend(syn_targets)

    df_X = pd.DataFrame(records, columns=FEATURE_NAMES)
    arr_y = np.array(targets, dtype=float)

    # Log tier distribution
    low_cnt = int(np.sum(arr_y <= 30.0))
    med_cnt = int(np.sum((arr_y > 30.0) & (arr_y <= 60.0)))
    high_cnt = int(np.sum(arr_y > 60.0))
    total = len(arr_y)

    print(f"[DatasetGenerator] Continuous Dataset Ready: {total} total samples.")
    print(f"   • LOW    (0-30)  : {low_cnt} ({low_cnt/total:.1%}) - avg: {np.mean(arr_y[arr_y <= 30.0]):.1f}")
    print(f"   • MEDIUM (31-60) : {med_cnt} ({med_cnt/total:.1%}) - avg: {np.mean(arr_y[(arr_y > 30.0) & (arr_y <= 60.0)]):.1f}")
    print(f"   • HIGH   (61-100): {high_cnt} ({high_cnt/total:.1%}) - avg: {np.mean(arr_y[arr_y > 60.0]):.1f}")

    return df_X, arr_y


def _generate_synthetic_continuous_examples(count: int) -> Tuple[List[List[float]], List[float]]:
    """
    Synthesizes rich, diverse transaction vectors covering:
    - Normal personal transactions (LOW)
    - High-value business transactions (LOW / expected)
    - Moderate borderline transactions (MEDIUM: new beneficiary, velocity bump, minor hour deviation)
    - Mule & hostile fraud transactions (HIGH: rapid forward, smurfing, fan-in, account drain)
    """
    syn_X = []
    syn_y = []

    for _ in range(count):
        roll = random.random()
        f = {fname: 0.0 for fname in FEATURE_NAMES}

        # 30% Genuine Business payments
        if roll < 0.30:
            is_biz = 1.0
            exp_vol = random.uniform(1500000, 8000000)
            amount = float(random.choice([45000, 80000, 150000, 280000, 450000, 750000]))
            balance = exp_vol * random.uniform(0.6, 2.0)
            hour = float(random.randint(9, 19))
            is_new_bene = 1.0 if random.random() < 0.12 else 0.0

            f["is_business"] = 1.0
            f["expected_turnover_or_volume"] = exp_vol
            f["amount"] = amount
            f["sender_balance"] = balance
            f["transfer_percentage_of_balance"] = round(amount / balance, 3)
            f["amount_vs_turnover_ratio"] = round(amount / exp_vol, 3)
            f["is_within_operating_hours"] = 1.0
            f["hour_of_day"] = hour
            f["is_night"] = 0.0
            f["is_unusual_hour"] = 0.0
            f["recipient_is_new"] = is_new_bene
            f["beneficiary_usage_frequency"] = 0.0 if is_new_bene else 2.0
            f["is_cross_bank"] = 1.0 if random.random() < 0.45 else 0.0
            f["tx_type_neft"] = 1.0 if amount >= 200000 else 0.0
            f["tx_type_imps"] = 1.0 if amount < 200000 else 0.0
            f["device_is_laptop"] = 1.0
            f["sender_avg_tx_amount"] = amount * random.uniform(0.7, 1.4)
            f["sender_max_tx_amount"] = amount * random.uniform(1.2, 2.5)
            f["sender_amount_vs_avg_ratio"] = round(amount / f["sender_avg_tx_amount"], 2)
            f["sender_amount_vs_max_ratio"] = round(amount / f["sender_max_tx_amount"], 2)
            f["sender_sent_count"] = float(random.randint(10, 40))
            f["sender_tx_1h"] = float(random.randint(0, 2))
            f["sender_tx_6h"] = float(random.randint(2, 8))
            f["sender_tx_24h"] = float(random.randint(5, 20))
            f["sender_burst_ratio"] = 1.0
            f["sender_velocity_ratio"] = 1.0
            f["sender_avg_interval_sec"] = float(random.randint(1800, 7200))
            f["sender_min_interval_sec"] = float(random.randint(600, 3600))
            f["sender_behavioural_risk_score"] = float(random.uniform(5.0, 22.0))

        # 35% Normal Personal transactions
        elif roll < 0.65:
            is_biz = 0.0
            exp_vol = random.uniform(30000, 120000)
            amount = float(random.choice([350, 750, 1500, 3200, 6500, 12000]))
            balance = exp_vol * random.uniform(0.4, 1.5)
            hour = float(random.randint(8, 22))
            is_new_bene = 1.0 if random.random() < 0.10 else 0.0

            f["is_business"] = 0.0
            f["expected_turnover_or_volume"] = exp_vol
            f["amount"] = amount
            f["sender_balance"] = balance
            f["transfer_percentage_of_balance"] = round(amount / balance, 3)
            f["amount_vs_turnover_ratio"] = round(amount / exp_vol, 3)
            f["is_within_operating_hours"] = 1.0
            f["hour_of_day"] = hour
            f["is_night"] = 0.0
            f["is_unusual_hour"] = 0.0
            f["recipient_is_new"] = is_new_bene
            f["beneficiary_usage_frequency"] = 0.0 if is_new_bene else 2.0
            f["is_cross_bank"] = 1.0 if random.random() < 0.3 else 0.0
            f["tx_type_upi"] = 1.0
            f["device_is_mobile"] = 1.0
            f["sender_avg_tx_amount"] = amount * random.uniform(0.8, 1.3)
            f["sender_max_tx_amount"] = amount * random.uniform(1.2, 3.0)
            f["sender_amount_vs_avg_ratio"] = round(amount / f["sender_avg_tx_amount"], 2)
            f["sender_amount_vs_max_ratio"] = round(amount / f["sender_max_tx_amount"], 2)
            f["sender_sent_count"] = float(random.randint(2, 8))
            f["sender_tx_1h"] = float(random.randint(0, 1))
            f["sender_tx_6h"] = float(random.randint(1, 3))
            f["sender_tx_24h"] = float(random.randint(2, 6))
            f["sender_burst_ratio"] = 1.0
            f["sender_velocity_ratio"] = 1.0
            f["sender_avg_interval_sec"] = float(random.randint(3600, 14400))
            f["sender_min_interval_sec"] = float(random.randint(1200, 7200))
            f["sender_behavioural_risk_score"] = float(random.uniform(4.0, 20.0))

        # 20% Medium-Risk Borderline Scenarios (Scores ~32 to 58)
        elif roll < 0.85:
            is_biz = 0.0
            exp_vol = random.uniform(40000, 100000)
            amount = float(random.choice([18000, 28000, 38000, 48000]))
            balance = exp_vol * random.uniform(0.7, 1.3)
            hour = float(random.randint(7, 23))

            variant = random.choice(["new_bene_mod_amt", "velocity_bump", "unusual_timing"])
            f["is_business"] = 0.0
            f["expected_turnover_or_volume"] = exp_vol
            f["amount"] = amount
            f["sender_balance"] = balance
            f["transfer_percentage_of_balance"] = round(amount / balance, 3)
            f["amount_vs_turnover_ratio"] = round(amount / exp_vol, 3)
            f["hour_of_day"] = hour
            f["tx_type_upi"] = 1.0
            f["device_is_mobile"] = 1.0
            f["sender_avg_tx_amount"] = amount * 0.45
            f["sender_max_tx_amount"] = amount * 1.1
            f["sender_amount_vs_avg_ratio"] = round(amount / f["sender_avg_tx_amount"], 2)

            if variant == "new_bene_mod_amt":
                f["recipient_is_new"] = 1.0
                f["beneficiary_usage_frequency"] = 0.0
                f["is_within_operating_hours"] = 1.0
                f["sender_tx_1h"] = float(random.randint(1, 2))
                f["sender_behavioural_risk_score"] = float(random.uniform(28.0, 42.0))
            elif variant == "velocity_bump":
                f["recipient_is_new"] = 0.0
                f["beneficiary_usage_frequency"] = 1.0
                f["sender_tx_1h"] = float(random.randint(3, 5))
                f["sender_tx_6h"] = float(random.randint(4, 8))
                f["sender_tx_24h"] = float(random.randint(6, 12))
                f["sender_burst_ratio"] = float(random.uniform(2.2, 3.8))
                f["sender_min_interval_sec"] = float(random.randint(80, 240))
                f["sender_behavioural_risk_score"] = float(random.uniform(35.0, 52.0))
            else:
                f["hour_of_day"] = float(random.choice([23, 0, 1, 5]))
                f["is_night"] = 1.0
                f["is_unusual_hour"] = 1.0
                f["sender_behavioural_risk_score"] = float(random.uniform(32.0, 48.0))

        # 15% High-Risk Mule & Fraud Patterns (Scores ~62 to 98)
        else:
            is_biz = 0.0
            exp_vol = random.uniform(30000, 90000)
            amount = float(random.choice([48000, 75000, 95000, 150000]))
            balance = max(amount * 1.1, 50000.0)

            pattern = random.choice(["rapid_forward", "smurfing", "fan_in_hub", "device_hijack"])
            f["is_business"] = 0.0
            f["expected_turnover_or_volume"] = exp_vol
            f["amount"] = amount
            f["sender_balance"] = balance
            f["transfer_percentage_of_balance"] = round(amount / balance, 3)
            f["amount_vs_turnover_ratio"] = round(amount / exp_vol, 3)
            f["recipient_is_new"] = 1.0
            f["beneficiary_usage_frequency"] = 0.0
            f["is_cross_bank"] = 1.0

            if pattern == "rapid_forward":
                f["network_rapid_forwarding"] = 1.0
                f["network_short_dwell_flag"] = 1.0
                f["sender_short_dwell_count"] = float(random.randint(2, 5))
                f["sender_forwarded_amount"] = amount * 0.95
                f["sender_min_interval_sec"] = float(random.randint(15, 60))
                f["sender_behavioural_risk_score"] = float(random.uniform(70.0, 92.0))
            elif pattern == "smurfing":
                f["amount"] = float(random.choice([49000, 49500, 49800, 9900]))
                f["network_amount_splitting"] = 1.0
                f["sender_amount_split_count"] = float(random.randint(2, 6))
                f["sender_tx_1h"] = float(random.randint(4, 8))
                f["sender_behavioural_risk_score"] = float(random.uniform(68.0, 88.0))
            elif pattern == "fan_in_hub":
                f["receiver_fan_in"] = float(random.randint(4, 12))
                f["receiver_unique_senders"] = float(random.randint(4, 10))
                f["receiver_tx_1h"] = float(random.randint(4, 10))
                f["receiver_behavioural_risk_score"] = float(random.uniform(72.0, 94.0))
            else:  # device hijack
                f["hour_of_day"] = float(random.choice([1, 2, 3, 4]))
                f["is_night"] = 1.0
                f["is_unusual_hour"] = 1.0
                f["is_new_device"] = 1.0
                f["sender_device_changes"] = float(random.randint(2, 4))
                f["is_location_deviation"] = 1.0
                f["sender_location_changes"] = float(random.randint(2, 4))
                f["device_location_anomaly"] = 1.0
                f["sender_amount_vs_avg_ratio"] = float(random.uniform(4.5, 9.0))
                f["sender_behavioural_risk_score"] = float(random.uniform(80.0, 96.0))

        score = compute_continuous_target(f)
        syn_X.append([float(f.get(fname, 0.0)) for fname in FEATURE_NAMES])
        syn_y.append(score)

    return syn_X, syn_y
