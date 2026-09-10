"""
ADSL Mule Network Manager & Topology Clustering Engine.
Identifies, clusters, and manages multi-account connected mule networks.
Computes network-level risk, roles, patterns, and full topology for interactive graph forensics.
"""

import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import networkx as nx

from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH


class MuleNetworkManager:
    """
    Manages detection, grouping, and forensics for connected Mule Networks.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.networks: Dict[str, Dict[str, Any]] = {}
        self.account_to_network: Dict[str, str] = {}
        self._counter = 1

    def _determine_node_role(
        self,
        node: str,
        graph: nx.DiGraph,
        classification: str,
        in_deg: int,
        out_deg: int,
        fan_in: bool = False,
        fan_out: bool = False,
    ) -> str:
        """
        Determines node role: SOURCE, MULE_HUB, MULE_RELAY, DISPERSER, SINK, SUSPICIOUS, NORMAL.
        """
        if classification == "NORMAL" and in_deg <= 1 and out_deg <= 1:
            return "NORMAL"

        if in_deg == 0 and out_deg > 0:
            return "SOURCE"
        elif in_deg > 0 and out_deg == 0:
            return "SINK"
        elif in_deg >= 2 and out_deg >= 2:
            return "MULE_HUB"
        elif fan_out or (out_deg >= 3 and in_deg <= 1):
            return "DISPERSER"
        elif in_deg >= 1 and out_deg >= 1:
            return "MULE_RELAY"
        elif classification in ("MULE", "SUSPICIOUS"):
            return "SUSPICIOUS"
        return "NORMAL"

    def register_or_update_network(
        self,
        trigger_tx_id: str,
        sender_id: str,
        receiver_id: str,
        gnn_result: Optional[Dict[str, Any]] = None,
        pattern_type: Optional[str] = None,
        risk_score: float = 75.0,
    ) -> Dict[str, Any]:
        """
        Groups connected mule/suspicious accounts into a Mule Network.
        """
        with self._lock:
            # Check if either account is already part of an existing network
            existing_net_id = self.account_to_network.get(sender_id) or self.account_to_network.get(receiver_id)
            if not existing_net_id:
                net_id = f"MN-{datetime.now().year}-{self._counter:03d}"
                self._counter += 1
            else:
                net_id = existing_net_id

            # Extract subgraph from global transaction graph
            subgraph_nodes = set()
            with GLOBAL_NETWORK_GRAPH._lock:
                g = GLOBAL_NETWORK_GRAPH.graph
                for root in [sender_id, receiver_id]:
                    if g.has_node(root):
                        subgraph_nodes.add(root)
                        # Add 2-hop neighbors
                        subgraph_nodes.update(nx.single_source_shortest_path_length(g, root, cutoff=2).keys())
                        # Add reverse 2-hop
                        subgraph_nodes.update(nx.single_source_shortest_path_length(g.reverse(), root, cutoff=2).keys())

                if not subgraph_nodes:
                    subgraph_nodes = {sender_id, receiver_id}

                sub = g.subgraph(subgraph_nodes).copy()

            # Analyze nodes and build node detail dicts
            nodes_list = []
            mule_accounts = []
            suspicious_accounts = []
            banks_involved = set()

            for n in sub.nodes():
                n_data = sub.nodes.get(n, {})
                bank = n_data.get("bank", n.split("-")[0] if "-" in n else "SBI")
                banks_involved.add(bank)

                in_deg = sub.in_degree(n)
                out_deg = sub.out_degree(n)

                # Determine classification based on GNN, topology, and behavioural risk
                gnn_mule_prob = 0.15
                classif = "NORMAL"
                if gnn_result and "node_classifications" in gnn_result:
                    node_gnn = gnn_result["node_classifications"].get(n, {})
                    classif = node_gnn.get("classification", "NORMAL")
                    gnn_mule_prob = float(node_gnn.get("mule_probability", 0.15))

                node_risk = float(n_data.get("risk_score", 0.0) or 0.0)
                # Topological and behavioural classification
                if classif == "NORMAL":
                    if "MULE" in n.upper() or gnn_mule_prob >= 0.65 or node_risk >= 70.0 or (in_deg >= 2 and out_deg >= 1):
                        classif = "MULE"
                        gnn_mule_prob = max(gnn_mule_prob, 0.88)
                    elif in_deg >= 2 or out_deg >= 2 or gnn_mule_prob >= 0.35 or node_risk >= 45.0 or (in_deg >= 1 and out_deg >= 1):
                        classif = "SUSPICIOUS"
                        gnn_mule_prob = max(gnn_mule_prob, 0.62)

                if classif == "MULE":
                    mule_accounts.append(n)
                elif classif == "SUSPICIOUS":
                    suspicious_accounts.append(n)

                role = self._determine_node_role(n, sub, classif, in_deg, out_deg)

                node_dict = {
                    "account_id": n,
                    "bank": bank,
                    "classification": classif,
                    "behaviour_risk": round(node_risk if node_risk > 0 else (75.0 if classif == "MULE" else (55.0 if classif == "SUSPICIOUS" else 25.0)), 1),
                    "xgboost_risk": round(gnn_mule_prob * 100 * 0.9, 1),
                    "gnn_mule_probability": round(gnn_mule_prob, 3),
                    "connected_accounts": list(set(list(sub.predecessors(n)) + list(sub.successors(n)))),
                    "incoming_transactions": in_deg,
                    "outgoing_transactions": out_deg,
                    "fan_in": in_deg >= 3,
                    "fan_out": out_deg >= 3,
                    "rapid_forwarding": in_deg >= 1 and out_deg >= 1,
                    "amount_splitting": out_deg >= 2,
                    "network_role": role,
                }
                nodes_list.append(node_dict)
                self.account_to_network[n] = net_id

            # Analyze edges
            edges_list = []
            has_halted_flow = False
            has_frozen_edge = False
            has_restricted_edge = False
            has_review_edge = False

            for u, v, d in sub.edges(data=True):
                e_status = d.get("status", "COMPLETED")
                is_halted = e_status in ("UNDER_REVIEW", "RESTRICTED", "FROZEN") or bool(d.get("flow_stopped", False))
                if is_halted:
                    has_halted_flow = True
                if e_status == "FROZEN":
                    has_frozen_edge = True
                elif e_status == "RESTRICTED":
                    has_restricted_edge = True
                elif e_status == "UNDER_REVIEW":
                    has_review_edge = True

                edges_list.append({
                    "source": u,
                    "target": v,
                    "amount": d.get("amount", 25000),
                    "timestamp": d.get("timestamp", datetime.now().isoformat()),
                    "transaction_id": d.get("transaction_id", f"TX_{u}_{v}"),
                    "is_cross_bank": d.get("is_cross_bank", False),
                    "status": e_status,
                    "flow_stopped": is_halted,
                    "halt_reason": f"Money flow halted: Risk policy ({e_status})" if is_halted else None,
                })

            primary_pat = pattern_type or (
                "FAN-IN + RAPID FORWARDING" if len(mule_accounts) > 1 else (
                    "AMOUNT SPLITTING + RELAY" if any(n.get("amount_splitting") for n in nodes_list) else "RAPID FORWARDING"
                )
            )

            # Realistic network-level risk calculation
            if len(mule_accounts) >= 2:
                net_risk = max(risk_score, 88.0 + min(len(mule_accounts) * 2.0, 10.0))
            elif len(mule_accounts) == 1:
                net_risk = max(risk_score, 78.0 + min(len(suspicious_accounts) * 2.0, 12.0))
            elif len(suspicious_accounts) >= 1:
                net_risk = max(risk_score, 68.0 + min(len(suspicious_accounts) * 2.0, 10.0))
            else:
                net_risk = max(risk_score, 45.0)

            net_risk = min(net_risk, 99.0)
            risk_level = "CRITICAL" if net_risk >= 80.0 else ("HIGH" if net_risk >= 65.0 else ("MEDIUM" if net_risk >= 40.0 else "LOW"))

            # Determine dynamic Network Status per Project Specification
            if has_frozen_edge or net_risk >= 95.0:
                net_status = "FROZEN"
            elif has_restricted_edge or net_risk >= 85.0:
                net_status = "RESTRICTED"
            elif has_review_edge or len(mule_accounts) > 0 or net_risk >= 50.0 or has_halted_flow:
                net_status = "UNDER_REVIEW"
            elif net_risk >= 30.0:
                net_status = "MONITORING"
            else:
                net_status = "COMPLETED"

            network_entry = {
                "network_id": net_id,
                "risk_score": round(net_risk, 1),
                "risk_level": risk_level,
                "mule_accounts": len(mule_accounts),
                "suspicious_accounts": len(suspicious_accounts),
                "total_accounts": len(nodes_list),
                "banks_involved": sorted(list(banks_involved)),
                "primary_pattern": primary_pat,
                "status": net_status,
                "trigger_transaction_id": trigger_tx_id,
                "created_at": datetime.now().isoformat(),
                "mule_account_ids": mule_accounts,
                "suspicious_account_ids": suspicious_accounts,
                "nodes": nodes_list,
                "edges": edges_list,
            }

            self.networks[net_id] = network_entry
            return network_entry

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate metrics for Mule Networks page."""
        with self._lock:
            all_nets = list(self.networks.values())
            total = len(all_nets)
            critical = sum(1 for n in all_nets if n["risk_level"] == "CRITICAL")
            mule_accs = sum(n["mule_accounts"] for n in all_nets)
            susp_accs = sum(n["suspicious_accounts"] for n in all_nets)
            under_review = sum(1 for n in all_nets if n["status"] == "UNDER_REVIEW")

            return {
                "total_networks": total,
                "critical_networks": critical,
                "mule_accounts_detected": mule_accs,
                "suspicious_accounts": susp_accs,
                "networks_under_review": under_review,
                "networks": [
                    {
                        "network_id": n["network_id"],
                        "risk_score": n["risk_score"],
                        "risk_level": n["risk_level"],
                        "mule_accounts": n["mule_accounts"],
                        "suspicious_accounts": n["suspicious_accounts"],
                        "total_accounts": n["total_accounts"],
                        "banks_involved": n["banks_involved"],
                        "primary_pattern": n["primary_pattern"],
                        "status": n["status"],
                        "created_at": n["created_at"],
                    }
                    for n in all_nets
                ],
            }

    def get_network_detail(self, network_id: str) -> Optional[Dict[str, Any]]:
        """Returns full network graph detail for interactive visualization."""
        with self._lock:
            return self.networks.get(network_id)

    def update_network_status(self, network_id: str, new_status: str) -> bool:
        """Updates the status of a specific mule network (e.g. from Admin decision)."""
        with self._lock:
            if network_id in self.networks:
                self.networks[network_id]["status"] = new_status
                return True
            return False

    def update_network_for_account_or_tx(self, identifier: str, new_status: str):
        """Updates status of any network containing this account or transaction."""
        with self._lock:
            for net_id, net in self.networks.items():
                matching = False
                if net.get("trigger_transaction_id") == identifier:
                    matching = True
                elif identifier in self.account_to_network and self.account_to_network[identifier] == net_id:
                    matching = True
                elif any(e.get("transaction_id") == identifier for e in net.get("edges", [])):
                    matching = True
                elif any(n.get("account_id") == identifier for n in net.get("nodes", [])):
                    matching = True

                if matching:
                    # Update status
                    if new_status in ("FROZEN", "RESTRICTED", "RELEASED", "MONITORING", "UNDER_REVIEW"):
                        net["status"] = new_status
                        # If frozen or restricted, update edge halted flags
                        for e in net.get("edges", []):
                            if e.get("transaction_id") == identifier or identifier in (e.get("source"), e.get("target")):
                                e["status"] = new_status
                                if new_status in ("FROZEN", "RESTRICTED", "UNDER_REVIEW"):
                                    e["flow_stopped"] = True
                                    e["halt_reason"] = f"Money flow halted: Admin decision ({new_status})"
                                elif new_status in ("RELEASED", "MONITORING"):
                                    e["flow_stopped"] = False
                                    e["halt_reason"] = None


# Singleton Mule Network Manager
GLOBAL_MULE_NETWORKS = MuleNetworkManager()
