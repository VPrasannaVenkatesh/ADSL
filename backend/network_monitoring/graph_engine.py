"""
Transaction Network Graph Engine.
Builds and maintains a directed multi-bank transaction graph with rich node & edge features,
ready for topological pattern analysis, NetworkX metrics, and future GNN integration.
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple, Any
import networkx as nx

from .config import GRAPH_MONITORING_CONFIG


class TransactionNetworkGraph:
    """
    Maintains an in-memory directed multi-graph of accounts and transactions across SBI, AXIS, and IOB.
    """

    def __init__(self, max_history: int = 2500):
        self.max_history = max_history
        self.graph = nx.DiGraph()
        self._lock = threading.RLock()
        
        # Fast lookup indices
        self.transactions_by_id: Dict[str, dict] = {}
        self.account_latest_inflow: Dict[str, datetime] = {}
        self.monitored_accounts: Set[str] = set()
        self.monitored_transactions: Set[str] = set()

    def add_account_node(self, account_id: str, bank: str, **kwargs):
        """Adds or updates an account node in the network graph."""
        with self._lock:
            if not self.graph.has_node(account_id):
                self.graph.add_node(
                    account_id,
                    account_id=account_id,
                    bank=bank,
                    account_type=kwargs.get("account_type", "SAVINGS"),
                    home_location=kwargs.get("home_location", "Chennai"),
                    is_monitored=(account_id in self.monitored_accounts),
                    risk_score=kwargs.get("risk_score", 0.0),
                    created_at=datetime.now(),
                    first_seen=kwargs.get("timestamp", datetime.now()),
                    last_seen=kwargs.get("timestamp", datetime.now()),
                )
            else:
                node = self.graph.nodes[account_id]
                node["last_seen"] = kwargs.get("timestamp", datetime.now())
                if "risk_score" in kwargs:
                    node["risk_score"] = kwargs["risk_score"]

    def add_transaction_edge(self, tx_dict: dict) -> float:
        """
        Adds a directed transaction edge from sender to receiver.
        Calculates dwell time (seconds between receiver's previous inflow and this outgoing hop).
        Returns calculated dwell_time_seconds (or -1 if no prior inflow).
        """
        sender_id = tx_dict["sender_account_id"]
        receiver_id = tx_dict["receiver_account_id"]
        sender_bank = tx_dict["sender_bank"]
        receiver_bank = tx_dict["receiver_bank"]
        tx_id = tx_dict["transaction_id"]
        amount = int(tx_dict["amount"])
        
        ts = tx_dict["transaction_timestamp"]
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except Exception:
                ts = datetime.now()

        with self._lock:
            # Ensure nodes exist
            self.add_account_node(sender_id, sender_bank, timestamp=ts)
            self.add_account_node(receiver_id, receiver_bank, timestamp=ts)

            # Calculate short dwell time on sender (if sender had a recent incoming transfer)
            dwell_time_sec = -1.0
            if sender_id in self.account_latest_inflow:
                prev_inflow_ts = self.account_latest_inflow[sender_id]
                if ts >= prev_inflow_ts:
                    dwell_time_sec = (ts - prev_inflow_ts).total_seconds()

            # Record receiver inflow timestamp
            self.account_latest_inflow[receiver_id] = ts

            # Edge attributes (graph-ready feature representation)
            edge_data = {
                "transaction_id": tx_id,
                "amount": amount,
                "timestamp": ts,
                "transaction_type": tx_dict.get("transaction_type", "UPI"),
                "is_cross_bank": tx_dict.get("is_cross_bank", (sender_bank != receiver_bank)),
                "sender_bank": sender_bank,
                "receiver_bank": receiver_bank,
                "sender_account_id": sender_id,
                "receiver_account_id": receiver_id,
                "sender_account": sender_id,
                "receiver_account": receiver_id,
                "location": tx_dict.get("location", "Chennai"),
                "device_ip": tx_dict.get("device_ip", "Mobile"),
                "recipient_is_new": tx_dict.get("recipient_is_new", False),
                "status": tx_dict.get("transaction_status", "INITIATED"),
                "dwell_time_seconds": dwell_time_sec,
            }

            self.graph.add_edge(sender_id, receiver_id, **edge_data)
            self.transactions_by_id[tx_id] = edge_data

            # Rolling window cleanup if exceeds max_history
            if len(self.transactions_by_id) > self.max_history:
                oldest_id = next(iter(self.transactions_by_id))
                del self.transactions_by_id[oldest_id]

            return dwell_time_sec

    def update_transaction_status(self, tx_id: str, new_status: str):
        """Updates the lifecycle status of a transaction edge and marks flow_stopped if halted."""
        with self._lock:
            is_stopped = new_status in ("UNDER_REVIEW", "RESTRICTED", "FROZEN")
            if tx_id in self.transactions_by_id:
                self.transactions_by_id[tx_id]["status"] = new_status
                self.transactions_by_id[tx_id]["flow_stopped"] = is_stopped
                if new_status in ("MONITORING", "UNDER_REVIEW"):
                    self.monitored_transactions.add(tx_id)

            for u, v, data in self.graph.edges(data=True):
                if data.get("transaction_id") == tx_id:
                    data["status"] = new_status
                    data["flow_stopped"] = is_stopped
                    if new_status in ("MONITORING", "UNDER_REVIEW"):
                        self.monitored_accounts.add(u)
                        self.monitored_accounts.add(v)
                        self.graph.nodes[u]["is_monitored"] = True
                        self.graph.nodes[v]["is_monitored"] = True
                    if is_stopped:
                        self.graph.nodes[v]["funds_controlled"] = True
                        if new_status == "FROZEN":
                            self.graph.nodes[v]["is_frozen"] = True
                    break

    def get_connected_subgraph(self, account_id: str, depth: int = 2) -> nx.DiGraph:
        """
        Extracts the connected multi-hop ego subgraph around an account up to `depth` hops (inbound and outbound).
        """
        with self._lock:
            if not self.graph.has_node(account_id):
                return nx.DiGraph()

            visited_nodes = {account_id}
            current_layer = {account_id}

            for _ in range(depth):
                next_layer = set()
                for n in current_layer:
                    successors = set(self.graph.successors(n))
                    predecessors = set(self.graph.predecessors(n))
                    next_layer.update(successors | predecessors)
                next_layer -= visited_nodes
                visited_nodes.update(next_layer)
                current_layer = next_layer
                if not current_layer:
                    break

            return self.graph.subgraph(visited_nodes).copy()

    def extract_chains_around_account(self, account_id: str, max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """
        Discovers all forward & backward multi-hop money flow chains involving the account:
        e.g. [X -> A -> B -> C -> D]
        """
        with self._lock:
            if not self.graph.has_node(account_id):
                return []

            chains = []
            
            # Find all simple paths of length >= 2 in the local neighbourhood
            sub = self.get_connected_subgraph(account_id, depth=max_depth)
            
            # Identify roots (in-degree = 0) and leaves (out-degree = 0)
            roots = [n for n in sub.nodes if sub.in_degree(n) == 0]
            leaves = [n for n in sub.nodes if sub.out_degree(n) == 0]

            if not roots:
                roots = list(sub.nodes)[:6]
            if not leaves:
                leaves = list(sub.nodes)[:6]

            for r in roots:
                for l in leaves:
                    if r != l:
                        try:
                            for path in nx.all_simple_paths(sub, source=r, target=l, cutoff=max_depth):
                                if account_id in path and len(path) >= 2:
                                    chain_edges = []
                                    for i in range(len(path) - 1):
                                        u, v = path[i], path[i + 1]
                                        e_data = sub.get_edge_data(u, v, default={})
                                        chain_edges.append({
                                            "from_account": u,
                                            "to_account": v,
                                            "sender_bank": sub.nodes[u].get("bank", ""),
                                            "receiver_bank": sub.nodes[v].get("bank", ""),
                                            "amount": e_data.get("amount", 0),
                                            "transaction_id": e_data.get("transaction_id", ""),
                                            "status": e_data.get("status", "COMPLETED"),
                                            "dwell_time_seconds": e_data.get("dwell_time_seconds", -1),
                                        })
                                    chains.append(chain_edges)
                        except Exception:
                            continue

            # Return unique chains limited to top 10 longest
            chains.sort(key=lambda c: len(c), reverse=True)
            return chains[:10]

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Returns topological summary metrics of the active transaction graph."""
        with self._lock:
            num_nodes = self.graph.number_of_nodes()
            num_edges = self.graph.number_of_edges()
            density = nx.density(self.graph) if num_nodes > 1 else 0.0

            return {
                "total_accounts_in_graph": num_nodes,
                "total_transactions_in_graph": num_edges,
                "monitored_accounts_count": len(self.monitored_accounts),
                "monitored_transactions_count": len(self.monitored_transactions),
                "graph_density": round(density, 6),
                "is_directed": True,
            }


# Singleton Global Graph Instance
GLOBAL_NETWORK_GRAPH = TransactionNetworkGraph()
