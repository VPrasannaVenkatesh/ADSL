#!/usr/bin/env python3
"""
Live Transaction Simulator CLI
════════════════════════════════════════════════════════════════════════════════
Generates realistic multi-bank transactions between SBI, AXIS, and IOB accounts.
Simulates normal transactions and concurrent connected network patterns simultaneously.
Updates PostgreSQL accounts, transactions, and behaviour_history tables dynamically.

Usage:
  python scripts/live_transaction_simulator.py
  python scripts/live_transaction_simulator.py --speed slow
  python scripts/live_transaction_simulator.py --speed fast --count 50
  python scripts/live_transaction_simulator.py --speed normal
"""

import os
import sys
import signal
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.transaction_engine import TransactionSimulationEngine, SPEED_SETTINGS
from simulator.balance_manager import TransactionRecord

# Clean terminal formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def format_inr(amount: int) -> str:
    """Formats amount as Indian Rupee string."""
    return f"₹{amount:,.0f}"


def print_banner(engine: TransactionSimulationEngine, speed: str, count: int):
    speed_info = SPEED_SETTINGS[speed]
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║               MULTI-BANK LIVE TRANSACTION SIMULATOR                          ║{RESET}")
    print(f"{CYAN}{BOLD}║         Databases: sbi_db (SBI) │ axis_db (AXIS) │ iob_db (IOB)              ║{RESET}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {BOLD}Simulation Speed :{RESET} {speed.upper()} ({speed_info['delay']}s delay per transaction)")
    print(f"  {BOLD}Execution Mode   :{RESET} {'Continuous (Press Ctrl+C to Stop)' if count == 0 else f'{count} transactions target'}")
    print(f"  {BOLD}Simulation Clock :{RESET} Starting at {engine.sim_clock.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {BOLD}Active Accounts  :{RESET} {len(engine.accounts_by_id):,} accounts across 3 banks\n")
    print(f"{DIM}{'─' * 82}{RESET}")


def on_transaction(rec: TransactionRecord, stats: dict):
    tx_num = stats["total_generated"]
    pair_badge = f"{rec.sender_bank} ➔ {rec.receiver_bank}"
    if rec.is_cross_bank:
        badge_colored = f"{MAGENTA}[INTER-BANK {pair_badge}]{RESET}"
    else:
        badge_colored = f"{GREEN}[INTRA-BANK {pair_badge}]{RESET}"

    new_flag = f"{YELLOW}[NEW_RECIP]{RESET}" if rec.recipient_is_new else ""

    print(
        f"{DIM}#{tx_num:05d}{RESET} {BOLD}{rec.transaction_id}{RESET} {badge_colored} {new_flag}\n"
        f"       {BLUE}Sender  :{RESET} {rec.sender_bank:<4} {rec.sender_account_id} "
        f"{DIM}(Bal: {format_inr(rec.sender_bal_before)} ➔ {format_inr(rec.sender_bal_after)}){RESET}\n"
        f"       {GREEN}Receiver:{RESET} {rec.receiver_bank:<4} {rec.receiver_account_id} "
        f"{DIM}(Bal: {format_inr(rec.receiver_bal_before)} ➔ {format_inr(rec.receiver_bal_after)}){RESET}\n"
        f"       {YELLOW}Details :{RESET} {BOLD}{format_inr(rec.amount):<10}{RESET} "
        f"Type: {rec.transaction_type:<13} "
        f"Time: {rec.transaction_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"       {DIM}Channel :{RESET} Device: {rec.device_ip:<24} Location: {rec.location}\n"
        f"{DIM}{'─' * 82}{RESET}"
    )


def print_summary(stats: dict, start_time: datetime):
    duration = (datetime.now() - start_time).total_seconds()
    print(f"\n{CYAN}{BOLD}════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{CYAN}{BOLD}                        SIMULATION SESSION SUMMARY                              {RESET}")
    print(f"{CYAN}{BOLD}════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {BOLD}Total Transactions :{RESET} {stats['total_generated']:,}")
    print(f"  {BOLD}Intra-Bank (Same)  :{RESET} {stats['intra_bank']:,}")
    print(f"  {BOLD}Inter-Bank (Cross) :{RESET} {stats['cross_bank']:,}")
    print(f"  {BOLD}Total Volume Moved :{RESET} {format_inr(stats['total_volume'])}")
    print(f"  {BOLD}Patterns Triggered :{RESET} {stats['patterns_triggered']:,}")
    print(f"  {BOLD}Session Duration   :{RESET} {duration:.1f}s")
    if duration > 0:
        print(f"  {BOLD}Throughput Rate    :{RESET} {stats['total_generated'] / duration:.2f} tx/sec")
    print(f"{CYAN}{BOLD}════════════════════════════════════════════════════════════════════════════════{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Multi-Bank Live Transaction Simulator (SBI, AXIS, IOB)")
    parser.add_argument(
        "--speed",
        choices=["slow", "normal", "fast"],
        default="normal",
        help="Simulation speed preset (default: normal)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of transactions to generate (default: 0 = continuous until Ctrl+C)",
    )

    args = parser.parse_args()
    engine = TransactionSimulationEngine(speed=args.speed)

    def sig_handler(sig, frame):
        print(f"\n{YELLOW}Stopping simulator gracefully... Please wait.{RESET}")
        engine.is_running = False

    signal.signal(signal.SIGINT, sig_handler)

    print_banner(engine, args.speed, args.count)
    start_time = datetime.now()

    try:
        engine.run_loop(total_count=args.count, on_record=on_transaction)
    finally:
        print_summary(engine.stats, start_time)
        engine.close()


if __name__ == "__main__":
    main()
