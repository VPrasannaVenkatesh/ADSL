"""
Account cache and selection manager for realistic multi-bank simulation.
"""

import random
from typing import Dict, List, Optional, Tuple
import psycopg2
from .config import BANK_NAMES, LOCATIONS, DEVICE_TYPES


class AccountManager:
    def __init__(self, conns: Dict[str, psycopg2.extensions.connection]):
        self.conns = conns
        # Cache of accounts by bank: { "SBI": [ {...}, ... ], "AXIS": [...], "IOB": [...] }
        self.accounts_by_bank: Dict[str, List[dict]] = {bank: [] for bank in BANK_NAMES}
        # Fast lookup by account_id: { "SBI-A0001": {...}, ... }
        self.accounts_by_id: Dict[str, dict] = {}
        # Track persistent primary device & IP per account for realistic behavioral consistency
        self.account_device_cache: Dict[str, str] = {}
        # Track accounts that recently received money for natural rapid forwarding chains
        self.recent_recipients: List[Tuple[str, int]] = []  # [(account_id, amount_received)]
        self.load_accounts()

    def load_accounts(self):
        """Loads all accounts from the 3 databases into memory."""
        self.accounts_by_id.clear()
        for bank in BANK_NAMES:
            self.accounts_by_bank[bank].clear()
            conn = self.conns[bank]
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, account_number, customer_name,
                           account_type, current_balance, home_location,
                           account_created_date
                    FROM accounts
                    WHERE account_status = 'ACTIVE'
                    ORDER BY account_id
                """)
                rows = cur.fetchall()
                for r in rows:
                    acc = {
                        "account_id": r[0],
                        "account_number": r[1],
                        "customer_name": r[2],
                        "account_type": r[3],
                        "current_balance": int(r[4]),
                        "home_location": r[5] or random.choice(LOCATIONS),
                        "account_created_date": r[6],
                        "bank": bank,
                    }
                    self.accounts_by_bank[bank].append(acc)
                    self.accounts_by_id[acc["account_id"]] = acc

                    # Assign a realistic default device & synthetic IP
                    dev_type = random.choices(
                        DEVICE_TYPES, weights=[0.70, 0.15, 0.10, 0.05], k=1
                    )[0]
                    ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                    self.account_device_cache[acc["account_id"]] = f"{dev_type}:{ip}"

    def update_balance_cache(self, account_id: str, new_balance: int):
        """Updates the cached balance for an account."""
        if account_id in self.accounts_by_id:
            self.accounts_by_id[account_id]["current_balance"] = int(new_balance)

    def record_recent_recipient(self, account_id: str, amount: int):
        """Records a recent recipient to enable natural multi-step fund movements."""
        self.recent_recipients.append((account_id, amount))
        if len(self.recent_recipients) > 50:
            self.recent_recipients.pop(0)

    def get_account_device(self, account_id: str, allow_device_switch: bool = False) -> str:
        """
        Returns device_ip string ('Device:IP').
        Maintains consistency for the account with occasional realistic switches.
        """
        current = self.account_device_cache.get(account_id)
        if not current:
            dev_type = random.choice(DEVICE_TYPES)
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            current = f"{dev_type}:{ip}"
            self.account_device_cache[account_id] = current

        if allow_device_switch and random.random() < 0.08:
            dev_type = random.choice(DEVICE_TYPES)
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            return f"{dev_type}:{ip}"

        return current

    def get_account_location(self, account: dict, allow_location_switch: bool = False) -> str:
        """
        Returns transaction location.
        Usually matches home_location with realistic travel/cross-city mobility.
        """
        home = account.get("home_location") or "Chennai"
        if allow_location_switch and random.random() < 0.12:
            return random.choice(LOCATIONS)
        return home

    def select_sender_and_receiver(
        self,
        sender_bank: Optional[str] = None,
        receiver_bank: Optional[str] = None,
        is_forwarding_attempt: bool = False,
    ) -> Optional[Tuple[dict, dict]]:
        """
        Selects a valid sender and receiver account ensuring:
        - Sender has available positive balance (>= 100).
        - Sender and Receiver are distinct accounts.
        - Respects specified sender_bank and receiver_bank if provided.
        """
        sender = None

        # Natural rapid forwarding check
        if is_forwarding_attempt and self.recent_recipients and random.random() < 0.6:
            recent_id, _ = random.choice(self.recent_recipients)
            cand = self.accounts_by_id.get(recent_id)
            if cand and cand["current_balance"] >= 100:
                if sender_bank is None or cand["bank"] == sender_bank:
                    sender = cand

        if not sender:
            # Select sender bank
            s_bank = sender_bank if sender_bank else random.choice(BANK_NAMES)
            eligible_senders = [
                a for a in self.accounts_by_bank[s_bank]
                if a["current_balance"] >= 100
            ]
            if not eligible_senders:
                # Try any bank
                all_eligible = [
                    a for a in self.accounts_by_id.values()
                    if a["current_balance"] >= 100
                ]
                if not all_eligible:
                    return None
                sender = random.choice(all_eligible)
            else:
                sender = random.choice(eligible_senders)

        # Select receiver bank
        r_bank = receiver_bank if receiver_bank else random.choice(BANK_NAMES)
        eligible_receivers = [
            a for a in self.accounts_by_bank[r_bank]
            if a["account_id"] != sender["account_id"]
        ]
        if not eligible_receivers:
            eligible_receivers = [
                a for a in self.accounts_by_id.values()
                if a["account_id"] != sender["account_id"]
            ]
            if not eligible_receivers:
                return None

        receiver = random.choice(eligible_receivers)
        return sender, receiver

    def check_recipient_is_new(self, sender_id: str, receiver_id: str, sender_bank: str) -> bool:
        """
        Checks the sender bank's transaction history to see if sender has ever sent to receiver.
        """
        conn = self.conns[sender_bank]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM transactions
                WHERE sender_account_id = %s AND receiver_account_id = %s
                LIMIT 1
            """, (sender_id, receiver_id))
            return cur.fetchone() is None
