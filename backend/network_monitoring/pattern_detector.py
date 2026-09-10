"""
Graph Pattern Detector & Dynamic Network Risk Scorer.
Identifies multi-hop chains, fan-in, fan-out, rapid short-dwell forwarding,
amount splitting, and circular loops to compute a dynamic network risk score.
"""

from typing import Dict, List, Any, Tuple
import networkx as nx

from .config import GRAPH_MONITORING_CONFIG
from .graph_engine import TransactionNetworkGraph, GLOBAL_NETWORK_GRAPH


def analyze_connected_network_risk(
    account_id: str,
    graph_instance: TransactionNetworkGraph = GLOBAL_NETWORK_GRAPH,
    current_tx_dwell_sec: float = -1.0,
) -> Dict[str, Any]:
    """
    Analyzes the 2-to-3 hop connected subgraph around account_id.
    Computes topological risk indicators, dynamic network score, and escalation recommendations.
    """
    sub = graph_instance.get_connected_subgraph(account_id, depth=GRAPH_MONITORING_CONFIG["max_subgraph_depth"])
    if not sub.has_node(account_id) or sub.number_of_nodes() <= 1:
        return {
            "network_risk_score": 0.0,
            "should_escalate": False,
            "detected_patterns": [],
            "reasons": ["Single isolated transaction; no connected graph anomalies."],
            "subgraph_nodes_count": 1,
            "subgraph_edges_count": 0,
            "chains_count": 0,
        }

    detected_patterns = []
    reasons = []

    # ── 1. Multi-Hop Chain Detection ─────────────────────────────────────────
    chains = graph_instance.extract_chains_around_account(account_id, max_depth=3)
    max_chain_len = max((len(c) for c in chains), default=1)
    
    chain_score = 0.0
    if max_chain_len >= 4:
        chain_score = 90.0
        detected_patterns.append("EXTENDED_MULTI_HOP_CHAIN")
        reasons.append(f"Deep multi-hop chain detected ({max_chain_len} continuous transaction hops)")
    elif max_chain_len == 3:
        chain_score = 65.0
        detected_patterns.append("MULTI_HOP_RELAY")
        reasons.append(f"3-hop transaction relay detected across connected accounts")
    elif max_chain_len == 2:
        chain_score = 30.0

    # ── 2. Short Dwell Time (Rapid Inflow-to-Outflow) ─────────────────────────
    dwell_score = 0.0
    dwell_thresh = GRAPH_MONITORING_CONFIG["short_dwell_seconds_threshold"]
    
    # Check dwell times on local edges
    short_dwell_count = sum(
        1 for _, _, d in sub.edges(data=True)
        if 0 <= d.get("dwell_time_seconds", -1) <= dwell_thresh
    )
    if current_tx_dwell_sec >= 0 and current_tx_dwell_sec <= dwell_thresh:
        short_dwell_count += 1

    if short_dwell_count >= 2:
        dwell_score = 95.0
        detected_patterns.append("REPEATED_SHORT_DWELL_FORWARDING")
        reasons.append(f"Repeated rapid pass-through: Funds forwarded in <{dwell_thresh}s across multiple hops")
    elif short_dwell_count == 1:
        dwell_score = 60.0
        detected_patterns.append("SHORT_DWELL_FORWARDING")
        reasons.append(f"Rapid fund forwarding within {int(current_tx_dwell_sec if current_tx_dwell_sec >= 0 else dwell_thresh)}s of receipt")

    # ── 3. Fan-In & Fan-Out Hub Topology ─────────────────────────────────────
    in_deg = sub.in_degree(account_id)
    out_deg = sub.out_degree(account_id)
    fan_score = 0.0

    if in_deg >= 3 and out_deg >= 2:
        fan_score = 85.0
        detected_patterns.append("FAN_IN_FAN_OUT_HUB")
        reasons.append(f"Hub relay structure: Receiving from {in_deg} accounts and distributing to {out_deg} accounts")
    elif in_deg >= 3:
        fan_score = 60.0
        detected_patterns.append("FAN_IN_AGGREGATION")
        reasons.append(f"Fan-in collection: Concentrating funds from {in_deg} distinct accounts")
    elif out_deg >= 3:
        fan_score = 60.0
        detected_patterns.append("FAN_OUT_DISPERSION")
        reasons.append(f"Fan-out dispersion: Dispersing funds to {out_deg} distinct accounts")

    # ── 4. Amount Splitting Detection ────────────────────────────────────────
    split_score = 0.0
    in_amounts = [d.get("amount", 0) for _, v, d in sub.in_edges(account_id, data=True)]
    out_amounts = [d.get("amount", 0) for u, _, d in sub.out_edges(account_id, data=True)]

    if in_amounts and len(out_amounts) >= 2:
        max_in = max(in_amounts)
        smaller_outs = [amt for amt in out_amounts if amt < max_in]
        if len(smaller_outs) >= 2:
            split_score = 80.0
            detected_patterns.append("AMOUNT_SPLITTING")
            reasons.append(f"Amount splitting: Inflow of ₹{max_in:,} broken into {len(smaller_outs)} smaller outflows")

    # ── 5. Circular Flow Detection (Cycles) ──────────────────────────────────
    cycle_score = 0.0
    try:
        cycles = list(nx.simple_cycles(sub))
        if any(account_id in c for c in cycles):
            cycle_score = 95.0
            detected_patterns.append("CIRCULAR_FLOW_LOOP")
            reasons.append("Circular flow loop detected: Funds routed through a closed multi-bank cycle")
    except Exception:
        pass

    # ── 6. Weighted Network Risk Aggregation ─────────────────────────────────
    w = GRAPH_MONITORING_CONFIG["weights"]
    net_score = (
        (dwell_score * w["short_dwell_weight"]) +
        (split_score * w["amount_split_weight"]) +
        (chain_score * w["multi_hop_chain_weight"]) +
        (fan_score * w["fan_in_out_weight"]) +
        (cycle_score * w["circular_flow_weight"])
    )
    net_score = round(min(100.0, max(0.0, net_score)), 1)

    # Escalation Rule: Escalates from MONITORING to RESTRICTED if network threshold exceeded
    escalate_thresh = GRAPH_MONITORING_CONFIG["network_escalation_score_threshold"]
    should_escalate = (
        net_score >= escalate_thresh or
        "CIRCULAR_FLOW_LOOP" in detected_patterns or
        ("REPEATED_SHORT_DWELL_FORWARDING" in detected_patterns and "EXTENDED_MULTI_HOP_CHAIN" in detected_patterns)
    )

    if should_escalate and "Escalation" not in str(reasons):
        reasons.insert(0, f"⚠️ Network risk threshold exceeded (Score: {net_score}/100) — Escalated to RESTRICTED")

    if not reasons:
        reasons.append("Connected subgraph monitored; no malicious structural patterns identified.")

    return {
        "network_risk_score": net_score,
        "should_escalate": should_escalate,
        "detected_patterns": detected_patterns,
        "reasons": reasons,
        "subgraph_nodes_count": sub.number_of_nodes(),
        "subgraph_edges_count": sub.number_of_edges(),
        "chains_count": len(chains),
        "active_chains": chains[:3],
    }
