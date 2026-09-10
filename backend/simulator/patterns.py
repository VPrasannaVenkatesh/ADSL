"""
Concurrent Connected Network Patterns Generator for Banking Behavioural Analysis.
Generates multi-hop chains, fan-in, fan-out, rapid forwarding, amount splitting,
and circular/diamond flow topologies without explicit labels or flags.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from .config import BANK_NAMES, TX_TYPES, DEVICE_TYPES, LOCATIONS
from .account_manager import AccountManager


import uuid

@dataclass
class PendingStep:
    sender_account_id: str
    sender_bank: str
    receiver_account_id: str
    receiver_bank: str
    amount: int
    tx_type: str
    device_ip: str
    location: str
    scheduled_time: datetime
    pattern_type: str  # Internal pattern type for generator state, not saved to DB
    sequence_id: str = ""  # ID linking all steps of this flow sequence


class NetworkPatternGenerator:
    """
    Manages concurrent multi-party transaction topologies.
    Maintains a pool of active connected subgraphs and scheduled event queues.
    """

    def __init__(self, account_mgr: AccountManager):
        self.account_mgr = account_mgr
        self.pending_queue: List[PendingStep] = []
        # Pre-select dedicated connected account clusters across all 3 banks
        self.clusters: List[Dict[str, List[dict]]] = self._initialize_clusters()

    def cancel_pattern_sequence(self, sequence_id: str):
        """Cancels all remaining pending steps for a pattern when money flow is stopped due to risk."""
        if not sequence_id:
            return
        initial_len = len(self.pending_queue)
        self.pending_queue = [s for s in self.pending_queue if s.sequence_id != sequence_id]
        cancelled = initial_len - len(self.pending_queue)
        if cancelled > 0:
            print(f"[PATTERN ENGINE] Halted pattern sequence {sequence_id}: {cancelled} downstream steps cancelled due to risk policy.")

    def cancel_steps_for_account(self, account_id: str):
        """Cancels all pending steps where account is sender when funds are restricted/frozen/held."""
        if not account_id:
            return
        initial_len = len(self.pending_queue)
        self.pending_queue = [s for s in self.pending_queue if s.sender_account_id != account_id]
        cancelled = initial_len - len(self.pending_queue)
        if cancelled > 0:
            print(f"[PATTERN ENGINE] Halted money flow from {account_id}: {cancelled} pending steps cancelled due to account risk/lien.")

    def _initialize_clusters(self) -> List[Dict[str, List[dict]]]:
        """
        Creates 8 distinct multi-bank clusters of accounts to generate
        recurring connected subgraph topologies over time.
        """
        clusters = []
        for i in range(8):
            # Select 2-3 accounts from each bank for this cluster
            cluster = {
                "SBI": [],
                "AXIS": [],
                "IOB": [],
                "all": []
            }
            for bank in BANK_NAMES:
                accs = self.account_mgr.accounts_by_bank[bank]
                if len(accs) >= 10:
                    # Pick unique slice
                    start_idx = (i * 15 + BANK_NAMES.index(bank) * 5) % (len(accs) - 5)
                    selected = accs[start_idx:start_idx + 3]
                    cluster[bank] = selected
                    cluster["all"].extend(selected)
            if len(cluster["all"]) >= 6:
                clusters.append(cluster)
        return clusters

    def has_pending_steps(self, current_time: datetime) -> bool:
        """Returns True if there are pending pattern steps ready for execution."""
        return any(step.scheduled_time <= current_time for step in self.pending_queue)

    def pop_ready_step(self, current_time: datetime) -> Optional[PendingStep]:
        """Pops the oldest ready scheduled step."""
        for idx, step in enumerate(self.pending_queue):
            if step.scheduled_time <= current_time:
                return self.pending_queue.pop(idx)
        return None

    def trigger_pattern_sequence(self, base_time: datetime):
        """
        Triggers one of several multi-account network patterns.
        Schedules all subsequent hops into the pending_queue with short dwell times.
        """
        if not self.clusters:
            return

        cluster = random.choice(self.clusters)
        pattern_choice = random.choice([
            "MULTI_HOP_CHAIN",
            "FAN_IN",
            "FAN_OUT",
            "RAPID_FORWARDING",
            "DIAMOND_SPLIT_MERGE",
            "CIRCULAR_FLOW"
        ])

        all_accs = [a for a in cluster["all"] if a["current_balance"] >= 2000]
        if len(all_accs) < 4:
            return

        if pattern_choice == "MULTI_HOP_CHAIN":
            self._schedule_multi_hop_chain(cluster, base_time)
        elif pattern_choice == "FAN_IN":
            self._schedule_fan_in(cluster, base_time)
        elif pattern_choice == "FAN_OUT":
            self._schedule_fan_out(cluster, base_time)
        elif pattern_choice == "RAPID_FORWARDING":
            self._schedule_rapid_forwarding(cluster, base_time)
        elif pattern_choice == "DIAMOND_SPLIT_MERGE":
            self._schedule_diamond_pattern(cluster, base_time)
        elif pattern_choice == "CIRCULAR_FLOW":
            self._schedule_circular_flow(cluster, base_time)

    def _schedule_multi_hop_chain(self, cluster: dict, base_time: datetime):
        """
        Multi-hop cross-bank chain: A (SBI) ➔ B (AXIS) ➔ C (IOB) ➔ D (SBI)
        with short dwell times (10s - 120s between hops).
        """
        sbi_accs = [a for a in cluster["SBI"] if a["current_balance"] >= 5000]
        axis_accs = cluster["AXIS"]
        iob_accs = cluster["IOB"]

        if not sbi_accs or not axis_accs or not iob_accs:
            return

        node_a = random.choice(sbi_accs)
        node_b = random.choice(axis_accs)
        node_c = random.choice(iob_accs)
        node_d = random.choice([a for a in cluster["all"] if a["account_id"] not in (node_a["account_id"], node_b["account_id"], node_c["account_id"])])

        amount_1 = random.randint(15000, 45000)
        amount_1 = min(amount_1, int(node_a["current_balance"] * 0.9))
        if amount_1 < 2000:
            return

        seq_id = f"SEQ_CHAIN_{uuid.uuid4().hex[:8]}"

        # Hop 1: A -> B
        t1 = base_time + timedelta(seconds=random.randint(1, 5))
        self.pending_queue.append(self._create_step(node_a, node_b, amount_1, t1, "MULTI_HOP_CHAIN", seq_id))

        # Hop 2: B -> C (rapid forward 90-95% of incoming)
        amount_2 = int(amount_1 * random.uniform(0.90, 0.96))
        t2 = t1 + timedelta(seconds=random.randint(15, 90))
        self.pending_queue.append(self._create_step(node_b, node_c, amount_2, t2, "MULTI_HOP_CHAIN", seq_id))

        # Hop 3: C -> D
        amount_3 = int(amount_2 * random.uniform(0.90, 0.95))
        t3 = t2 + timedelta(seconds=random.randint(20, 120))
        self.pending_queue.append(self._create_step(node_c, node_d, amount_3, t3, "MULTI_HOP_CHAIN", seq_id))

    def _schedule_fan_in(self, cluster: dict, base_time: datetime):
        """
        Fan-In: Multiple feeder accounts transfer funds to a single collector account within minutes.
        """
        all_accs = [a for a in cluster["all"] if a["current_balance"] >= 2000]
        if len(all_accs) < 4:
            return

        collector = random.choice(all_accs)
        feeders = [a for a in all_accs if a["account_id"] != collector["account_id"]][:3]
        seq_id = f"SEQ_FANIN_{uuid.uuid4().hex[:8]}"

        for i, feeder in enumerate(feeders):
            amt = random.randint(3000, 15000)
            amt = min(amt, int(feeder["current_balance"] * 0.8))
            if amt >= 500:
                t = base_time + timedelta(seconds=i * random.randint(5, 25))
                self.pending_queue.append(self._create_step(feeder, collector, amt, t, "FAN_IN", seq_id))

    def _schedule_fan_out(self, cluster: dict, base_time: datetime):
        """
        Fan-Out: Single distributor splits and transfers money to multiple recipients rapidly.
        """
        distributors = [a for a in cluster["all"] if a["current_balance"] >= 15000]
        if not distributors:
            return

        distributor = random.choice(distributors)
        recipients = [a for a in cluster["all"] if a["account_id"] != distributor["account_id"]][:3]

        total_to_distribute = min(int(distributor["current_balance"] * 0.85), random.randint(15000, 50000))
        split_amt = total_to_distribute // len(recipients)
        seq_id = f"SEQ_FANOUT_{uuid.uuid4().hex[:8]}"

        for i, recip in enumerate(recipients):
            t = base_time + timedelta(seconds=i * random.randint(8, 30))
            self.pending_queue.append(self._create_step(distributor, recip, split_amt, t, "FAN_OUT", seq_id))

    def _schedule_rapid_forwarding(self, cluster: dict, base_time: datetime):
        """
        Rapid Forwarding: A -> B, then B -> C within a short dwell time.
        """
        all_accs = [a for a in cluster["all"] if a["current_balance"] >= 4000]
        if len(all_accs) < 3:
            return

        node_a, node_b, node_c = random.sample(all_accs, 3)
        amount = random.randint(8000, 30000)
        amount = min(amount, int(node_a["current_balance"] * 0.9))
        if amount < 1000:
            return

        seq_id = f"SEQ_FWD_{uuid.uuid4().hex[:8]}"
        t1 = base_time + timedelta(seconds=random.randint(1, 5))
        self.pending_queue.append(self._create_step(node_a, node_b, amount, t1, "RAPID_FORWARDING", seq_id))

        forward_amt = int(amount * random.uniform(0.85, 0.96))
        t2 = t1 + timedelta(seconds=random.randint(10, 45))
        self.pending_queue.append(self._create_step(node_b, node_c, forward_amt, t2, "RAPID_FORWARDING", seq_id))

    def _schedule_diamond_pattern(self, cluster: dict, base_time: datetime):
        """
        Diamond Split & Merge: A sends to B & C; B & C send to D.
        """
        all_accs = [a for a in cluster["all"] if a["current_balance"] >= 8000]
        if len(all_accs) < 4:
            return

        node_a, node_b, node_c, node_d = random.sample(all_accs, 4)
        amt_b = random.randint(4000, 15000)
        amt_c = random.randint(4000, 15000)
        if node_a["current_balance"] < (amt_b + amt_c + 500):
            return

        seq_id = f"SEQ_DIAMOND_{uuid.uuid4().hex[:8]}"
        t1 = base_time + timedelta(seconds=5)
        t2 = base_time + timedelta(seconds=12)
        t3 = base_time + timedelta(seconds=45)
        t4 = base_time + timedelta(seconds=55)

        self.pending_queue.append(self._create_step(node_a, node_b, amt_b, t1, "DIAMOND_SPLIT_MERGE", seq_id))
        self.pending_queue.append(self._create_step(node_a, node_c, amt_c, t2, "DIAMOND_SPLIT_MERGE", seq_id))
        self.pending_queue.append(self._create_step(node_b, node_d, int(amt_b * 0.92), t3, "DIAMOND_SPLIT_MERGE", seq_id))
        self.pending_queue.append(self._create_step(node_c, node_d, int(amt_c * 0.92), t4, "DIAMOND_SPLIT_MERGE", seq_id))

    def _schedule_circular_flow(self, cluster: dict, base_time: datetime):
        """
        Circular Flow: A ➔ B ➔ C ➔ A across different banks.
        """
        all_accs = [a for a in cluster["all"] if a["current_balance"] >= 6000]
        if len(all_accs) < 3:
            return

        node_a, node_b, node_c = random.sample(all_accs, 3)
        amount = random.randint(6000, 20000)
        amount = min(amount, int(node_a["current_balance"] * 0.85))
        if amount < 1000:
            return

        seq_id = f"SEQ_CIRC_{uuid.uuid4().hex[:8]}"
        t1 = base_time + timedelta(seconds=5)
        t2 = t1 + timedelta(seconds=random.randint(20, 60))
        t3 = t2 + timedelta(seconds=random.randint(20, 60))

        self.pending_queue.append(self._create_step(node_a, node_b, amount, t1, "CIRCULAR_FLOW", seq_id))
        self.pending_queue.append(self._create_step(node_b, node_c, int(amount * 0.95), t2, "CIRCULAR_FLOW", seq_id))
        self.pending_queue.append(self._create_step(node_c, node_a, int(amount * 0.90), t3, "CIRCULAR_FLOW", seq_id))

    def _create_step(self, sender: dict, receiver: dict, amount: int, sched_time: datetime, pattern_name: str, sequence_id: str = "") -> PendingStep:
        tx_type = random.choice(["UPI", "IMPS", "NEFT"])
        dev_ip = self.account_mgr.get_account_device(sender["account_id"], allow_device_switch=(random.random() < 0.15))
        loc = self.account_mgr.get_account_location(sender, allow_location_switch=(random.random() < 0.15))
        return PendingStep(
            sender_account_id=sender["account_id"],
            sender_bank=sender["bank"],
            receiver_account_id=receiver["account_id"],
            receiver_bank=receiver["bank"],
            amount=amount,
            tx_type=tx_type,
            device_ip=dev_ip,
            location=loc,
            scheduled_time=sched_time,
            pattern_type=pattern_name,
            sequence_id=sequence_id,
        )
