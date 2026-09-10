"""
Graph Feature Extractor for GNN-Based Money Mule Detection.
Extracts 22-dimensional node feature vectors and 10-dimensional edge feature vectors
from the live NetworkX transaction graph.

Extends the existing gnn_preparation.py tensors with richer behavioural and
topological features. Reuses existing graph engine, pattern detector, and
risk propagation modules.
"""

import math
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime

import networkx as nx

from .config import (
    NODE_FEATURE_NAMES,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_DIM,
    LABEL_THRESHOLDS,
    SUBGRAPH_CONFIG,
)


def _safe_log_norm(value: float, scale: float = 6.0) -> float:
    """Log-normalised value: log10(max(1, value)) / scale → [0, 1]."""
    return round(min(1.0, math.log10(max(1.0, float(value))) / scale), 5)


def _safe_norm(value: float, divisor: float) -> float:
    """Linear normalised value: value / divisor → [0, 1]."""
    if divisor <= 0:
        return 0.0
    return round(min(1.0, max(0.0, float(value) / divisor)), 5)


def extract_node_features(
    graph: nx.DiGraph,
    account_id: str,
    pagerank_scores: Optional[Dict[str, float]] = None,
    cycle_nodes: Optional[Set[str]] = None,
    max_degree: int = 20,
    max_amount: float = 1_000_000.0,
) -> List[float]:
    """
    Extracts a 22-dimensional feature vector for a single account node.
    Uses the live NetworkX graph and pre-computed optional metrics.

    Returns list of 22 floats in canonical NODE_FEATURE_NAMES order.
    """
    if not graph.has_node(account_id):
        return [0.0] * NODE_FEATURE_DIM

    n_data = graph.nodes[account_id]
    bank = str(n_data.get("bank", "")).upper()

    # Graph topology metrics
    in_deg  = graph.in_degree(account_id)
    out_deg = graph.out_degree(account_id)
    tot_deg = in_deg + out_deg

    # Incoming and outgoing edges with data
    in_edges  = list(graph.in_edges(account_id, data=True))
    out_edges = list(graph.out_edges(account_id, data=True))

    # [0] behavioural_risk_score
    behav_risk = float(n_data.get("risk_score", 0.0) or 0.0) / 100.0

    # [1] avg_tx_amount — mean over all adjacent edge amounts
    all_amounts = [float(d.get("amount", 0) or 0) for _, _, d in in_edges + out_edges]
    avg_amount_raw = sum(all_amounts) / max(1, len(all_amounts))
    avg_tx_amount = _safe_log_norm(avg_amount_raw)

    # [2] total_tx_count
    total_tx_count = _safe_norm(tot_deg, max_degree)

    # [3] sent_count
    sent_count = _safe_norm(out_deg, max(1, max_degree // 2))

    # [4] received_count
    received_count = _safe_norm(in_deg, max(1, max_degree // 2))

    # [5] unique_sender_count — unique predecessors
    unique_senders = len(set(u for u, _, _ in in_edges))
    unique_sender_count = _safe_norm(unique_senders, 10.0)

    # [6] unique_recipient_count — unique successors
    unique_recipients = len(set(v for _, v, _ in out_edges))
    unique_recipient_count = _safe_norm(unique_recipients, 10.0)

    # [7] fan_in_score
    fan_in_score = _safe_norm(in_deg, 10.0)

    # [8] fan_out_score
    fan_out_score = _safe_norm(out_deg, 10.0)

    # [9] short_dwell_count — edges where dwell_time < threshold
    short_dwell_thresh = LABEL_THRESHOLDS["short_dwell_seconds"]
    short_dwell_out = sum(
        1 for _, _, d in out_edges
        if 0 <= float(d.get("dwell_time_seconds", -1) or -1) <= short_dwell_thresh
    )
    short_dwell_in = sum(
        1 for _, _, d in in_edges
        if 0 <= float(d.get("dwell_time_seconds", -1) or -1) <= short_dwell_thresh
    )
    short_dwell_count = _safe_norm(short_dwell_out + short_dwell_in, 5.0)

    # [10] amount_split_flag — large inflow then multiple smaller outflows
    amount_split_flag = 0.0
    if in_edges and len(out_edges) >= 2:
        max_in_amt = max((float(d.get("amount", 0) or 0) for _, _, d in in_edges), default=0)
        out_amounts = [float(d.get("amount", 0) or 0) for _, _, d in out_edges]
        smaller_outs = [a for a in out_amounts if a < max_in_amt and a > 0]
        if len(smaller_outs) >= 2:
            amount_split_flag = 1.0

    # [11] cross_bank_tx_count
    cross_bank_edges = sum(
        1 for _, _, d in (in_edges + out_edges)
        if d.get("is_cross_bank", False)
    )
    cross_bank_tx_count = _safe_norm(cross_bank_edges, 10.0)

    # [12] is_monitored
    is_monitored = 1.0 if n_data.get("is_monitored") else 0.0

    # [13] degree_centrality — pre-computed or computed on the fly
    if graph.number_of_nodes() > 1:
        deg_cent = tot_deg / (graph.number_of_nodes() - 1)
    else:
        deg_cent = 0.0
    degree_centrality = round(min(1.0, deg_cent), 5)

    # [14] in_degree (normalised)
    in_degree = _safe_norm(in_deg, max_degree)

    # [15] out_degree (normalised)
    out_degree = _safe_norm(out_deg, max_degree)

    # [16] pagerank_score
    pagerank_score = 0.0
    if pagerank_scores and account_id in pagerank_scores:
        pagerank_score = round(min(1.0, float(pagerank_scores[account_id]) * 50.0), 5)

    # [17] risk_propagation_score — from node data if stored, else 0.0
    risk_propagation_score = float(n_data.get("propagated_risk", 0.0) or 0.0) / 100.0

    # [18–20] Bank one-hot encoding
    bank_sbi  = 1.0 if bank == "SBI"  else 0.0
    bank_axis = 1.0 if bank == "AXIS" else 0.0
    bank_iob  = 1.0 if bank == "IOB"  else 0.0

    # [21] has_cycle — participates in any detected cycle
    has_cycle = 1.0 if (cycle_nodes and account_id in cycle_nodes) else 0.0

    feature_vec = [
        behav_risk,           # [0]
        avg_tx_amount,        # [1]
        total_tx_count,       # [2]
        sent_count,           # [3]
        received_count,       # [4]
        unique_sender_count,  # [5]
        unique_recipient_count,# [6]
        fan_in_score,         # [7]
        fan_out_score,        # [8]
        short_dwell_count,    # [9]
        amount_split_flag,    # [10]
        cross_bank_tx_count,  # [11]
        is_monitored,         # [12]
        degree_centrality,    # [13]
        in_degree,            # [14]
        out_degree,           # [15]
        pagerank_score,       # [16]
        risk_propagation_score,# [17]
        bank_sbi,             # [18]
        bank_axis,            # [19]
        bank_iob,             # [20]
        has_cycle,            # [21]
    ]

    assert len(feature_vec) == NODE_FEATURE_DIM, (
        f"Node feature dim mismatch: got {len(feature_vec)}, expected {NODE_FEATURE_DIM}"
    )
    return feature_vec


def extract_edge_features(edge_data: dict) -> List[float]:
    """
    Extracts a 10-dimensional feature vector for a transaction edge.

    Returns list of 10 floats.
    """
    amount = float(edge_data.get("amount", 0) or 0)
    norm_amt = _safe_log_norm(amount)

    dwell = float(edge_data.get("dwell_time_seconds", -1.0) or -1.0)
    norm_dwell = round(min(1.0, dwell / 3600.0), 5) if dwell >= 0 else 1.0

    is_cross = 1.0 if edge_data.get("is_cross_bank") else 0.0

    tx_type = str(edge_data.get("transaction_type", "UPI")).upper()
    type_upi  = 1.0 if tx_type == "UPI"           else 0.0
    type_imps = 1.0 if tx_type == "IMPS"          else 0.0
    type_neft = 1.0 if tx_type == "NEFT"          else 0.0

    # [6] transaction risk estimate — fast proxy
    tx_risk_est = round(norm_amt * (1.5 if (dwell >= 0 and dwell < 60) else 1.0), 5)
    tx_risk_est = min(1.0, tx_risk_est)

    # [7] rapid_forwarding_flag — dwell < 60s
    rapid_fwd = 1.0 if (0 <= dwell < 60) else 0.0

    # [8] recipient_is_new
    recip_new = 1.0 if edge_data.get("recipient_is_new") else 0.0

    # [9] hour_of_day_normalized
    ts = edge_data.get("timestamp")
    hour_norm = 0.5
    if isinstance(ts, datetime):
        hour_norm = round(ts.hour / 23.0, 5)

    edge_vec = [
        norm_amt,     # [0]
        norm_dwell,   # [1]
        is_cross,     # [2]
        type_upi,     # [3]
        type_imps,    # [4]
        type_neft,    # [5]
        tx_risk_est,  # [6]
        rapid_fwd,    # [7]
        recip_new,    # [8]
        hour_norm,    # [9]
    ]

    assert len(edge_vec) == EDGE_FEATURE_DIM, (
        f"Edge feature dim mismatch: got {len(edge_vec)}, expected {EDGE_FEATURE_DIM}"
    )
    return edge_vec


def build_pyg_tensors_from_graph(
    graph: nx.DiGraph,
    lock: Optional[threading.RLock] = None,
) -> Dict[str, Any]:
    """
    Converts a NetworkX DiGraph into PyTorch Geometric-compatible tensors.
    Computes PageRank, cycle nodes, and max_degree once for the full graph,
    then calls extract_node_features() for each node.

    Returns:
        {
            "x":           List[List[float]]   shape [N, 22]
            "edge_index":  [List[int], List[int]]   shape [2, E]
            "edge_attr":   List[List[float]]   shape [E, 10]
            "node_mapping": {idx -> account_id}
            "num_nodes":   int
            "num_edges":   int
        }
    """
    ctx = lock if lock else threading.RLock()

    with ctx:
        nodes = list(graph.nodes())
        num_nodes = len(nodes)

        if num_nodes == 0:
            return {
                "x": [], "edge_index": [[], []], "edge_attr": [],
                "node_mapping": {}, "num_nodes": 0, "num_edges": 0,
            }

        node_to_idx = {n: i for i, n in enumerate(nodes)}
        idx_to_node = {i: n for n, i in node_to_idx.items()}

        # Pre-compute graph-level metrics once
        try:
            pagerank_scores = nx.pagerank(graph, alpha=0.85, max_iter=100)
        except Exception:
            pagerank_scores = {}

        cycle_nodes: Set[str] = set()
        try:
            for cycle in nx.simple_cycles(graph):
                cycle_nodes.update(cycle)
        except Exception:
            pass

        max_degree = max((graph.degree(n) for n in nodes), default=1)
        max_degree = max(max_degree, 1)

        # Build node feature matrix
        x_features: List[List[float]] = []
        for account_id in nodes:
            vec = extract_node_features(
                graph=graph,
                account_id=account_id,
                pagerank_scores=pagerank_scores,
                cycle_nodes=cycle_nodes,
                max_degree=max_degree,
            )
            x_features.append(vec)

        # Build edge index and edge attribute matrix
        edge_src: List[int] = []
        edge_dst: List[int] = []
        edge_attrs: List[List[float]] = []

        for u, v, e_data in graph.edges(data=True):
            if u in node_to_idx and v in node_to_idx:
                edge_src.append(node_to_idx[u])
                edge_dst.append(node_to_idx[v])
                edge_attrs.append(extract_edge_features(e_data))

        return {
            "x":            x_features,
            "edge_index":   [edge_src, edge_dst],
            "edge_attr":    edge_attrs,
            "node_mapping": idx_to_node,
            "num_nodes":    num_nodes,
            "num_edges":    len(edge_src),
            "cycle_nodes":  list(cycle_nodes),
            "pagerank":     pagerank_scores,
        }
