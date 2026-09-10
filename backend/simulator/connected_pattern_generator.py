"""
Connected pattern generator for multi-bank simulation.
Generates multi-hop chains, fan-in, fan-out, rapid forwarding, amount splitting,
and circular flows across SBI, AXIS, and IOB without adding explicit fraud/mule labels.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

BANK_NAMES = ["SBI", "AXIS", "IOB"]
DEVICE_TYPES = ["Mobile", "Desktop", "Laptop", "Tablet"]
LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur",
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]


@dataclass
class ScheduledPatternStep:
    sender_account_id: str
    sender_bank: str
    receiver_account_id: str
    receiver_bank: str
    amount: int
    tx_type: str
    device_ip: str
    location: str
    scheduled_time: datetime


class ConnectedPatternGenerator:
    """
    Schedules and manages multi-account connected network patterns over time.
    """

    def __init__(self, accounts_by_bank: Dict[str, List[dict]], accounts_by_id: Dict[str, dict]):
        self.accounts_by_bank = accounts_by_bank
        self.accounts_by_id = accounts_by_id
        self.pending_steps: List[ScheduledPatternStep] = []
        self.clusters: List[Dict[str, List[dict]]] = self._create_account_clusters()

    def _create_account_clusters(self) -> List[Dict[str, List[dict]]]:
        """Creates dedicated multi-bank account clusters for recurring graph structures."""
        clusters = []
        for i in range(8):
            cluster = {"SBI": [], "AXIS": [], "IOB": [], "all": []}
            for bank in BANK_NAMES:
                accs = self.accounts_by_bank.get(bank, [])
                if len(accs) >= 10:
                    start_idx = (i * 12 + BANK_NAMES.index(bank) * 4) % (len(accs) - 4)
                    chosen = accs[start_idx:start_idx + 3]
                    cluster[bank] = chosen
                    cluster["all"].extend(chosen)
            if len(cluster["all"]) >= 6:
                clusters.append(cluster)
        return clusters

    def has_ready_step(self, current_time: datetime) -> bool:
        return any(s.scheduled_time <= current_time for s in self.pending_steps)

    def pop_ready_step(self, current_time: datetime) -> Optional[ScheduledPatternStep]:
        for idx, step in enumerate(self.pending_steps):
            if step.scheduled_time <= current_time:
                return self.pending_steps.pop(idx)
        return None

    def trigger_random_pattern(self, base_time: datetime):
        """Triggers a connected multi-party pattern and schedules its sequential hops."""
        if not self.clusters:
            return

        cluster = random.choice(self.clusters)
        pattern = random.choice(["MULTI_HOP", "FAN_IN", "FAN_OUT", "RAPID_FORWARD", "AMOUNT_SPLIT", "CIRCULAR"])

        if pattern == "MULTI_HOP":
            self._schedule_multi_hop(cluster, base_time)
        elif pattern == "FAN_IN":
            self._schedule_fan_in(cluster, base_time)
        elif pattern == "FAN_OUT":
            self._schedule_fan_out(cluster, base_time)
        elif pattern == "RAPID_FORWARD":
            self._schedule_rapid_forward(cluster, base_time)
        elif pattern == "AMOUNT_SPLIT":
            self._schedule_amount_split(cluster, base_time)
        elif pattern == "CIRCULAR":
            self._schedule_circular(cluster, base_time)

    def _schedule_multi_hop(self, cluster: dict, base_time: datetime):
        """Cross-bank relay: SBI ➔ AXIS ➔ IOB ➔ SBI with short dwell intervals."""
        sbi = [a for a in cluster["SBI"] if a["current_balance"] >= 6000]
        axis = cluster["AXIS"]
        iob = cluster["IOB"]
        if not sbi or not axis or not iob:
            return

        node_a = random.choice(sbi)
        node_b = random.choice(axis)
        node_c = random.choice(iob)
        node_d = random.choice([a for a in cluster["all"] if a["account_id"] not in (node_a["account_id"], node_b["account_id"], node_c["account_id"])])

        amt1 = random.randint(15000, 40000)
        amt1 = min(amt1, int(node_a["current_balance"] * 0.9))
        if amt1 < 2000:
            return

        t1 = base_time + timedelta(seconds=random.randint(1, 4))
        self.pending_steps.append(self._create_step(node_a, node_b, amt1, t1))

        amt2 = int(amt1 * random.uniform(0.90, 0.96))
        t2 = t1 + timedelta(seconds=random.randint(15, 60))
        self.pending_steps.append(self._create_step(node_b, node_c, amt2, t2))

        amt3 = int(amt2 * random.uniform(0.90, 0.95))
        t3 = t2 + timedelta(seconds=random.randint(20, 90))
        self.pending_steps.append(self._create_step(node_c, node_d, amt3, t3))

    def _schedule_fan_in(self, cluster: dict, base_time: datetime):
        """Fan-in: Multiple accounts transfer to a single collector account within minutes."""
        eligible = [a for a in cluster["all"] if a["current_balance"] >= 2000]
        if len(eligible) < 4:
            return

        collector = random.choice(eligible)
        feeders = [a for a in eligible if a["account_id"] != collector["account_id"]][:3]

        for i, feeder in enumerate(feeders):
            amt = min(random.randint(3000, 15000), int(feeder["current_balance"] * 0.85))
            if amt >= 500:
                t = base_time + timedelta(seconds=i * random.randint(5, 20))
                self.pending_steps.append(self._create_step(feeder, collector, amt, t))

    def _schedule_fan_out(self, cluster: dict, base_time: datetime):
        """Fan-out: Single distributor account disperses funds to multiple accounts."""
        distributors = [a for a in cluster["all"] if a["current_balance"] >= 15000]
        if not distributors:
            return

        distributor = random.choice(distributors)
        recipients = [a for a in cluster["all"] if a["account_id"] != distributor["account_id"]][:3]
        total_amt = min(int(distributor["current_balance"] * 0.85), random.randint(15000, 45000))
        split_amt = total_amt // len(recipients)

        for i, recip in enumerate(recipients):
            t = base_time + timedelta(seconds=i * random.randint(6, 25))
            self.pending_steps.append(self._create_step(distributor, recip, split_amt, t))

    def _schedule_rapid_forward(self, cluster: dict, base_time: datetime):
        """Rapid forwarding: A ➔ B, then B ➔ C within 15-45 seconds."""
        eligible = [a for a in cluster["all"] if a["current_balance"] >= 4000]
        if len(eligible) < 3:
            return

        a, b, c = random.sample(eligible, 3)
        amt = min(random.randint(8000, 25000), int(a["current_balance"] * 0.9))
        if amt < 1000:
            return

        t1 = base_time + timedelta(seconds=2)
        self.pending_steps.append(self._create_step(a, b, amt, t1))

        t2 = t1 + timedelta(seconds=random.randint(12, 45))
        self.pending_steps.append(self._create_step(b, c, int(amt * random.uniform(0.88, 0.96)), t2))

    def _schedule_amount_split(self, cluster: dict, base_time: datetime):
        """Amount splitting: A sends to B & C; B & C both send to D."""
        eligible = [a for a in cluster["all"] if a["current_balance"] >= 8000]
        if len(eligible) < 4:
            return

        a, b, c, d = random.sample(eligible, 4)
        amt1 = random.randint(4000, 12000)
        amt2 = random.randint(4000, 12000)
        if a["current_balance"] < (amt1 + amt2 + 500):
            return

        t1 = base_time + timedelta(seconds=4)
        t2 = base_time + timedelta(seconds=10)
        t3 = base_time + timedelta(seconds=40)
        t4 = base_time + timedelta(seconds=50)

        self.pending_steps.append(self._create_step(a, b, amt1, t1))
        self.pending_steps.append(self._create_step(a, c, amt2, t2))
        self.pending_steps.append(self._create_step(b, d, int(amt1 * 0.92), t3))
        self.pending_steps.append(self._create_step(c, d, int(amt2 * 0.92), t4))

    def _schedule_circular(self, cluster: dict, base_time: datetime):
        """Circular multi-bank loop: A ➔ B ➔ C ➔ A."""
        eligible = [a for a in cluster["all"] if a["current_balance"] >= 6000]
        if len(eligible) < 3:
            return

        a, b, c = random.sample(eligible, 3)
        amt = min(random.randint(6000, 18000), int(a["current_balance"] * 0.85))
        if amt < 1000:
            return

        t1 = base_time + timedelta(seconds=5)
        t2 = t1 + timedelta(seconds=random.randint(20, 50))
        t3 = t2 + timedelta(seconds=random.randint(20, 50))

        self.pending_steps.append(self._create_step(a, b, amt, t1))
        self.pending_steps.append(self._create_step(b, c, int(amt * 0.95), t2))
        self.pending_steps.append(self._create_step(c, a, int(amt * 0.90), t3))

    def _create_step(self, sender: dict, receiver: dict, amount: int, sched_time: datetime) -> ScheduledPatternStep:
        dev_type = random.choice(DEVICE_TYPES)
        ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        return ScheduledPatternStep(
            sender_account_id=sender["account_id"],
            sender_bank=sender["bank"],
            receiver_account_id=receiver["account_id"],
            receiver_bank=receiver["bank"],
            amount=amount,
            tx_type=random.choice(["UPI", "IMPS", "NEFT"]),
            device_ip=f"{dev_type}:{ip}",
            location=random.choice(LOCATIONS),
            scheduled_time=sched_time,
        )
