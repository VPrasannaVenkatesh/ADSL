"""
Comprehensive Multi-Manner Transaction & Behaviour Generator.
Generates balanced, high-fidelity banking transactions across:
1. Everyday Normal Personal Banking (UPI, IMPS, NEFT, bills)
2. Commercial Corporate B2B Settlements & Payrolls
3. Financial Crime & Mule Topologies (Fan-In, Fan-Out, Multi-Hop, Circular, Mule-to-Genuine)
"""

import os
import sys
import random
import time
from datetime import datetime, timedelta
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.config import SimulatorConfig, BANK_NAMES, TX_TYPES, LOCATIONS, DEVICE_TYPES
from simulator.engine import LiveTransactionSimulator
from simulator.db_connection import get_bank_connection
from risk_engine.aggregator import run_risk_assessment, score_to_level
from risk_engine.storage import store_risk_assessment
from risk_engine.feature_extractor import extract_account_features
from simulator.behaviour_history_updater import update_daily_account_behaviour
from network_monitoring.lien_layer import GLOBAL_LIEN_LAYER
from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT


def run_comprehensive_generation(batch_count=1500):
    print("=" * 70)
    print("BANKING PLATFORM: COMPREHENSIVE MULTI-MANNER TRANSACTION ENGINE")
    print(f"Target Batch: {batch_count} transactions across SBI, AXIS, and IOB")
    print("=" * 70)

    # 1. Initialize Simulator with balanced mix mode
    config = SimulatorConfig(mode="normal", total_count=0, mix_mode="balanced")
    sim = LiveTransactionSimulator(config)

    # Reload account pools to ensure newly added accounts (601 to 1000) are included
    sim.account_mgr.load_accounts()
    sim.normal_gen.accounts_by_bank = sim.account_mgr.accounts_by_bank
    sim.normal_gen.accounts_by_id = sim.account_mgr.accounts_by_id
    sim.patterns.clusters = sim.patterns._initialize_clusters()

    total_accs = sum(len(accs) for accs in sim.account_mgr.accounts_by_bank.values())
    print(f"[INIT] Loaded {total_accs} active accounts across SBI, AXIS, IOB.")

    categories = {
        "NORMAL_PERSONAL": 0,
        "BUSINESS_COMMERCIAL": 0,
        "FAN_IN_SMURF": 0,
        "FAN_OUT_DISPERSE": 0,
        "MULTI_HOP_CHAIN": 0,
        "CIRCULAR_WASH": 0,
        "MULE_TO_GENUINE": 0,
    }

    start_time = time.time()
    successful = 0

    # Ensure pattern queue has pre-queued topologies
    base_time = datetime.now()
    for _ in range(15):
        sim.patterns.trigger_pattern_sequence(base_time)

    for i in range(1, batch_count + 1):
        # Rotate mix mode to ensure even representation of all manners
        if i % 10 in (0, 1, 2, 3):
            sim.config.mix_mode = "balanced"
        elif i % 10 in (4, 5):
            sim.config.mix_mode = "business"
        elif i % 10 in (6, 7):
            sim.config.mix_mode = "mule"
        else:
            sim.config.mix_mode = "normal"

        # Explicitly inject Mule-to-Genuine scenario every 30 transactions
        if i % 30 == 0:
            mule_accs = [a for a in sim.account_mgr.accounts_by_bank["SBI"] if "001" in a["account_id"] or "002" in a["account_id"]]
            genuine_biz = [a for a in sim.account_mgr.accounts_by_bank["AXIS"] if a.get("account_classification") == "BUSINESS" or a["current_balance"] > 500000]
            if mule_accs and genuine_biz:
                s_node = random.choice(mule_accs)
                r_node = random.choice(genuine_biz)
                amt = random.randint(45000, 350000)
                if s_node["current_balance"] >= amt:
                    res = sim.processor.execute_transaction(
                        sender=s_node,
                        receiver=r_node,
                        amount=amt,
                        tx_type="IMPS",
                        timestamp=datetime.now(),
                        device_ip=f"Mobile:10.0.{random.randint(1,250)}.{random.randint(1,250)}",
                        location="Mumbai",
                        recipient_is_new=True,
                    )
                    if res:
                        sim._record_result(res, is_pattern=True, is_business=False)
                        categories["MULE_TO_GENUINE"] += 1
                        successful += 1
                        continue

        # Standard step
        res = sim.simulate_single_transaction()
        if res:
            successful += 1
            if getattr(res, "is_cross_bank", False):
                categories["MULTI_HOP_CHAIN"] += 1
            else:
                categories["NORMAL_PERSONAL"] += 1

        if i % 250 == 0:
            elapsed = time.time() - start_time
            print(f"[{i}/{batch_count}] Generated {successful} valid transactions ({elapsed:.1f}s)...")

    # Update summary counts from databases
    print("\n" + "=" * 70)
    print("FINAL DATABASE HEALTH & RISK ASSESSMENT AUDIT")
    print("=" * 70)

    for bank in BANK_NAMES:
        conn = get_bank_connection(bank)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM transactions")
        total_txs = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM accounts")
        total_accs = cur.fetchone()[0]
        cur.execute("SELECT risk_level, count(*) FROM risk_assessments GROUP BY risk_level")
        risk_dist = cur.fetchall()
        cur.execute("SELECT count(*) FROM transactions WHERE lien_status = 'LIEN_APPLIED'")
        lien_count = cur.fetchone()[0]

        print(f"\n[{bank} Core Banking Ledger]")
        print(f"  * Accounts in Registry    : {total_accs:,}")
        print(f"  * Completed Transactions  : {total_txs:,}")
        print(f"  * Active Protective Liens : {lien_count:,}")
        print(f"  * Behavioural Risk Levels :")
        for lvl, cnt in risk_dist:
            print(f"      - {lvl:<8}: {cnt:,}")
        cur.close()
        conn.close()

    print("\n" + "=" * 70)
    print("COMPREHENSIVE TRANSACTION GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    count = 1500
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    run_comprehensive_generation(batch_count=count)
