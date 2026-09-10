"""
Normal routine & business transaction generator for multi-bank simulation.
Generates genuine consumer and commercial transactions across SBI, AXIS, and IOB.
"""

import random
from typing import Dict, List, Optional, Tuple

BANK_NAMES = ["SBI", "AXIS", "IOB"]
ALL_BANK_PAIRS = [
    ("SBI", "SBI"), ("SBI", "AXIS"), ("SBI", "IOB"),
    ("AXIS", "SBI"), ("AXIS", "AXIS"), ("AXIS", "IOB"),
    ("IOB", "SBI"), ("IOB", "AXIS"), ("IOB", "IOB"),
]
TX_TYPES = ["UPI", "IMPS", "NEFT", "BANK_TRANSFER"]
DEVICE_TYPES = ["Mobile", "Desktop", "Laptop", "Tablet"]
LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur",
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]


class NormalTransactionGenerator:
    """
    Handles regular everyday personal and business banking transactions.
    Supports distinct characteristics for Personal vs Business accounts.
    """

    def __init__(self, accounts_by_bank: Dict[str, List[dict]], accounts_by_id: Dict[str, dict]):
        self.accounts_by_bank = accounts_by_bank
        self.accounts_by_id = accounts_by_id
        self.account_device_cache: Dict[str, str] = {}
        self._init_device_cache()

    def _init_device_cache(self):
        for acc_id, acc in self.accounts_by_id.items():
            is_biz = acc.get("account_type") == "BUSINESS"
            if is_biz:
                dev = random.choices(DEVICE_TYPES, weights=[0.25, 0.45, 0.25, 0.05], k=1)[0]
            else:
                dev = random.choices(DEVICE_TYPES, weights=[0.75, 0.12, 0.09, 0.04], k=1)[0]
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            self.account_device_cache[acc_id] = f"{dev}:{ip}"

    def get_device(self, account_id: str) -> str:
        dev = self.account_device_cache.get(account_id)
        if not dev:
            dev_type = random.choice(DEVICE_TYPES)
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            dev = f"{dev_type}:{ip}"
            self.account_device_cache[account_id] = dev

        if random.random() < 0.06:
            dev_type = random.choice(DEVICE_TYPES)
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            return f"{dev_type}:{ip}"
        return dev

    def get_location(self, account: dict) -> str:
        home = account.get("home_location") or "Chennai"
        if random.random() < 0.08:
            return random.choice(LOCATIONS)
        return home

    def generate_amount(self, tx_type: str, sender_balance: int, is_business: bool = False) -> int:
        """
        Generates realistic amount based on payment channel and account type.
        Business accounts support significantly higher legitimate amounts (B2B, payroll, supplier).
        """
        max_possible = max(100, int(sender_balance * 0.92))

        if is_business:
            if tx_type == "NEFT":
                amt = random.choices(
                    [
                        random.randint(50000, 250000),      # Small vendor
                        random.randint(250000, 1000000),    # Bulk supplier / inventory
                        random.randint(1000000, 3500000),   # Corporate settlement
                    ],
                    weights=[0.45, 0.40, 0.15],
                    k=1
                )[0]
            elif tx_type == "BANK_TRANSFER":
                amt = random.choices(
                    [
                        random.randint(30000, 150000),     # Salary / operational
                        random.randint(150000, 600000),    # Commercial contract
                        random.randint(600000, 2000000),   # B2B transfer
                    ],
                    weights=[0.40, 0.45, 0.15],
                    k=1
                )[0]
            elif tx_type == "IMPS":
                amt = random.choices(
                    [
                        random.randint(10000, 50000),
                        random.randint(50000, 200000),
                        random.randint(200000, 500000),
                    ],
                    weights=[0.50, 0.35, 0.15],
                    k=1
                )[0]
            else:  # UPI merchant collections
                amt = random.choices(
                    [
                        random.randint(1000, 15000),
                        random.randint(15000, 50000),
                        random.randint(50000, 100000),
                    ],
                    weights=[0.55, 0.35, 0.10],
                    k=1
                )[0]
        else:
            if tx_type == "UPI":
                amt = random.choices(
                    [
                        random.randint(100, 1500),      # Coffee, grocery, retail
                        random.randint(1500, 6000),     # Shopping, dining
                        random.randint(6000, 20000),    # Personal transfer
                        random.randint(20000, 50000),   # Rent, tuition
                    ],
                    weights=[0.55, 0.28, 0.13, 0.04],
                    k=1
                )[0]
            elif tx_type == "IMPS":
                amt = random.choices(
                    [
                        random.randint(500, 5000),
                        random.randint(5000, 25000),
                        random.randint(25000, 80000),
                    ],
                    weights=[0.45, 0.40, 0.15],
                    k=1
                )[0]
            elif tx_type == "NEFT":
                amt = random.choices(
                    [
                        random.randint(5000, 35000),
                        random.randint(35000, 120000),
                        random.randint(120000, 300000),
                    ],
                    weights=[0.45, 0.40, 0.15],
                    k=1
                )[0]
            else:  # BANK_TRANSFER
                amt = random.choices(
                    [
                        random.randint(2000, 20000),
                        random.randint(20000, 75000),
                        random.randint(75000, 200000),
                    ],
                    weights=[0.45, 0.40, 0.15],
                    k=1
                )[0]

        return max(100, min(amt, max_possible))

    def select_accounts(
        self,
        sender_bank: Optional[str] = None,
        receiver_bank: Optional[str] = None,
        require_business: bool = False,
    ) -> Optional[Tuple[dict, dict]]:
        s_bank = sender_bank or random.choice(BANK_NAMES)
        r_bank = receiver_bank or random.choice(BANK_NAMES)

        if require_business:
            if random.random() < 0.60:
                eligible_senders = [
                    a for a in self.accounts_by_bank[s_bank]
                    if a.get("account_type") == "BUSINESS" and a["current_balance"] >= 5000
                ]
                if not eligible_senders:
                    eligible_senders = [a for a in self.accounts_by_bank[s_bank] if a["current_balance"] >= 200]
                sender = random.choice(eligible_senders) if eligible_senders else None

                eligible_receivers = [
                    a for a in self.accounts_by_bank[r_bank]
                    if sender and a["account_id"] != sender["account_id"]
                ]
                receiver = random.choice(eligible_receivers) if eligible_receivers else None
            else:
                eligible_senders = [
                    a for a in self.accounts_by_bank[s_bank]
                    if a["current_balance"] >= 500
                ]
                sender = random.choice(eligible_senders) if eligible_senders else None

                eligible_receivers = [
                    a for a in self.accounts_by_bank[r_bank]
                    if a.get("account_type") == "BUSINESS" and sender and a["account_id"] != sender["account_id"]
                ]
                if not eligible_receivers:
                    eligible_receivers = [
                        a for a in self.accounts_by_bank[r_bank]
                        if sender and a["account_id"] != sender["account_id"]
                    ]
                receiver = random.choice(eligible_receivers) if eligible_receivers else None
        else:
            eligible_senders = [a for a in self.accounts_by_bank[s_bank] if a["current_balance"] >= 200]
            if not eligible_senders:
                all_eligible = [a for a in self.accounts_by_id.values() if a["current_balance"] >= 200]
                if not all_eligible:
                    return None
                sender = random.choice(all_eligible)
            else:
                sender = random.choice(eligible_senders)

            eligible_receivers = [a for a in self.accounts_by_bank[r_bank] if a["account_id"] != sender["account_id"]]
            if not eligible_receivers:
                eligible_receivers = [a for a in self.accounts_by_id.values() if a["account_id"] != sender["account_id"]]
                if not eligible_receivers:
                    return None
                receiver = random.choice(eligible_receivers)
            else:
                receiver = random.choice(eligible_receivers)

        if not sender or not receiver:
            return None
        return sender, receiver
