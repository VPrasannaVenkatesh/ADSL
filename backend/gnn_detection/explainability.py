"""
GNN Explainability Engine.
Generates human-readable natural language explanations for every GNN prediction.
Uses graph topology analysis — NOT attention weights (for speed and reliability).
"""

from typing import List, Dict, Any
import networkx as nx

from .config import LABEL_THRESHOLDS


def generate_explanation(
    graph: nx.DiGraph,
    account_id: str,
    classification: str,
    mule_probability: float,
    gnn_risk_score: float,
) -> List[str]:
    """
    Generates a list of human-readable explanation strings for a GNN prediction.
    Each string describes a specific structural reason why the account was flagged.

    Args:
        graph:             NetworkX subgraph around the account
        account_id:        The account being explained
        classification:    "NORMAL", "SUSPICIOUS", or "MULE"
        mule_probability:  Raw mule probability from the model
        gnn_risk_score:    GNN risk score 0–100

    Returns:
        List of explanation strings (maximum 6)
    """
    reasons: List[str] = []
    thresh  = LABEL_THRESHOLDS["short_dwell_seconds"]

    if not graph.has_node(account_id):
        if classification == "NORMAL":
            reasons.append("Account has limited transaction history. Low network risk observed.")
        return reasons

    in_edges  = list(graph.in_edges(account_id, data=True))
    out_edges = list(graph.out_edges(account_id, data=True))
    in_deg    = len(in_edges)
    out_deg   = len(out_edges)
    tot_deg   = in_deg + out_deg

    # ── Detect rapid forwarding ─────────────────────────────────────────────────
    rapid_out = [
        d for _, _, d in out_edges
        if 0 <= float(d.get("dwell_time_seconds", -1) or -1) <= thresh
    ]
    if rapid_out:
        avg_dwell = sum(float(d.get("dwell_time_seconds", thresh)) for d in rapid_out) / len(rapid_out)
        reasons.append(
            f"Account rapidly forwarded funds within {int(avg_dwell)}s of receipt "
            f"({len(rapid_out)} rapid transfer{'s' if len(rapid_out) > 1 else ''} detected)."
        )

    # ── Fan-in detection ─────────────────────────────────────────────────────────
    if in_deg >= 3:
        unique_senders = len(set(u for u, _, _ in in_edges))
        cross_bank_in  = sum(1 for _, _, d in in_edges if d.get("is_cross_bank"))
        reasons.append(
            f"Mule risk elevated: account received funds from {unique_senders} distinct "
            f"sender{'s' if unique_senders > 1 else ''}"
            + (f" ({cross_bank_in} cross-bank)" if cross_bank_in > 0 else "") + "."
        )

    # ── Fan-out detection ─────────────────────────────────────────────────────────
    if out_deg >= 3:
        unique_recipients = len(set(v for _, v, _ in out_edges))
        reasons.append(
            f"Account dispersed funds to {unique_recipients} distinct recipient"
            f"{'s' if unique_recipients > 1 else ''} (fan-out distribution pattern)."
        )

    # ── Amount splitting ─────────────────────────────────────────────────────────
    if in_edges and len(out_edges) >= 2:
        max_in = max((float(d.get("amount", 0) or 0) for _, _, d in in_edges), default=0)
        out_amts = [float(d.get("amount", 0) or 0) for _, _, d in out_edges]
        smaller_outs = [a for a in out_amts if 0 < a < max_in]
        if len(smaller_outs) >= 2:
            reasons.append(
                f"Amount splitting detected: received ₹{int(max_in):,} then split into "
                f"{len(smaller_outs)} smaller outflows (potential smurfing / structuring)."
            )

    # ── Circular flow detection ──────────────────────────────────────────────────
    try:
        cycles = [c for c in nx.simple_cycles(graph) if account_id in c]
        if cycles:
            cycle_len = len(cycles[0])
            cycle_accounts = " → ".join(cycles[0][:4])
            if len(cycles[0]) > 4:
                cycle_accounts += " → …"
            reasons.append(
                f"Circular fund flow detected: account participates in a {cycle_len}-node "
                f"closed loop ({cycle_accounts})."
            )
    except Exception:
        pass

    # ── High-risk cluster ─────────────────────────────────────────────────────────
    neighbour_risk_scores = []
    for n in graph.nodes():
        if n != account_id:
            r = float(graph.nodes[n].get("risk_score", 0.0) or 0.0)
            if r > 0:
                neighbour_risk_scores.append(r)

    if neighbour_risk_scores:
        avg_neighbour_risk = sum(neighbour_risk_scores) / len(neighbour_risk_scores)
        high_risk_neighbours = sum(1 for r in neighbour_risk_scores if r >= 50)
        if avg_neighbour_risk >= 40 or high_risk_neighbours >= 2:
            reasons.append(
                f"Account is located in a high-risk transaction cluster: "
                f"{high_risk_neighbours} connected account{'s' if high_risk_neighbours != 1 else ''} "
                f"have elevated behavioural risk (avg neighbour risk: {avg_neighbour_risk:.0f}/100)."
            )

    # ── Cross-bank activity ────────────────────────────────────────────────────
    cross_bank_total = sum(
        1 for _, _, d in (in_edges + out_edges)
        if d.get("is_cross_bank")
    )
    if cross_bank_total >= 3:
        reasons.append(
            f"Elevated cross-bank activity: {cross_bank_total} transactions span multiple banks, "
            f"consistent with cross-institution money movement layering."
        )

    # ── Normal account explanation ────────────────────────────────────────────
    if classification == "NORMAL" and not reasons:
        reasons.append(
            f"Account shows typical transaction patterns. "
            f"Network connectivity ({tot_deg} edges) and behavioural profile are within normal range."
        )

    if classification == "SUSPICIOUS" and not reasons:
        reasons.append(
            f"Account connectivity ({tot_deg} edges, {in_deg} in / {out_deg} out) is elevated "
            f"relative to normal accounts. Further monitoring recommended."
        )

    # ── Score-based summary ────────────────────────────────────────────────────
    if gnn_risk_score >= 81:
        reasons.insert(0, f"GNN Risk Score: {gnn_risk_score:.0f}/100 (CRITICAL) — "
                          f"Mule probability: {mule_probability * 100:.1f}%.")
    elif gnn_risk_score >= 61:
        reasons.insert(0, f"GNN Risk Score: {gnn_risk_score:.0f}/100 (HIGH) — "
                          f"Mule probability: {mule_probability * 100:.1f}%.")

    return reasons[:6]   # Maximum 6 reasons per account
