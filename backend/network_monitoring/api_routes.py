"""
FastAPI Router for Real-Time Network Graph Monitoring, Fund Provenance,
Risk Propagation, GNN Data Preparation, and Controlled Funds/Lien Layer.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel

from .graph_engine import GLOBAL_NETWORK_GRAPH
from .pattern_detector import analyze_connected_network_risk
from .fund_provenance import trace_fund_provenance
from .risk_propagation import calculate_network_risk_propagation
from .gnn_preparation import prepare_pyg_graph_representation
from .ppo_decision_engine import GLOBAL_PPO_ENGINE
from .lien_layer import GLOBAL_LIEN_LAYER

network_router = APIRouter(prefix="/api/network", tags=["Network Graph Monitoring"])


class ReleaseLienRequest(BaseModel):
    investigator_id: str
    reason: str


@network_router.get("/graph-summary")
def get_graph_summary():
    """Returns real-time topological statistics of the multi-bank transaction graph."""
    return GLOBAL_NETWORK_GRAPH.get_summary_metrics()


@network_router.get("/monitored")
def get_monitored_entities(limit: int = Query(50, le=200)):
    """Returns recent transactions and accounts currently placed under MONITORING."""
    monitored_txs = []
    for tx_id, edge_data in list(GLOBAL_NETWORK_GRAPH.transactions_by_id.items())[::-1]:
        if edge_data.get("status") in ("MONITORING", "UNDER_REVIEW", "RESTRICTED", "FROZEN", "RELEASED"):
            monitored_txs.append(edge_data)
            if len(monitored_txs) >= limit:
                break

    return {
        "monitored_transactions": monitored_txs,
        "monitored_accounts": list(GLOBAL_NETWORK_GRAPH.monitored_accounts)[:100],
        "count": len(monitored_txs),
    }


@network_router.get("/chains/{account_id}")
def get_account_chains(account_id: str, depth: int = Query(3, ge=1, le=4)):
    """Extracts all active multi-hop money flow chains involving the specified account."""
    chains = GLOBAL_NETWORK_GRAPH.extract_chains_around_account(account_id, max_depth=depth)
    return {
        "account_id": account_id,
        "chains": chains,
        "total_chains": len(chains),
    }


@network_router.get("/risk-analysis/{account_id}")
def get_network_risk_analysis(account_id: str):
    """Runs on-demand connected subgraph pattern detection and network scoring for an account."""
    analysis = analyze_connected_network_risk(account_id)
    return {
        "account_id": account_id,
        "analysis": analysis,
    }


@network_router.get("/subgraph/{account_id}")
def get_ego_subgraph(account_id: str, depth: int = Query(2, ge=1, le=3)):
    """Returns the ego-subgraph nodes and edges around the account for graph visualization."""
    sub = GLOBAL_NETWORK_GRAPH.get_connected_subgraph(account_id, depth=depth)
    nodes = []
    for n, d in sub.nodes(data=True):
        nodes.append({"id": n, **d})

    edges = []
    for u, v, d in sub.edges(data=True):
        edges.append({"source": u, "target": v, **d})

    return {
        "center_account": account_id,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


@network_router.get("/provenance/{account_id}")
def get_fund_provenance(account_id: str, max_hops: int = Query(3, ge=1, le=4)):
    """Traces multi-hop fund provenance: Source Account -> Intermediate Accounts -> Downstream Sinks."""
    return trace_fund_provenance(account_id=account_id, max_hops=max_hops)


@network_router.get("/propagation/{account_id}")
def get_risk_propagation(
    account_id: str,
    direct_risk: float = Query(0.0),
    behav_risk: float = Query(0.0),
):
    """Calculates controlled contextual risk propagation through connected relationships."""
    return calculate_network_risk_propagation(
        account_id=account_id,
        direct_tx_risk=direct_risk,
        account_behav_risk=behav_risk,
    )


@network_router.get("/gnn-representation")
def get_gnn_representation():
    """Returns PyTorch Geometric (PyG) compatible node/edge feature tensors."""
    return prepare_pyg_graph_representation()


@network_router.get("/ppo-evaluation/{account_id}")
def get_ppo_decision_evaluation(
    account_id: str,
    combined_risk: float = Query(50.0),
    sender_risk: float = Query(30.0),
    receiver_risk: float = Query(20.0),
    network_risk: float = Query(40.0),
    is_cross_bank: bool = Query(False),
):
    """Evaluates adaptive security policy action using the PPO environment state representation."""
    return GLOBAL_PPO_ENGINE.evaluate_decision(
        combined_risk_score=combined_risk,
        sender_risk_score=sender_risk,
        receiver_risk_score=receiver_risk,
        network_risk_score=network_risk,
        is_cross_bank=is_cross_bank,
    )


@network_router.get("/liens")
def get_liens(
    limit: int = Query(150, ge=1, le=500),
    status: Optional[str] = Query("ALL"),
    bank: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
):
    """Returns comprehensive statistics and total history of all controlled funds / lien holds."""
    metrics = GLOBAL_LIEN_LAYER.get_summary_metrics()
    history = GLOBAL_LIEN_LAYER.get_lien_history(limit=limit, status=status, bank=bank, search=search)
    metrics["all_liens"] = history
    metrics["recent_liens"] = history
    return metrics


@network_router.get("/liens/history")
def get_total_lien_history(
    limit: int = Query(150, ge=1, le=500),
    status: Optional[str] = Query("ALL"),
    bank: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
):
    """Returns detailed historical log of all liens, releases, and forensic notes."""
    return {
        "count": len(GLOBAL_LIEN_LAYER.active_liens),
        "history": GLOBAL_LIEN_LAYER.get_lien_history(limit=limit, status=status, bank=bank, search=search),
    }


@network_router.post("/liens/{lien_id}/release")
def release_lien(lien_id: str, req: ReleaseLienRequest):
    """Releases an active lien after investigation audit clearance."""
    released = GLOBAL_LIEN_LAYER.release_lien(
        lien_id=lien_id,
        investigator_id=req.investigator_id,
        reason=req.reason,
    )
    if not released:
        raise HTTPException(status_code=404, detail=f"Lien {lien_id} not found")
    return released
