"""
FastAPI Router for GNN-Based Money Mule Network Detection.
Exposes endpoints for model status, account analysis, network analysis,
flagged accounts, training triggers, and network summaries.

All endpoints are prefixed: /api/gnn
"""

import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from .predictor import GLOBAL_GNN_PREDICTOR
from .config import GNN_TRIGGER_LEVELS, GNN_TRIGGER_SCORE_THRESHOLD

gnn_router = APIRouter(prefix="/api/gnn", tags=["GNN Mule Network Detection"])


# ── Request / Response Models ──────────────────────────────────────────────────
class AnalyzeAccountRequest(BaseModel):
    account_id: str
    depth: int = 3


class AnalyzeNetworkRequest(BaseModel):
    transaction_id: str


class TrainRequest(BaseModel):
    model_type: str = "GATv2"
    epochs: int = 120


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_conns():
    """Gets active PostgreSQL connections from the simulator."""
    try:
        from simulator.db import get_all_connections
        return get_all_connections()
    except Exception:
        return {}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@gnn_router.get("/status")
def get_gnn_status():
    """
    Returns current GNN model status, architecture, and performance metrics.
    """
    return GLOBAL_GNN_PREDICTOR.get_status()


@gnn_router.post("/analyze-account")
def analyze_account(req: AnalyzeAccountRequest):
    """
    Runs GNN inference on the ego-subgraph around a given account.
    Returns classification (NORMAL/SUSPICIOUS/MULE), risk score, and explanations.
    """
    result = GLOBAL_GNN_PREDICTOR.predict_account(
        account_id=req.account_id,
        depth=req.depth,
    )

    # Optionally persist to DB
    if result.get("model_loaded") and result.get("classification") in ("SUSPICIOUS", "MULE"):
        _save_account_async(result, req.account_id)

    return result


@gnn_router.post("/analyze-network")
def analyze_network(req: AnalyzeNetworkRequest):
    """
    Runs GNN on the combined subgraph around both endpoints of a transaction.
    Returns per-node classifications, mule/suspicious account lists, and network pattern.
    """
    result = GLOBAL_GNN_PREDICTOR.predict_network(
        transaction_id=req.transaction_id,
    )

    # Persist network assessment
    if result.get("model_loaded") and result.get("node_count", 0) > 0:
        _save_network_async(result)

    return result


@gnn_router.get("/flagged-accounts")
def get_flagged_accounts(
    bank:  str = Query("ALL", description="Filter by bank: ALL, SBI, AXIS, IOB"),
    limit: int = Query(100, le=500),
    classification: str = Query("", description="Filter: MULE, SUSPICIOUS, or empty for both"),
):
    """
    Returns GNN-flagged accounts (SUSPICIOUS or MULE) from the last 24 hours.
    """
    conns = _get_conns()
    if not conns:
        # Fallback: return live graph accounts with high GNN score
        return {"accounts": [], "total": 0, "message": "DB connections not available"}

    from .storage import fetch_gnn_flagged_accounts
    accounts = fetch_gnn_flagged_accounts(conns, bank=bank, limit=limit)

    if classification in ("MULE", "SUSPICIOUS"):
        accounts = [a for a in accounts if a["classification"] == classification]

    return {
        "accounts": accounts,
        "total":    len(accounts),
        "bank":     bank,
    }


@gnn_router.get("/network-summary")
def get_network_summary():
    """
    Returns aggregate GNN network statistics: total nodes, edges, mule counts, etc.
    """
    conns = _get_conns()
    if not conns:
        # Return graph-only summary
        from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
        g = GLOBAL_NETWORK_GRAPH.get_summary_metrics()
        return {
            "total_graph_nodes":        g.get("total_accounts_in_graph", 0),
            "total_graph_edges":        g.get("total_transactions_in_graph", 0),
            "mule_accounts_24h":        0,
            "suspicious_accounts_24h":  0,
            "total_gnn_assessments":    0,
            "total_networks_analyzed":  0,
            "mule_networks_detected":   0,
        }

    from .storage import fetch_gnn_network_summary
    return fetch_gnn_network_summary(conns)


@gnn_router.get("/live-graph")
def get_live_graph_for_gnn():
    """
    Returns the current live graph topology with GNN-ready feature info.
    Useful for visualisation in the dashboard.
    """
    from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
    from .graph_features import build_pyg_tensors_from_graph
    from .labels import generate_labels

    with GLOBAL_NETWORK_GRAPH._lock:
        graph = GLOBAL_NETWORK_GRAPH.graph
        tensors = build_pyg_tensors_from_graph(graph, lock=GLOBAL_NETWORK_GRAPH._lock)

        # Run quick labelling for visualisation colour coding
        try:
            labels = generate_labels(graph)
        except Exception:
            labels = {}

        nodes = []
        for idx, account_id in tensors["node_mapping"].items():
            n_data = graph.nodes.get(account_id, {})
            label_int = labels.get(account_id, 0)
            nodes.append({
                "id":             account_id,
                "bank":           n_data.get("bank", ""),
                "risk_score":     n_data.get("risk_score", 0),
                "is_monitored":   n_data.get("is_monitored", False),
                "auto_label":     ["NORMAL", "SUSPICIOUS", "MULE"][label_int],
                "in_degree":      graph.in_degree(account_id),
                "out_degree":     graph.out_degree(account_id),
            })

        edges = []
        for u, v, d in graph.edges(data=True):
            edges.append({
                "source":       u,
                "target":       v,
                "amount":       d.get("amount", 0),
                "is_cross_bank": d.get("is_cross_bank", False),
                "dwell_time":   d.get("dwell_time_seconds", -1),
                "status":       d.get("status", ""),
            })

    return {
        "nodes":      nodes,
        "edges":      edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "model_status": GLOBAL_GNN_PREDICTOR.get_status().get("status", "NOT_TRAINED"),
    }


@gnn_router.post("/train")
def train_gnn_model(req: TrainRequest):
    """
    Triggers GNN training on the current live transaction graph.
    Runs synchronously (blocks until complete, ~30–90s on CPU).
    Returns training metrics after completion.
    """
    from .trainer import train_gnn
    try:
        metadata = train_gnn(
            model_type=req.model_type,
            epochs=req.epochs,
            verbose=True,
        )

        if "error" in metadata:
            raise HTTPException(status_code=400, detail=metadata["error"])

        # Reload the predictor with the new model
        GLOBAL_GNN_PREDICTOR.reload_model()

        return {
            "status":         "SUCCESS",
            "model_type":     metadata.get("model_type"),
            "model_version":  metadata.get("model_version"),
            "training_time_sec": metadata.get("training_time_sec"),
            "training_samples":  metadata.get("training_samples"),
            "label_distribution": metadata.get("label_distribution"),
            "validation_metrics": metadata.get("validation_metrics"),
            "test_metrics":      metadata.get("test_metrics"),
            "hyperparams":       metadata.get("hyperparams"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@gnn_router.get("/analyze-account/{account_id}")
def analyze_account_get(account_id: str, depth: int = Query(3, ge=1, le=4)):
    """GET convenience wrapper for account analysis."""
    result = GLOBAL_GNN_PREDICTOR.predict_account(account_id=account_id, depth=depth)
    return result


# ── Internal Async Persistence Helpers ────────────────────────────────────────

def _save_account_async(result: Dict[str, Any], trigger_tx_id: Optional[str] = None):
    """Fire-and-forget account assessment persistence."""
    try:
        conns = _get_conns()
        bank  = result.get("account_id", "").split("-")[0] if "-" in result.get("account_id", "") else "SBI"
        bank  = bank.upper()
        if bank not in conns:
            return

        from .storage import save_gnn_account_assessment
        save_gnn_account_assessment(
            conn=conns[bank],
            account_id=result["account_id"],
            bank=bank,
            classification=result.get("classification", "UNKNOWN"),
            mule_probability=result.get("mule_probability", 0.0),
            suspicious_probability=result.get("suspicious_probability", 0.0),
            normal_probability=result.get("normal_probability", 1.0),
            gnn_risk_score=result.get("gnn_risk_score", 0.0),
            risk_level=result.get("risk_level", "LOW"),
            network_pattern=result.get("network_pattern", "UNKNOWN"),
            connected_account_count=result.get("connected_account_count", 0),
            confidence=result.get("confidence", 0.0),
            explanation=result.get("explanation", []),
            model_version=result.get("model_version", "v1.0.0-gatv2"),
            trigger_transaction_id=trigger_tx_id,
        )
    except Exception as e:
        print(f"[GNN API] _save_account_async error: {e}")


def _save_network_async(result: Dict[str, Any]):
    """Fire-and-forget network assessment persistence."""
    try:
        conns = _get_conns()
        if not conns:
            return

        # Save to sender bank
        sender_id = result.get("sender_id", "")
        bank = sender_id.split("-")[0].upper() if "-" in sender_id else "SBI"
        conn = conns.get(bank) or list(conns.values())[0]

        from .storage import save_gnn_network_assessment
        save_gnn_network_assessment(
            conn=conn,
            trigger_transaction_id=result.get("transaction_id", ""),
            node_count=result.get("node_count", 0),
            edge_count=result.get("edge_count", 0),
            mule_accounts_detected=len(result.get("mule_accounts", [])),
            suspicious_accounts_detected=len(result.get("suspicious_accounts", [])),
            network_pattern=result.get("network_pattern", "UNKNOWN"),
            network_risk_score=result.get("network_risk_score", 0.0),
            node_classifications=result.get("node_classifications", {}),
        )
    except Exception as e:
        print(f"[GNN API] _save_network_async error: {e}")
