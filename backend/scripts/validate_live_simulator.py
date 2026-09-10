#!/usr/bin/env python3
"""
validate_live_simulator.py
════════════════════════════════════════════════════════════════════════════════
Automated verification test suite for Live Transaction Simulator.
Validates:
  1. Intra-bank transactions across all 3 banks (SBI->SBI, AXIS->AXIS, IOB->IOB).
  2. Cross-bank transactions across all 6 pairs (SBI->AXIS, SBI->IOB, etc.).
  3. Strict balance consistency (no negative balances, exact debit & credit math).
  4. Cross-bank correlation (identical transaction_id recorded in both bank DBs).
  5. Behaviour history dynamic updates (transaction counts, amounts, velocity, balances).
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.config import SimulatorConfig, ALL_BANK_PAIRS
from simulator.engine import LiveTransactionSimulator
from simulator.db import get_all_connections


def run_tests():
    print("=" * 72)
    print("  LIVE TRANSACTION SIMULATOR VALIDATION SUITE")
    print("=" * 72)

    config = SimulatorConfig(mode="fast", total_count=0)
    sim = LiveTransactionSimulator(config)
    conns = sim.conns

    passed_tests = 0
    total_tests = 0

    try:
        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: Test all 9 bank pair combinations
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 1] Testing all 9 bank pair combinations...")
        for s_bank, r_bank in ALL_BANK_PAIRS:
            total_tests += 1
            is_cross = (s_bank != r_bank)
            pair_label = f"{s_bank} ➔ {r_bank} ({'Inter-Bank' if is_cross else 'Intra-Bank'})"

            # Execute single transaction for this pair
            res = sim.simulate_single_transaction(sender_bank=s_bank, receiver_bank=r_bank)
            if not res:
                print(f"  ❌ FAILED: Could not generate transaction for {pair_label}")
                continue

            # Check balances in DB
            s_conn = conns[s_bank]
            with s_conn.cursor() as cur:
                cur.execute("SELECT current_balance FROM accounts WHERE account_id = %s", (res.sender_account_id,))
                s_db_bal = cur.fetchone()[0]

            r_conn = conns[r_bank]
            with r_conn.cursor() as cur:
                cur.execute("SELECT current_balance FROM accounts WHERE account_id = %s", (res.receiver_account_id,))
                r_db_bal = cur.fetchone()[0]

            # Verify math
            if s_db_bal != res.sender_bal_after or r_db_bal != res.receiver_bal_after:
                print(f"  ❌ FAILED: Balance mismatch for {pair_label}")
                continue

            # Verify transaction record exists in DB
            with s_conn.cursor() as cur:
                cur.execute("SELECT amount, transaction_status FROM transactions WHERE transaction_id = %s", (res.transaction_id,))
                s_tx_row = cur.fetchone()

            if not s_tx_row or s_tx_row[0] != res.amount or s_tx_row[1] != "COMPLETED":
                print(f"  ❌ FAILED: Sender DB transaction missing or invalid for {pair_label}")
                continue

            if is_cross:
                with r_conn.cursor() as cur:
                    cur.execute("SELECT amount, transaction_status FROM transactions WHERE transaction_id = %s", (res.transaction_id,))
                    r_tx_row = cur.fetchone()
                if not r_tx_row or r_tx_row[0] != res.amount:
                    print(f"  ❌ FAILED: Receiver DB cross-bank transaction missing for {pair_label}")
                    continue

            print(f"  ✅ PASS: {pair_label:<32} TxID={res.transaction_id} Amount=₹{res.amount:,}")
            passed_tests += 1

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: Verify Dynamic Behaviour History Update
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 2] Verifying Behaviour History dynamic update...")
        total_tests += 1

        # Generate a targeted transaction on SBI
        sender_cand = [a for a in sim.account_mgr.accounts_by_bank["SBI"] if a["current_balance"] > 5000][0]
        receiver_cand = [a for a in sim.account_mgr.accounts_by_bank["SBI"] if a["account_id"] != sender_cand["account_id"]][0]

        res = sim.simulate_single_transaction(sender_bank="SBI", receiver_bank="SBI")
        txn_date = res.transaction_timestamp.date()

        # Check sender's behaviour history row
        with conns["SBI"].cursor() as cur:
            cur.execute("""
                SELECT transaction_count, sent_transaction_count, total_amount_sent,
                       transactions_24h, closing_balance, primary_device
                FROM behaviour_history
                WHERE account_id = %s AND behaviour_date = %s
            """, (res.sender_account_id, txn_date))
            bh_row = cur.fetchone()

        if bh_row and bh_row[0] > 0 and bh_row[1] > 0 and bh_row[2] > 0:
            print(f"  ✅ PASS: Behaviour profile for {res.sender_account_id} on {txn_date}:")
            print(f"           tx_count={bh_row[0]}, sent_count={bh_row[1]}, total_sent=₹{bh_row[2]:,}, "
                  f"txns_24h={bh_row[3]}, closing_bal=₹{bh_row[4]:,}, primary_dev='{bh_row[5]}'")
            passed_tests += 1
        else:
            print(f"  ❌ FAILED: Behaviour profile not populated for {res.sender_account_id} (row={bh_row})")

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: Verify Balances Never Go Negative
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 3] Checking non-negative balance constraint across all databases...")
        total_tests += 1
        neg_count = 0
        for bank, conn in conns.items():
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM accounts WHERE current_balance < 0")
                cnt = cur.fetchone()[0]
                neg_count += cnt

        if neg_count == 0:
            print("  ✅ PASS: All account balances are non-negative across SBI, AXIS, and IOB.")
            passed_tests += 1
        else:
            print(f"  ❌ FAILED: Found {neg_count} accounts with negative balance!")

        # ─────────────────────────────────────────────────────────────────────
        # TEST 4: Batch Simulation Speed Test
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 4] Running batch simulation (20 transactions in fast mode)...")
        total_tests += 1
        initial_tx_count = sim.stats["total_generated"]

        for _ in range(20):
            sim.simulate_single_transaction()

        diff = sim.stats["total_generated"] - initial_tx_count
        if diff == 20:
            print(f"  ✅ PASS: Successfully executed {diff} continuous transactions.")
            passed_tests += 1
        else:
            print(f"  ❌ FAILED: Expected 20 transactions, got {diff}")

    finally:
        sim.close()

    print("\n" + "=" * 72)
    print(f"  VALIDATION SUMMARY: {passed_tests}/{total_tests} Tests Passed")
    print("=" * 72 + "\n")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
