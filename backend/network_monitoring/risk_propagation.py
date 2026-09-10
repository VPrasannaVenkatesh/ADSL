"""
Controlled Risk Propagation Engine (Module 11).
Implements configurable, explainable risk propagation through connected transaction relationships.
Maintains three distinct concepts:
1. Direct Transaction Risk
2. Account Behavioural Risk
3. Network Contextual Risk
Does not permanently mark accounts as fraudulent; dynamically recalculates contextual risk.
"""

from typing import Dict, List, Any, Optional
import networkx as nx

from .graph_engine import TransactionNetworkGraph, GLOBAL_NETWORK_GRAPH

# Propagation hyperparameters
DEFAULT_PROPAGATION_CONFIG = {
    "decay_factor": 0.65,               # Risk decay per downstream hop
    "short_dwell_amplifier": 1.45,      # Multiplier if forwarded in < 60s
    "max_propagation_depth": 3,         # Maximum hops to propagate
    "contextual_risk_threshold": 45.0,  # Threshold to flag contextual network anomaly
}


def calculate_network_risk_propagation(
    account_id: str,
    direct_tx_risk: float = 0.0,
    account_behav_risk: float = 0.0,
    graph_instance: TransactionNetworkGraph = GLOBAL_NETWORK_GRAPH,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculates contextual network risk propagated to account_id from upstream senders.
    
    Returns a breakdown separating:
    - direct_transaction_risk (0 to 100)
    - account_behavioural_risk (0 to 100)
    - network_contextual_risk (0 to 100)
    - composite_propagated_risk (0 to 100)
    - propagation_sources (explainable audit list of upstream risk factors)
    """
    cfg = config or DEFAULT_PROPAGATION_CONFIG
    decay = cfg["decay_factor"]
    dwell_mult = cfg["short_dwell_amplifier"]
    max_depth = cfg["max_propagation_depth"]

    with graph_instance._lock:
        g = graph_instance.graph
        if not g.has_node(account_id):
            return {
                "account_id": account_id,
                "direct_transaction_risk": round(direct_tx_risk, 2),
                "account_behavioural_risk": round(account_behav_risk, 2),
                "network_contextual_risk": 0.0,
                "composite_propagated_risk": round(max(direct_tx_risk, account_behav_risk), 2),
                "propagation_sources": [],
                "is_contextually_elevated": False,
            }

        # Traverse upstream predecessors up to max_depth hops
        propagation_sources: List[Dict[str, Any]] = []
        accumulated_contextual_risk = 0.0

        # Layer 1: Direct Inflow Predecessors
        predecessors = list(g.predecessors(account_id))
        for pred in predecessors:
            edge_data = g.get_edge_data(pred, account_id) or {}
            pred_node = g.nodes[pred]
            
            # Base risk of sender account
            pred_risk = float(pred_node.get("risk_score", 0.0) or 0.0)
            dwell_sec = float(edge_data.get("dwell_time_seconds", -1.0) or -1.0)
            
            # Amplifier if rapid forwarding
            multiplier = dwell_mult if (0.0 <= dwell_sec <= 60.0) else 1.0
            hop_risk = pred_risk * decay * multiplier

            if hop_risk > 15.0:
                accumulated_contextual_risk += hop_risk
                propagation_sources.append({
                    "from_account": pred,
                    "from_bank": pred_node.get("bank", "UNKNOWN"),
                    "upstream_risk_score": round(pred_risk, 2),
                    "hop_distance": 1,
                    "dwell_time_seconds": dwell_sec,
                    "applied_multiplier": multiplier,
                    "propagated_contribution": round(hop_risk, 2),
                    "reason": f"Upstream inflow from {pred} (risk {pred_risk:.1f})" + (f" rapidly forwarded in {dwell_sec:.0f}s" if multiplier > 1.0 else ""),
                })

            # Layer 2: Predecessors of predecessors (2 hops)
            if max_depth >= 2:
                for grand_pred in g.predecessors(pred):
                    gp_node = g.nodes[grand_pred]
                    gp_risk = float(gp_node.get("risk_score", 0.0) or 0.0)
                    gp_hop_risk = gp_risk * (decay ** 2)
                    if gp_hop_risk > 20.0:
                        accumulated_contextual_risk += gp_hop_risk
                        propagation_sources.append({
                            "from_account": grand_pred,
                            "from_bank": gp_node.get("bank", "UNKNOWN"),
                            "upstream_risk_score": round(gp_risk, 2),
                            "hop_distance": 2,
                            "dwell_time_seconds": -1,
                            "applied_multiplier": 1.0,
                            "propagated_contribution": round(gp_hop_risk, 2),
                            "reason": f"2-hop upstream origin {grand_pred} (risk {gp_risk:.1f}) decayed by {(decay**2):.2f}",
                        })

        # Cap contextual network risk between 0 and 100
        network_contextual_risk = min(100.0, round(accumulated_contextual_risk, 2))

        # Composite Propagated Risk blends direct risk, behavioural risk, and contextual network risk
        composite_propagated_risk = round(
            0.40 * direct_tx_risk + 
            0.30 * account_behav_risk + 
            0.30 * network_contextual_risk, 
            2
        )
        composite_propagated_risk = min(100.0, max(0.0, composite_propagated_risk))

        is_elevated = bool(network_contextual_risk >= cfg["contextual_risk_threshold"])

        return {
            "account_id": account_id,
            "bank": g.nodes[account_id].get("bank", "UNKNOWN"),
            "direct_transaction_risk": round(direct_tx_risk, 2),
            "account_behavioural_risk": round(account_behav_risk, 2),
            "network_contextual_risk": network_contextual_risk,
            "composite_propagated_risk": composite_propagated_risk,
            "propagation_sources": propagation_sources,
            "is_contextually_elevated": is_elevated,
            "upstream_predecessors_count": len(predecessors),
        }
