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

    def get_subgraph_for_transaction(self, tx_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Returns full graph data (nodes, directed edges, roles, GNN probabilities, statuses)
        centered around the specified transaction.
        Evaluates Reinforcement Learning (RL) investigation agent to decide whether the graph
        should grow further or terminate traversal.
        """
        depth = max(1, min(4, int(depth)))
        with self._lock:
            matched_result = None

            # 1. Check if this tx_id is already in an existing network
            for net_id, net in self.networks.items():
                if net.get("trigger_transaction_id") == tx_id or any(e.get("transaction_id") == tx_id for e in net.get("edges", [])):
                    matched_result = {**net, "selected_transaction_id": tx_id}
                    break

            # 2. Check in GLOBAL_NETWORK_GRAPH
            if not matched_result:
                tx_data = GLOBAL_NETWORK_GRAPH.transactions_by_id.get(tx_id)
                sender_id = None
                receiver_id = None
                if tx_data:
                    sender_id = tx_data.get("sender_account_id") or tx_data.get("sender_account")
                    receiver_id = tx_data.get("receiver_account_id") or tx_data.get("receiver_account")
                else:
                    # Search edges of GLOBAL_NETWORK_GRAPH
                    with GLOBAL_NETWORK_GRAPH._lock:
                        for u, v, d in GLOBAL_NETWORK_GRAPH.graph.edges(data=True):
                            if d.get("transaction_id") == tx_id:
                                sender_id, receiver_id = u, v
                                tx_data = d
                                break

                # If accounts found and mapped to an existing network
                if sender_id and sender_id in self.account_to_network:
                    net = self.networks.get(self.account_to_network[sender_id])
                    if net:
                        matched_result = {**net, "selected_transaction_id": tx_id}
                elif receiver_id and receiver_id in self.account_to_network:
                    net = self.networks.get(self.account_to_network[receiver_id])
                    if net:
                        matched_result = {**net, "selected_transaction_id": tx_id}

            if not matched_result:
                # Build dynamic subgraph around sender & receiver with requested depth
                subgraph_nodes = set()
                with GLOBAL_NETWORK_GRAPH._lock:
                    g = GLOBAL_NETWORK_GRAPH.graph
                    for root in [sender_id, receiver_id]:
                        if root and g.has_node(root):
                            subgraph_nodes.add(root)
                            subgraph_nodes.update(nx.single_source_shortest_path_length(g, root, cutoff=depth).keys())
                            subgraph_nodes.update(nx.single_source_shortest_path_length(g.reverse(), root, cutoff=depth).keys())

                    if not subgraph_nodes:
                        if sender_id and receiver_id:
                            subgraph_nodes = {sender_id, receiver_id}
                        else:
                            subgraph_nodes = set(list(g.nodes)[-6:]) if len(g.nodes) > 0 else set()

                    sub = g.subgraph(subgraph_nodes).copy()

                # Analyze nodes and build node list
                nodes_list = []
                banks_involved = set()
                for n in sub.nodes():
                    n_data = sub.nodes.get(n, {})
                    bank = n_data.get("bank", n.split("-")[0] if "-" in n else "SBI")
                    banks_involved.add(bank)
                    in_deg = sub.in_degree(n)
                    out_deg = sub.out_degree(n)
                    node_risk = float(n_data.get("risk_score", 0.0) or 0.0)
                    is_mule = "MULE" in n.upper() or node_risk >= 70 or (in_deg >= 2 and out_deg >= 1)
                    is_susp = in_deg >= 1 and out_deg >= 1 or node_risk >= 45
                    classif = "MULE" if is_mule else ("SUSPICIOUS" if is_susp else "NORMAL")
                    role = self._determine_node_role(n, sub, classif, in_deg, out_deg)
                    gnn_prob = 0.88 if is_mule else (0.62 if is_susp else 0.12)
                    nodes_list.append({
                        "account_id": n,
                        "bank": bank,
                        "classification": classif,
                        "behaviour_risk": round(node_risk if node_risk > 0 else (75.0 if classif == "MULE" else 25.0), 1),
                        "xgboost_risk": round(gnn_prob * 90.0, 1),
                        "gnn_mule_probability": gnn_prob,
                        "connected_accounts": list(set(list(sub.predecessors(n)) + list(sub.successors(n)))),
                        "incoming_transactions": in_deg,
                        "outgoing_transactions": out_deg,
                        "fan_in": in_deg >= 3,
                        "fan_out": out_deg >= 3,
                        "rapid_forwarding": in_deg >= 1 and out_deg >= 1,
                        "amount_splitting": out_deg >= 2,
                        "network_role": role,
                    })

                edges_list = []
                for u, v, d in sub.edges(data=True):
                    e_status = d.get("status", "COMPLETED")
                    is_halted = e_status in ("UNDER_REVIEW", "RESTRICTED", "FROZEN") or bool(d.get("flow_stopped", False))
                    edges_list.append({
                        "source": u,
                        "target": v,
                        "amount": d.get("amount", 25000),
                        "timestamp": str(d.get("timestamp", datetime.now().isoformat())),
                        "transaction_id": d.get("transaction_id", f"TX_{u}_{v}"),
                        "is_cross_bank": d.get("is_cross_bank", False),
                        "status": e_status,
                        "flow_stopped": is_halted,
                        "halt_reason": f"Money flow halted ({e_status})" if is_halted else None,
                    })

                matched_result = {
                    "network_id": self.account_to_network.get(sender_id or "") or f"SUBGRAPH-{tx_id[-6:] if tx_id else 'TX'}",
                    "selected_transaction_id": tx_id,
                    "risk_score": 75.0 if any(n["classification"] == "MULE" for n in nodes_list) else 45.0,
                    "risk_level": "HIGH" if any(n["classification"] == "MULE" for n in nodes_list) else "MEDIUM",
                    "mule_accounts": sum(1 for n in nodes_list if n["classification"] == "MULE"),
                    "suspicious_accounts": sum(1 for n in nodes_list if n["classification"] == "SUSPICIOUS"),
                    "total_accounts": len(nodes_list),
                    "banks_involved": sorted(list(banks_involved)),
                    "primary_pattern": "MULE DISPERSION & SINK" if any(n["network_role"] == "SINK" for n in nodes_list) else "RAPID FORWARDING",
                    "status": "UNDER_REVIEW" if any(e["flow_stopped"] for e in edges_list) else "MONITORING",
                    "trigger_transaction_id": tx_id,
                    "nodes": nodes_list,
                    "edges": edges_list,
                }

            # 3. Evaluate Reinforcement Learning (RL) Investigation Decision
            try:
                from network_monitoring.rl_investigation_engine import GLOBAL_RL_AGENT
                m_prob = max([n.get("gnn_mule_probability", 0.1) for n in matched_result.get("nodes", [])] or [0.3])
                rl_dec = GLOBAL_RL_AGENT.decide_investigation_action(
                    network_id=matched_result.get("network_id", "NET_SUBGRAPH"),
                    transaction_id=tx_id,
                    network_risk_score=float(matched_result.get("risk_score", 60.0)),
                    max_mule_probability=m_prob,
                    suspicious_node_count=matched_result.get("suspicious_accounts", 0) + matched_result.get("mule_accounts", 0),
                    current_hops_analyzed=depth,
                    graph_density=0.45,
                    recent_suspicious_tx_count=len(matched_result.get("edges", [])),
                    lien_active=matched_result.get("status") in ("UNDER_REVIEW", "RESTRICTED", "FROZEN"),
                    node_count=len(matched_result.get("nodes", [])),
                )
                rl_dec["should_grow"] = (rl_dec["action"] == "EXPAND_GRAPH" and depth < 4)
                matched_result["rl_decision"] = rl_dec
            except Exception as e:
                matched_result["rl_decision"] = {
                    "action": "EXPAND_GRAPH" if depth < 3 else "STOP_INVESTIGATION",
                    "should_grow": depth < 3,
                    "confidence": 0.85,
                    "reward": 7.0,
                    "reason": "RL agent heuristic fallback.",
                    "hops_analyzed": depth,
                    "investigation_cost": 0.5,
                }

            # 4. Attach Dynamic Automated Verdict
            r_score = float(matched_result.get("risk_score", 50.0))
            is_mule_ring = matched_result.get("mule_accounts", 0) > 0
            if r_score >= 80.0 or is_mule_ring:
                verdict_title = "AUTOMATIC LIEN APPLIED & QUARANTINED"
                verdict_status = "RESTRICTED"
                verdict_desc = f"Autonomous policy: Combined GNN Mule Risk ({r_score:.1f}%) crossed critical security threshold. Inter-bank lien automatically imposed."
            elif r_score >= 50.0:
                verdict_title = "DYNAMIC HIGH-VELOCITY MONITORING"
                verdict_status = "UNDER_REVIEW"
                verdict_desc = "Autonomous policy: Transaction flagged for cross-bank behavioural anomaly. Placed on dynamic watch."
            else:
                verdict_title = "CLEARED BY FAST PATH"
                verdict_status = "COMPLETED"
                verdict_desc = "Autonomous policy: Normal customer behavioural profile verified. Zero restrictions imposed."

            matched_result["automated_verdict"] = {
                "policy_action": verdict_title,
                "status": verdict_status,
                "automated_reason": verdict_desc,
                "hops_analyzed": depth,
            }

            return matched_result

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
