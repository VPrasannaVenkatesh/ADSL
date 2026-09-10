"""
GATv2 Graph Neural Network Model for Money Mule Detection.
Architecture: 3-layer Graph Attention Network (GATv2Conv) with classification head.

Input → GATv2(64, heads=4) → ELU → Dropout → GATv2(64, heads=2) → ELU → Dropout
     → GATv2(32, heads=1) → ELU → Linear(16) → ReLU → Linear(3) → Softmax

Classifies each account node as:
  0 = NORMAL
  1 = SUSPICIOUS
  2 = MULE
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import GATv2Conv, SAGEConv, global_mean_pool

from .config import (
    NODE_FEATURE_DIM,
    EDGE_FEATURE_DIM,
    NUM_CLASSES,
    GNN_HYPERPARAMS,
    GNN_MODEL_TYPE,
)


class GATv2MuleDetector(nn.Module):
    """
    Graph Attention Network v2 for node-level money mule classification.

    Uses 3 GATv2Conv layers with configurable hidden dimensions and attention heads.
    Outputs [N, 3] logits (NORMAL / SUSPICIOUS / MULE) for every node in the graph.
    """

    def __init__(
        self,
        node_feature_dim:   int = NODE_FEATURE_DIM,
        hidden_dim:         int = GNN_HYPERPARAMS["hidden_dim"],
        heads_l1:           int = GNN_HYPERPARAMS["heads_layer1"],
        heads_l2:           int = GNN_HYPERPARAMS["heads_layer2"],
        heads_l3:           int = GNN_HYPERPARAMS["heads_layer3"],
        dropout:            float = GNN_HYPERPARAMS["dropout"],
        num_classes:        int = NUM_CLASSES,
    ):
        super().__init__()

        self.dropout_rate = dropout

        # Input projection (normalise raw features)
        self.input_norm = nn.LayerNorm(node_feature_dim)

        # ── Layer 1: GATv2Conv ─────────────────────────────────────────────────
        # Output dim: hidden_dim * heads_l1 (concat=True)
        self.conv1 = GATv2Conv(
            in_channels=node_feature_dim,
            out_channels=hidden_dim,
            heads=heads_l1,
            concat=True,
            dropout=dropout,
            add_self_loops=True,
        )
        self.bn1 = nn.BatchNorm1d(hidden_dim * heads_l1)

        # ── Layer 2: GATv2Conv ─────────────────────────────────────────────────
        # Input: hidden_dim * heads_l1 → Output: hidden_dim * heads_l2 (concat=True)
        self.conv2 = GATv2Conv(
            in_channels=hidden_dim * heads_l1,
            out_channels=hidden_dim,
            heads=heads_l2,
            concat=True,
            dropout=dropout,
            add_self_loops=True,
        )
        self.bn2 = nn.BatchNorm1d(hidden_dim * heads_l2)

        # ── Layer 3: GATv2Conv ─────────────────────────────────────────────────
        # Input: hidden_dim * heads_l2 → Output: hidden_dim // 2 (concat=False → single head)
        out_l3 = hidden_dim // 2
        self.conv3 = GATv2Conv(
            in_channels=hidden_dim * heads_l2,
            out_channels=out_l3,
            heads=heads_l3,
            concat=False,
            dropout=dropout,
            add_self_loops=True,
        )
        self.bn3 = nn.BatchNorm1d(out_l3)

        # ── Classification Head ────────────────────────────────────────────────
        self.fc1 = nn.Linear(out_l3, 16)
        self.fc2 = nn.Linear(16, num_classes)

        # Weight initialisation
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x:          Node feature matrix [N, node_feature_dim]
            edge_index: Edge connectivity [2, E]

        Returns:
            logits:     [N, 3] raw logits (use softmax for probabilities)
        """
        # Input normalisation
        x = self.input_norm(x)

        # ── Conv Layer 1 ───────────────────────────────────────────────────────
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)

        # ── Conv Layer 2 ───────────────────────────────────────────────────────
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)

        # ── Conv Layer 3 ───────────────────────────────────────────────────────
        x = self.conv3(x, edge_index)
        x = self.bn3(x)
        x = F.elu(x)

        # ── Classification Head ────────────────────────────────────────────────
        x = self.fc1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_rate * 0.5, training=self.training)
        logits = self.fc2(x)

        return logits   # [N, 3]

    def predict_proba(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Returns softmax probabilities [N, 3]."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x, edge_index)
            return F.softmax(logits, dim=-1)


class GraphSAGEMuleDetector(nn.Module):
    """
    GraphSAGE-based alternative model for money mule detection.
    Same task as GATv2MuleDetector, useful when attention overhead is a concern.
    """

    def __init__(
        self,
        node_feature_dim: int   = NODE_FEATURE_DIM,
        hidden_dim:       int   = GNN_HYPERPARAMS["hidden_dim"],
        dropout:          float = GNN_HYPERPARAMS["dropout"],
        num_classes:      int   = NUM_CLASSES,
    ):
        super().__init__()

        self.dropout_rate = dropout
        self.input_norm   = nn.LayerNorm(node_feature_dim)

        self.conv1 = SAGEConv(node_feature_dim, hidden_dim * 2)
        self.bn1   = nn.BatchNorm1d(hidden_dim * 2)

        self.conv2 = SAGEConv(hidden_dim * 2, hidden_dim)
        self.bn2   = nn.BatchNorm1d(hidden_dim)

        self.conv3 = SAGEConv(hidden_dim, hidden_dim // 2)
        self.bn3   = nn.BatchNorm1d(hidden_dim // 2)

        self.fc1 = nn.Linear(hidden_dim // 2, 16)
        self.fc2 = nn.Linear(16, num_classes)

    def forward(self, x, edge_index):
        x = self.input_norm(x)

        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)

        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_rate, training=self.training)

        x = self.conv3(x, edge_index)
        x = self.bn3(x)
        x = F.relu(x)

        x = self.fc1(x)
        x = F.relu(x)
        logits = self.fc2(x)
        return logits

    def predict_proba(self, x, edge_index):
        self.eval()
        with torch.no_grad():
            return F.softmax(self.forward(x, edge_index), dim=-1)


def build_model(model_type: str = GNN_MODEL_TYPE) -> nn.Module:
    """Factory: returns GATv2MuleDetector or GraphSAGEMuleDetector."""
    if model_type.upper() == "GRAPHSAGE":
        return GraphSAGEMuleDetector()
    return GATv2MuleDetector()
