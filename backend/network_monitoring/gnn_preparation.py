"""
GNN / GAT Data Preparation Layer (Module 12).
Prepares transaction graph data structures for future Graph Neural Network (GNN)
and Graph Attention Network (GAT) models with PyTorch Geometric (PyG) compatibility.

NOTE: This layer extracts node feature tensors and edge feature tensors formatted for PyG.
A trained GNN model does NOT yet exist; this module provides the rigorous tensor interface.
"""

from typing import Dict, List, Any, Tuple, Optional
import networkx as nx
from datetime import datetime

from .graph_engine import TransactionNetworkGraph, GLOBAL_NETWORK_GRAPH

# Canonical Node Feature Specification (Dim: 8)
# [0] account_risk_score (0.0 to 1.0)
# [1] degree_centrality
# [2] fan_in (in-degree normalized)
# [3] fan_out (out-degree normalized)
# [4] is_monitored (0.0 or 1.0)
# [5] bank_sbi (1.0 or 0.0)
# [6] bank_axis (1.0 or 0.0)
# [7] bank_iob (1.0 or 0.0)
NODE_FEATURE_DIM = 8

# Canonical Edge Feature Specification (Dim: 7)
# [0] normalized_amount (log scale)
# [1] dwell_time_normalized
# [2] is_cross_bank (1.0 or 0.0)
# [3] type_upi (1.0 or 0.0)
# [4] type_imps (1.0 or 0.0)
# [5] type_neft (1.0 or 0.0)
# [6] transaction_risk_estimate (0.0 to 1.0)
EDGE_FEATURE_DIM = 7


def prepare_pyg_graph_representation(
    subgraph: Optional[nx.DiGraph] = None,
    graph_instance: TransactionNetworkGraph = GLOBAL_NETWORK_GRAPH,
) -> Dict[str, Any]:
    """
    Extracts PyTorch Geometric compatible tensors from the NetworkX transaction graph:
    - x: Node feature matrix of shape [Num_Nodes, 8]
    - edge_index: Graph connectivity tensor of shape [2, Num_Edges]
    - edge_attr: Edge feature matrix of shape [Num_Edges, 7]
    - node_id_map: Maps node index -> account_id string
    """
    with graph_instance._lock:
        g = subgraph if subgraph is not None else graph_instance.graph
        nodes = list(g.nodes())
        num_nodes = len(nodes)
        
        if num_nodes == 0:
            return {
                "status": "ready_for_gnn",
                "trained_model_active": False,
                "architecture": "GATv2 / GraphSAGE (Future PyG Model)",
                "num_nodes": 0,
                "num_edges": 0,
                "x": [],
                "edge_index": [[], []],
                "edge_attr": [],
                "node_mapping": {},
            }

        # Build integer node mapping: account_id -> index
        node_to_idx = {account_id: i for i, account_id in enumerate(nodes)}
        idx_to_node = {i: account_id for account_id, i in node_to_idx.items()}

        # 1. Build Node Feature Matrix (x)
        x_features: List[List[float]] = []
        for account_id in nodes:
            n_data = g.nodes[account_id]
            bank = n_data.get("bank", "").upper()
            
            in_deg = g.in_degree(account_id)
            out_deg = g.out_degree(account_id)
            tot_deg = in_deg + out_deg
            
            risk_score = float(n_data.get("risk_score", 0.0) or 0.0) / 100.0
            is_mon = 1.0 if n_data.get("is_monitored") else 0.0

            node_vec = [
                round(risk_score, 4),
                round(min(1.0, tot_deg / 20.0), 4),
                round(min(1.0, in_deg / 10.0), 4),
                round(min(1.0, out_deg / 10.0), 4),
                is_mon,
                1.0 if bank == "SBI" else 0.0,
                1.0 if bank == "AXIS" else 0.0,
                1.0 if bank == "IOB" else 0.0,
            ]
            x_features.append(node_vec)

        # 2. Build Edge Index & Edge Attribute Matrix
        edge_src: List[int] = []
        edge_dst: List[int] = []
        edge_attrs: List[List[float]] = []

        import math
        for u, v, e_data in g.edges(data=True):
            src_idx = node_to_idx[u]
            dst_idx = node_to_idx[v]
            edge_src.append(src_idx)
            edge_dst.append(dst_idx)

            amt = float(e_data.get("amount", 0) or 0)
            norm_amt = round(min(1.0, math.log10(max(1.0, amt)) / 6.0), 4)  # Log-scale up to 10^6
            
            dwell = float(e_data.get("dwell_time_seconds", -1.0) or -1.0)
            norm_dwell = round(min(1.0, dwell / 3600.0), 4) if dwell >= 0 else 1.0
            
            is_cross = 1.0 if e_data.get("is_cross_bank") else 0.0
            tx_type = str(e_data.get("transaction_type", "UPI")).upper()
            
            edge_vec = [
                norm_amt,
                norm_dwell,
                is_cross,
                1.0 if tx_type == "UPI" else 0.0,
                1.0 if tx_type == "IMPS" else 0.0,
                1.0 if tx_type == "NEFT" else 0.0,
                round(norm_amt * (1.5 if norm_dwell < 0.05 else 1.0), 4),  # Estimated edge risk
            ]
            edge_attrs.append(edge_vec)

        return {
            "status": "ready_for_gnn",
            "trained_model_active": False,
            "architecture": "GATv2 / GraphSAGE (Future PyG Model)",
            "num_nodes": num_nodes,
            "num_edges": len(edge_src),
            "node_feature_dim": NODE_FEATURE_DIM,
            "edge_feature_dim": EDGE_FEATURE_DIM,
            "x": x_features,
            "edge_index": [edge_src, edge_dst],
            "edge_attr": edge_attrs,
            "node_mapping": idx_to_node,
        }
