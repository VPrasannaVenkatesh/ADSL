"""
Dataset preparation module for Multi-Class XGBoost Transaction Risk Prediction.
Extracts historical transactions from bank PostgreSQL databases (SBI, AXIS, IOB),
derives rich behavioural features, and generates realistic 4-class labels:
  - Class 0: NORMAL (Legitimate everyday banking)
  - Class 1: SUSPICIOUS (Anomalous velocity, night activity, new beneficiary)
  - Class 2: MULE_FLOW (Rapid forwarding, structured smurfing, fan-in/fan-out hub)
  - Class 3: CRITICAL_FRAUD (Account drain, device hijack, hostile cyberfraud pattern)
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
from .config import FEATURE_NAMES, RISK_CLASSES, NUM_CLASSES
from .feature_extractor import extract_features_for_transaction, features_to_vector


def generate_training_dataset(
    sample_limit: int = 24000,
    synthetic_ratio: float = 0.25,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generates training dataset (X, y) from real DB transactions across banks
    augmented with synthetic topological patterns.
    Outputs:
        df_X: DataFrame of 44 engineered features
        arr_y: Integer array of 4 classes (0: NORMAL, 1: SUSPICIOUS, 2: MULE_FLOW, 3: CRITICAL_FRAUD)
    """
    conns = get_all_bank_connections()
    records = []
    labels = []

    per_bank_limit = max(sample_limit // max(len(conns), 1), 5000)
    print(f"[DatasetGenerator] Extracting up to {per_bank_limit} transactions per bank database...")

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
                    tx_id = r[0]
                    s_acc = r[1]
                    r_acc = r[2]
                    s_bank = r[3] or bank
                    r_bank = r[4] or bank
                    amt = int(r[5])
                    tx_type = r[6]
                    ts = r[7]
                    dev = r[8] or "Mobile:192.168.1.1"
                    loc = r[9] or "Chennai"
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

                    class_label = _determine_multi_class_label(feat_dict, s_risk)
                    records.append(features_to_vector(feat_dict))
                    labels.append(class_label)

        except Exception as e:
            print(f"  Warning: failed reading from {bank}: {e}")

    # Synthesize edge-case pattern transactions across all 4 categories for balanced training
    num_synthetic = max(int(len(records) * synthetic_ratio), 5000)
    print(f"[DatasetGenerator] Generating {num_synthetic} synthetic pattern examples for multi-class coverage...")
    syn_records, syn_labels = _generate_synthetic_pattern_examples(num_synthetic)

    records.extend(syn_records)
    labels.extend(syn_labels)

    df_X = pd.DataFrame(records, columns=FEATURE_NAMES)
    arr_y = np.array(labels, dtype=int)

    # Class distribution statistics
    counts = {RISK_CLASSES[i]: int(np.sum(arr_y == i)) for i in range(NUM_CLASSES)}
    print(f"[DatasetGenerator] Multi-Class Dataset Ready: {len(df_X)} total samples.")
    for cls_name, cnt in counts.items():
        print(f"   • {cls_name:15}: {cnt} samples ({cnt / len(df_X):.1%})")

    return df_X, arr_y


def _determine_multi_class_label(feat: Dict[str, float], s_risk: float) -> int:
    """
    Accurately maps feature patterns and behavioural metrics into 4 granular classes:
    0: NORMAL
    1: SUSPICIOUS
    2: MULE_FLOW
    3: CRITICAL_FRAUD
    """
    is_biz = feat.get("is_business", 0.0) == 1.0
    turnover_ratio = feat.get("amount_vs_turnover_ratio", 0.0)
    within_hours = feat.get("is_within_operating_hours", 1.0) == 1.0

    # Business account genuine context: Large transactions within normal business turnover & operating hours are NORMAL
    if is_biz and turnover_ratio <= 0.25 and within_hours and s_risk < 50.0:
        if not (feat.get("network_rapid_forwarding", 0) == 1.0 or feat.get("receiver_fan_in", 0) >= 4 or feat.get("sender_fan_out", 0) >= 4):
            return 0

    # 3: CRITICAL_FRAUD (Account drain, night heist, massive anomalous deviation, hostile device change)
    if (
        (feat.get("is_night", 0) == 1.0 and feat.get("amount", 0) >= 50000 and feat.get("recipient_is_new", 0) == 1.0)
        or (feat.get("sender_amount_vs_avg_ratio", 1.0) >= 5.0 and feat.get("amount", 0) >= 70000 and not is_biz)
        or (feat.get("sender_device_changes", 0) >= 2 and feat.get("sender_location_changes", 0) >= 2 and feat.get("amount", 0) >= 40000)
        or s_risk >= 85.0
    ):
        return 3

    # 2: MULE_FLOW (Structured mule network topology: rapid forwarding, smurfing, fan-in/fan-out hub)
    if (
        feat.get("network_rapid_forwarding", 0) == 1.0
        or feat.get("sender_short_dwell_count", 0) >= 2
        or feat.get("receiver_fan_in", 0) >= 3
        or feat.get("sender_fan_out", 0) >= 3
        or feat.get("sender_amount_split_count", 0) >= 2
        or feat.get("network_amount_splitting", 0) == 1.0
        or (feat.get("is_cross_bank", 0) == 1.0 and feat.get("network_short_dwell_flag", 0) == 1.0)
    ):
        return 2

    # 1: SUSPICIOUS (Behavioural anomalies: velocity surge, moderate risk score, new recipient)
    if (
        s_risk >= 50.0
        or feat.get("sender_behavioural_risk_score", 0.0) >= 50.0
        or feat.get("sender_tx_1h", 0) >= 4
        or feat.get("sender_velocity_ratio", 1.0) >= 2.5
        or (feat.get("recipient_is_new", 0) == 1.0 and feat.get("amount", 0) >= 30000 and not is_biz)
        or (feat.get("is_night", 0) == 1.0 and feat.get("amount", 0) >= 25000)
    ):
        return 1

    # 0: NORMAL
    return 0


def _generate_synthetic_pattern_examples(count: int) -> Tuple[List[List[float]], List[int]]:
    """
    Synthesizes targeted feature vectors covering all 4 risk classes with personal and business contexts.
    """
    syn_X = []
    syn_y = []

    for _ in range(count):
        # Roll for class type: 40% Normal, 25% Suspicious, 25% Mule Flow, 10% Critical Fraud
        roll = random.random()
        if roll < 0.40:
            target_class = 0
        elif roll < 0.65:
            target_class = 1
        elif roll < 0.90:
            target_class = 2
        else:
            target_class = 3

        # Realistic business vs personal distribution
        is_biz = 1.0 if random.random() < 0.35 else 0.0
        exp_vol = random.uniform(1500000, 8000000) if is_biz else random.uniform(30000, 150000)

        # Base vector with realistic normal values
        f = {fname: 0.0 for fname in FEATURE_NAMES}
        f["is_business"] = is_biz
        f["expected_turnover_or_volume"] = exp_vol
        f["is_within_operating_hours"] = 1.0
        f["hour_of_day"] = float(random.randint(9, 20))
        f["is_night"] = 0.0
        f["is_cross_bank"] = 1.0 if random.random() < 0.4 else 0.0
        f["recipient_is_new"] = 1.0 if random.random() < 0.15 else 0.0
        f["tx_type_upi"] = 1.0
        f["device_is_mobile"] = 1.0

        if is_biz:
            f["amount"] = float(random.choice([45000, 85000, 150000, 250000, 380000]))
            f["amount_vs_turnover_ratio"] = round(f["amount"] / exp_vol, 3)
            f["sender_avg_tx_amount"] = f["amount"] * random.uniform(0.7, 1.3)
            f["sender_max_tx_amount"] = f["amount"] * random.uniform(1.2, 2.5)
        else:
            f["amount"] = float(random.choice([500, 1200, 2500, 5000, 10000, 15000]))
            f["amount_vs_turnover_ratio"] = round(f["amount"] / exp_vol, 3)
            f["sender_avg_tx_amount"] = f["amount"] * random.uniform(0.8, 1.2)
            f["sender_max_tx_amount"] = f["amount"] * random.uniform(1.0, 2.0)

        f["sender_sent_count"] = float(random.randint(1, 5))
        f["sender_received_count"] = float(random.randint(1, 4))
        f["sender_tx_1h"] = float(random.randint(0, 2))
        f["sender_tx_6h"] = float(random.randint(1, 4))
        f["sender_tx_24h"] = float(random.randint(2, 6))
        f["sender_avg_interval_sec"] = float(random.randint(1800, 7200))
        f["sender_min_interval_sec"] = float(random.randint(600, 3600))
        f["sender_behavioural_risk_score"] = float(random.uniform(5.0, 25.0))
        f["sender_amount_vs_avg_ratio"] = 1.0
        f["sender_velocity_ratio"] = 1.0

        if target_class == 1:  # SUSPICIOUS
            variant = random.choice(["velocity", "amount_bump", "night_small"])
            if variant == "velocity":
                f["sender_tx_1h"] = float(random.randint(5, 9))
                f["sender_tx_24h"] = float(random.randint(12, 22))
                f["sender_avg_interval_sec"] = float(random.randint(45, 180))
                f["sender_velocity_ratio"] = float(random.uniform(2.5, 4.5))
                f["sender_behavioural_risk_score"] = float(random.uniform(52.0, 68.0))
            elif variant == "amount_bump":
                f["amount"] = float(random.randint(35000, 65000))
                f["recipient_is_new"] = 1.0
                f["sender_amount_vs_avg_ratio"] = float(random.uniform(2.8, 4.2))
                f["sender_behavioural_risk_score"] = float(random.uniform(55.0, 69.0))
            else:
                f["hour_of_day"] = float(random.choice([0, 1, 2, 3, 4]))
                f["is_night"] = 1.0
                f["amount"] = float(random.randint(25000, 45000))
                f["sender_behavioural_risk_score"] = float(random.uniform(50.0, 65.0))

        elif target_class == 2:  # MULE_FLOW
            pattern = random.choice(["rapid_forward", "fan_in", "fan_out", "structuring"])
            if pattern == "rapid_forward":
                f["amount"] = float(random.randint(45000, 95000))
                f["network_rapid_forwarding"] = 1.0
                f["network_short_dwell_flag"] = 1.0
                f["sender_short_dwell_count"] = float(random.randint(2, 5))
                f["sender_forwarded_amount"] = f["amount"] * 0.96
                f["sender_behavioural_risk_score"] = float(random.uniform(72.0, 92.0))
                f["sender_min_interval_sec"] = float(random.randint(10, 80))
                f["is_cross_bank"] = 1.0
            elif pattern == "fan_in":
                f["receiver_fan_in"] = float(random.randint(5, 14))
                f["receiver_received_count"] = float(random.randint(8, 22))
                f["receiver_unique_senders"] = float(random.randint(5, 12))
                f["receiver_tx_1h"] = float(random.randint(5, 12))
                f["receiver_behavioural_risk_score"] = float(random.uniform(76.0, 94.0))
                f["amount"] = float(random.randint(25000, 85000))
            elif pattern == "fan_out":
                f["sender_fan_out"] = float(random.randint(4, 10))
                f["sender_sent_count"] = float(random.randint(6, 16))
                f["sender_unique_recipients"] = float(random.randint(4, 10))
                f["sender_tx_1h"] = float(random.randint(4, 9))
                f["sender_behavioural_risk_score"] = float(random.uniform(70.0, 90.0))
            else:  # structuring
                f["amount"] = float(random.choice([48500, 49000, 49800, 9800, 9900]))
                f["sender_amount_split_count"] = float(random.randint(2, 5))
                f["network_amount_splitting"] = 1.0
                f["sender_tx_1h"] = float(random.randint(3, 7))
                f["sender_behavioural_risk_score"] = float(random.uniform(68.0, 86.0))

        elif target_class == 3:  # CRITICAL_FRAUD
            f["amount"] = float(random.randint(75000, 200000))
            f["hour_of_day"] = float(random.choice([1, 2, 3, 4]))
            f["is_night"] = 1.0
            f["recipient_is_new"] = 1.0
            f["sender_device_changes"] = float(random.randint(2, 4))
            f["sender_location_changes"] = float(random.randint(2, 4))
            f["sender_amount_vs_avg_ratio"] = float(random.uniform(5.5, 12.0))
            f["sender_behavioural_risk_score"] = float(random.uniform(86.0, 98.0))

        syn_X.append([f.get(fname, 0.0) for fname in FEATURE_NAMES])
        syn_y.append(target_class)

    return syn_X, syn_y
