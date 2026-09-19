"""
Executes an end-to-end Multi-Mule Layered Sink Topology in ADSL:
1. Source Account -> Multiple Intermediate Mule Accounts (Dispersion / Smurfing).
2. Multiple Intermediate Mule Accounts -> Single Sink Account (Funneling / Sinking).
3. Full real-time XGBoost ML Risk Scoring, Behavioural History update,
   Decentralized Coordinator Consensus, and Network Lien Layer evaluation.
"""

import sys
import os
import json
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator.engine import LiveTransactionSimulator
from simulator.config import SimulatorConfig

def main():
    print("=" * 80)
    print("  ADSL MULTI-MULE TO SINK ACCOUNT TRANSACTION EXECUTION")
    print("  Pattern Topology: Source -> [Multiple Mules] -> Sink Account")
    print("=" * 80)

    config = SimulatorConfig(mode="normal", custom_delay=0.1)
    engine = LiveTransactionSimulator(config=config)

    print("\n[1] Initializing Multi-Bank Ledger & Accounts...")
    print(f"  Connected Banks: SBI, AXIS, IOB")

    print("\n[2] Triggering Multi-Mule Dispersion & Sink Transaction Flow (Total: ₹75,000)...")
    res = engine.execute_mule_sink_flow(total_amount=75000)

    print("\n" + "-" * 80)
    print("  FLOW EXECUTION SUMMARY")
    print("-" * 80)
    print(f"  Topology           : {res['topology']}")
    print(f"  Source Account     : {res['source_account']}")
    print(f"  Intermediate Mules : {', '.join(res['intermediate_mules'])}")
    print(f"  Sink Account       : {res['sink_account']}")
    print(f"  Total Dispersed    : ₹{res['total_dispersed']:,}")
    print(f"  Total Sunk         : ₹{res['total_sunk']:,}")
    print(f"  Total Transactions : {res['total_transactions_executed']}")

    print("\n" + "=" * 80)
    print("  STAGE 1: DISPERSION / SMURFING (Source -> Intermediate Mules)")
    print("=" * 80)
    for i, tx in enumerate(res["stage_1_dispersion"], 1):
        print(f"  [Txn 1.{i}] ID: {tx['transaction_id']}")
        print(f"          Flow    : {tx['sender']}  -->  {tx['receiver']}")
        print(f"          Amount  : ₹{tx['amount']:,}")
        print(f"          XGB Risk: {tx['xgboost_risk_score']:.1f} / 100")
        print(f"          Status  : {tx['status']}")
        print(f"          Time    : {tx['timestamp']}")
        print()

    print("=" * 80)
    print("  STAGE 2: SINK CONSOLIDATION (Intermediate Mules -> Sink Account)")
    print("=" * 80)
    for i, tx in enumerate(res["stage_2_sink"], 1):
        print(f"  [Txn 2.{i}] ID: {tx['transaction_id']}")
        print(f"          Flow    : {tx['sender']}  -->  {tx['receiver']} (SINK)")
        print(f"          Amount  : ₹{tx['amount']:,}")
        print(f"          XGB Risk: {tx['xgboost_risk_score']:.1f} / 100")
        print(f"          Status  : {tx['status']}")
        print(f"          Time    : {tx['timestamp']}")
        print()

    print("=" * 80)
    print("  MULE & SINK FLOW COMPLETED SUCCESSFULLY")
    print("  All transactions are recorded in PostgreSQL and viewable across all dashboards!")
    print("  - Simulator Feed      : http://localhost:5173/")
    print("  - Risk Dashboard      : http://localhost:5174/")
    print("  - Coordinator Monitor : http://localhost:5175/")
    print("=" * 80)

if __name__ == "__main__":
    main()
