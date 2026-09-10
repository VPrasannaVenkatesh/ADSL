"""
Fund Provenance Engine (Module 9 & 10).
Tracks downstream and upstream fund movement through the transaction network graph:
Source Account -> Intermediate Account(s) -> Downstream Sinks.
Preserves audit links between transactions without marking all downstream accounts as fraudulent.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import networkx as nx

from .graph_engine import TransactionNetworkGraph, GLOBAL_NETWORK_GRAPH


def trace_fund_provenance(
    account_id: str,
    max_hops: int = 3,
    graph_instance: TransactionNetworkGraph = GLOBAL_NETWORK_GRAPH,
) -> Dict[str, Any]:
    """
    Traces fund provenance around an account:
    - Upstream Inflow Tree: Where did funds recently originate from?
    - Downstream Outflow Tree: Where did funds subsequently disperse to?
    - Full Provenance Chains: Multi-hop transaction sequences.
    """
    with graph_instance._lock:
        if not graph_instance.graph.has_node(account_id):
            return {
                "account_id": account_id,
                "upstream_sources": [],
                "downstream_destinations": [],
                "provenance_chains": [],
                "total_inflow": 0,
                "total_outflow": 0,
                "pass_through_ratio": 0.0,
            }

        g = graph_instance.graph
        
        # 1. Direct and multi-hop upstream inflows (who sent money to account_id)
        upstream_nodes: List[Dict[str, Any]] = []
        total_inflow = 0
        for pred in g.predecessors(account_id):
            e_data = g.get_edge_data(pred, account_id) or {}
            amt = int(e_data.get("amount", 0))
            total_inflow += amt
            upstream_nodes.append({
                "source_account": pred,
                "source_bank": g.nodes[pred].get("bank", "UNKNOWN"),
                "amount": amt,
                "transaction_id": e_data.get("transaction_id", ""),
                "timestamp": str(e_data.get("timestamp", "")),
                "is_cross_bank": bool(e_data.get("is_cross_bank", False)),
                "hop_distance": 1,
            })

        # 2. Direct and multi-hop downstream outflows (where did account_id send money)
        downstream_nodes: List[Dict[str, Any]] = []
        total_outflow = 0
        for succ in g.successors(account_id):
            e_data = g.get_edge_data(account_id, succ) or {}
            amt = int(e_data.get("amount", 0))
            total_outflow += amt
            downstream_nodes.append({
                "destination_account": succ,
                "destination_bank": g.nodes[succ].get("bank", "UNKNOWN"),
                "amount": amt,
                "transaction_id": e_data.get("transaction_id", ""),
                "timestamp": str(e_data.get("timestamp", "")),
                "is_cross_bank": bool(e_data.get("is_cross_bank", False)),
                "dwell_time_seconds": e_data.get("dwell_time_seconds", -1),
                "hop_distance": 1,
            })

        # 3. Calculate pass-through ratio
        pass_through_ratio = 0.0
        if total_inflow > 0:
            pass_through_ratio = round(min(1.0, total_outflow / total_inflow), 4)

        # 4. Extract end-to-end multi-hop chains
        chains = graph_instance.extract_chains_around_account(account_id, max_depth=max_hops)

        # Format provenance chain structures
        formatted_chains = []
        for c in chains:
            chain_hops = []
            chain_total = 0
            for hop in c:
                chain_total += hop.get("amount", 0)
                chain_hops.append({
                    "from_account": hop["from_account"],
                    "from_bank": hop["sender_bank"],
                    "to_account": hop["to_account"],
                    "to_bank": hop["receiver_bank"],
                    "amount": hop["amount"],
                    "transaction_id": hop["transaction_id"],
                    "dwell_time_seconds": hop.get("dwell_time_seconds", -1),
                    "status": hop.get("status", "COMPLETED"),
                })
            formatted_chains.append({
                "chain_length": len(c),
                "total_flow_amount": chain_total,
                "hops": chain_hops,
            })

        return {
            "account_id": account_id,
            "bank": g.nodes[account_id].get("bank", "UNKNOWN"),
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "pass_through_ratio": pass_through_ratio,
            "upstream_sources": upstream_nodes,
            "downstream_destinations": downstream_nodes,
            "provenance_chains": formatted_chains,
        }
