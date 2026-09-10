"""
GNN Dataset Builder.
Converts the live NetworkX transaction graph into PyTorch Geometric Data objects
for GNN training, validation, and testing.

Strategy:
  - Uses the GLOBAL_NETWORK_GRAPH (live in-memory graph from simulator).
  - Also queries PostgreSQL behaviour_history for richer account-level features.
  - Labels derived from graph topology (labels.py).
  - Time-based split to prevent data leakage across train/val/test.
  - Returns augmented subgraphs if full graph is too small for training.
"""

import random
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

import networkx as nx
import torch
from torch_geometric.data import Data

from .config import (
    DATASET_SPLITS,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_DIM,
    LABEL_NORMAL,
    LABEL_SUSPICIOUS,
    LABEL_MULE,
    NUM_CLASSES,
)
from .graph_features import build_pyg_tensors_from_graph
from .labels import generate_labels


def _nx_to_pyg_data(
    graph: nx.DiGraph,
    labels: Optional[Dict[str, int]] = None,
) -> Optional[Data]:
    """
    Converts a NetworkX DiGraph to a torch_geometric.data.Data object.
    If labels is None, generates them from topology.
    Returns None if graph has fewer than 2 nodes.
    """
    if graph.number_of_nodes() < 2:
        return None

    tensors = build_pyg_tensors_from_graph(graph)
    num_nodes = tensors["num_nodes"]
    node_mapping = tensors["node_mapping"]

    if num_nodes < 2:
        return None

    # Build node label tensor
    if labels is None:
        labels = generate_labels(graph)

    y_list = []
    for idx in range(num_nodes):
        account_id = node_mapping[idx]
        y_list.append(labels.get(account_id, LABEL_NORMAL))

    # Node features tensor [N, 22]
    x = torch.tensor(tensors["x"], dtype=torch.float)

    # Edge index tensor [2, E]
    ei = tensors["edge_index"]
    if not ei[0]:
        # No edges — add self-loops for single-node graphs
        idx_list = list(range(num_nodes))
        edge_index = torch.tensor([idx_list, idx_list], dtype=torch.long)
        edge_attr  = torch.zeros((num_nodes, EDGE_FEATURE_DIM), dtype=torch.float)
    else:
        edge_index = torch.tensor(ei, dtype=torch.long)
        edge_attr  = torch.tensor(tensors["edge_attr"], dtype=torch.float)

    y = torch.tensor(y_list, dtype=torch.long)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
        num_nodes=num_nodes,
    )
    # Store account mapping for inference
    data.node_mapping = node_mapping
    return data


def _split_by_time(
    graph: nx.DiGraph,
    train_ratio: float = DATASET_SPLITS["train"],
    val_ratio: float   = DATASET_SPLITS["val"],
) -> Tuple[nx.DiGraph, nx.DiGraph, nx.DiGraph]:
    """
    Splits the transaction graph by edge timestamp into train/val/test subgraphs.
    Nodes that only appear in val/test are excluded from training.
    """
    edges_with_ts = []
    for u, v, d in graph.edges(data=True):
        ts = d.get("timestamp")
        if isinstance(ts, datetime):
            edges_with_ts.append((u, v, d, ts))
        else:
            edges_with_ts.append((u, v, d, datetime.min))

    # Sort by timestamp
    edges_with_ts.sort(key=lambda e: e[3])
    n = len(edges_with_ts)

    if n < 6:
        # Too few edges — use full graph for all splits
        data = _nx_to_pyg_data(graph)
        if data is None:
            return nx.DiGraph(), nx.DiGraph(), nx.DiGraph()
        # Return same graph for train/val/test (small dataset)
        return graph, graph, graph

    train_end = int(n * train_ratio)
    val_end   = int(n * (train_ratio + val_ratio))

    train_edges = edges_with_ts[:train_end]
    val_edges   = edges_with_ts[train_end:val_end]
    test_edges  = edges_with_ts[val_end:]

    def _build_subgraph(edge_list):
        g = nx.DiGraph()
        for u, v, d, _ in edge_list:
            g.add_node(u, **graph.nodes.get(u, {"bank": "SBI"}))
            g.add_node(v, **graph.nodes.get(v, {"bank": "SBI"}))
            g.add_edge(u, v, **d)
        return g

    return (
        _build_subgraph(train_edges),
        _build_subgraph(val_edges),
        _build_subgraph(test_edges),
    )


def _augment_with_subgraphs(
    graph: nx.DiGraph,
    labels: Dict[str, int],
    num_subgraphs: int = 20,
    min_nodes: int     = 10,
    max_nodes: int     = 80,
) -> List[Data]:
    """
    Creates multiple training Data objects by sampling random ego-subgraphs.
    Prevents overfitting to the full graph structure and improves generalisation.
    """
    all_nodes = list(graph.nodes())
    if len(all_nodes) < min_nodes:
        return []

    aug_data_list = []
    for _ in range(num_subgraphs):
        # Pick a random seed node — prefer MULE/SUSPICIOUS for balance
        mule_nodes = [n for n in all_nodes if labels.get(n, 0) == LABEL_MULE]
        if mule_nodes and random.random() < 0.5:
            seed = random.choice(mule_nodes)
        else:
            seed = random.choice(all_nodes)

        # Ego subgraph up to 3 hops
        visited = {seed}
        current_layer = {seed}
        for _ in range(3):
            next_layer = set()
            for n in current_layer:
                next_layer.update(graph.successors(n))
                next_layer.update(graph.predecessors(n))
            next_layer -= visited
            visited.update(next_layer)
            current_layer = next_layer
            if len(visited) >= max_nodes or not current_layer:
                break

        if len(visited) < 3:
            continue

        # Trim to max_nodes
        if len(visited) > max_nodes:
            visited = set(list(visited)[:max_nodes])

        sub = graph.subgraph(visited).copy()
        sub_labels = {n: labels.get(n, LABEL_NORMAL) for n in sub.nodes()}
        data = _nx_to_pyg_data(sub, labels=sub_labels)
        if data is not None:
            aug_data_list.append(data)

    return aug_data_list


def build_dataset(
    graph: Optional[nx.DiGraph] = None,
) -> Dict[str, Any]:
    """
    Main dataset builder.
    
    1. Uses the provided graph (or GLOBAL_NETWORK_GRAPH).
    2. Generates topology-based labels.
    3. Splits by time into train/val/test.
    4. Augments training set with random subgraphs.
    5. Returns PyG Data objects + label distribution stats.

    Returns:
        {
            "train_data":   Data,
            "val_data":     Data,
            "test_data":    Data,
            "aug_data":     List[Data],
            "full_labels":  Dict[account_id, int],
            "label_dist":   Dict[str, int],
            "num_nodes":    int,
            "num_edges":    int,
        }
    """
    if graph is None:
        from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
        graph = GLOBAL_NETWORK_GRAPH.graph

    if graph.number_of_nodes() < 4:
        # Hydrate from PostgreSQL bank transactions
        try:
            from simulator.db_connection import get_bank_connection, BANK_NAMES
            from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
            for b_name in BANK_NAMES:
                try:
                    conn = get_bank_connection(b_name)
                    cur = conn.cursor()
                    cur.execute("SELECT transaction_id, sender_account_id, receiver_account_id, sender_bank, receiver_bank, amount, transaction_type, transaction_timestamp FROM transactions ORDER BY transaction_timestamp DESC LIMIT 500")
                    rows = cur.fetchall()
                    for r in rows:
                        GLOBAL_NETWORK_GRAPH.add_account_node(r[1], r[3] or b_name)
                        GLOBAL_NETWORK_GRAPH.add_account_node(r[2], r[4] or b_name)
                        GLOBAL_NETWORK_GRAPH.add_transaction_edge({
                            "transaction_id": str(r[0]),
                            "sender_account_id": str(r[1]),
                            "receiver_account_id": str(r[2]),
                            "sender_bank": str(r[3] or b_name),
                            "receiver_bank": str(r[4] or b_name),
                            "amount": float(r[5] or 1000),
                            "transaction_type": str(r[6] or "TRANSFER"),
                            "transaction_timestamp": r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]),
                        })
                    cur.close()
                    conn.close()
                except Exception as inner_e:
                    print(f"[GNN Dataset] DB hydration for {b_name} error: {inner_e}")
            graph = GLOBAL_NETWORK_GRAPH.graph
        except Exception as e:
            print(f"[GNN Dataset] DB hydration error: {e}")

    if graph.number_of_nodes() < 4:
        print("[GNN Dataset] Graph too small — need at least 4 nodes for training.")
        return {
            "train_data": None, "val_data": None, "test_data": None,
            "aug_data": [], "full_labels": {}, "label_dist": {},
            "num_nodes": 0, "num_edges": 0,
        }

    print(f"[GNN Dataset] Building from graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    # Generate labels for full graph
    full_labels = generate_labels(graph)
    label_counts = {}
    for v in full_labels.values():
        label_counts[v] = label_counts.get(v, 0) + 1
    print(f"[GNN Dataset] Label distribution: NORMAL={label_counts.get(0,0)}, SUSPICIOUS={label_counts.get(1,0)}, MULE={label_counts.get(2,0)}")

    # Time-based split
    train_g, val_g, test_g = _split_by_time(graph)

    # Convert splits to PyG Data objects
    train_data = _nx_to_pyg_data(
        train_g,
        labels={n: full_labels.get(n, LABEL_NORMAL) for n in train_g.nodes()}
    ) if train_g.number_of_nodes() >= 2 else None

    val_data = _nx_to_pyg_data(
        val_g,
        labels={n: full_labels.get(n, LABEL_NORMAL) for n in val_g.nodes()}
    ) if val_g.number_of_nodes() >= 2 else None

    test_data = _nx_to_pyg_data(
        test_g,
        labels={n: full_labels.get(n, LABEL_NORMAL) for n in test_g.nodes()}
    ) if test_g.number_of_nodes() >= 2 else None

    # Augment training set with random ego-subgraphs
    aug_data = _augment_with_subgraphs(
        graph,
        full_labels,
        num_subgraphs=30,
        min_nodes=6,
        max_nodes=100,
    )
    print(f"[GNN Dataset] Augmented with {len(aug_data)} additional subgraph samples.")

    from .labels import get_label_distribution
    label_dist = get_label_distribution(full_labels)

    return {
        "train_data": train_data,
        "val_data":   val_data,
        "test_data":  test_data,
        "aug_data":   aug_data,
        "full_labels": full_labels,
        "label_dist":  label_dist,
        "num_nodes":   graph.number_of_nodes(),
        "num_edges":   graph.number_of_edges(),
    }
