"""
Configuration for Real-Time Transaction Lifecycle & Graph-Based Network Monitoring.
Configurable thresholds, lifecycle state definitions, and graph analysis parameters.
"""

from typing import Dict, Any

# ── 1. Transaction Lifecycle Statuses ──────────────────────────────────────────
LIFECYCLE_STATUSES = {
    "INITIATED": {
        "label": "Initiated",
        "description": "Transaction initiated and balance verified. Awaiting risk scoring.",
        "color": "#06B6D4",      # Cyan
        "badge_class": "badge-INITIATED",
    },
    "PROCESSING": {
        "label": "Processing",
        "description": "Risk evaluation and decentralized coordination in progress.",
        "color": "#8B5CF6",      # Purple / Violet
        "badge_class": "badge-PROCESSING",
    },
    "ASSESSING": {
        "label": "Assessing",
        "description": "Sender and receiver behavioural risk calculations in progress.",
        "color": "#8B5CF6",      # Purple / Violet
        "badge_class": "badge-ASSESSING",
    },
    "COMPLETED": {
        "label": "Completed",
        "description": "Low risk consensus confirmed (< 30). Transaction approved and committed.",
        "color": "#10B981",      # Emerald Green
        "badge_class": "badge-COMPLETED",
    },
    "MONITORING": {
        "label": "Monitoring",
        "description": "Moderate risk (30-50). Approved with dynamic graph monitoring.",
        "color": "#F59E0B",      # Amber / Yellow
        "badge_class": "badge-MONITORING",
    },
    "UNDER_REVIEW": {
        "label": "Under Review",
        "description": "Suspicious risk (50-85). Lien applied; funds temporarily held for Admin investigation.",
        "color": "#C084FC",      # Bright Violet / Purple
        "badge_class": "badge-UNDER_REVIEW",
    },
    "RESTRICTED": {
        "label": "Restricted",
        "description": "High / Critical risk (85-95). Funds controlled and blocked under AML policy.",
        "color": "#EF4444",      # Red
        "badge_class": "badge-RESTRICTED",
    },
    "FROZEN": {
        "label": "Frozen",
        "description": "Severe fraud / ATO confirmed (>= 95). Account and transaction completely frozen.",
        "color": "#DC2626",      # Deep Crimson
        "badge_class": "badge-FROZEN",
    },
    "RELEASED": {
        "label": "Released",
        "description": "Admin approved and released from lien hold -> Committed to Completed.",
        "color": "#14B8A6",      # Teal
        "badge_class": "badge-RELEASED",
    },
}

# ── 2. ADSL Risk Thresholds (Configurable per Section 12) ─────────────────────
ALLOW_THRESHOLD = 30.0       # < 30 -> COMPLETED
MONITOR_THRESHOLD = 50.0     # 30 to 50 -> MONITORING
REVIEW_THRESHOLD = 70.0      # 50 to 85 -> UNDER_REVIEW (Lien applied)
RESTRICT_THRESHOLD = 85.0    # 85 to 95 -> RESTRICTED
FREEZE_THRESHOLD = 95.0      # >= 95 -> FROZEN

# ── 3. Risk Decision to Lifecycle Status Mapping ──────────────────────────────
DECISION_TO_STATUS = {
    "ALLOW": "COMPLETED",
    "MONITOR": "MONITORING",
    "REVIEW": "UNDER_REVIEW",
    "UNDER_REVIEW": "UNDER_REVIEW",
    "RESTRICT": "RESTRICTED",
    "CONTROLLED_ACTION": "RESTRICTED",
    "FREEZE": "FROZEN",
    "RELEASE": "RELEASED",
}

# ── 3. Graph-Based Network Monitoring Parameters ──────────────────────────────
GRAPH_MONITORING_CONFIG: Dict[str, Any] = {
    "max_subgraph_depth": 3,              # Max hops to traverse for connected analysis
    "max_history_transactions": 2500,     # In-memory graph rolling window
    "min_chain_length_for_alert": 3,      # Multi-hop chain threshold (e.g. A->B->C->D)
    
    # Network Risk Weights
    "weights": {
        "short_dwell_weight": 0.25,        # Rapid incoming-to-outgoing velocity (< 60s)
        "amount_split_weight": 0.20,       # Inflow split into multiple smaller outflows
        "multi_hop_chain_weight": 0.20,    # Relay chain length >= 3
        "fan_in_out_weight": 0.20,         # Aggregation & dispersion ratio
        "circular_flow_weight": 0.15,      # Closed loops (A->B->C->A)
    },
    
    # Dynamic Network Escalation Threshold
    # If dynamic network risk exceeds this, escalate from MONITORING to RESTRICTED
    "network_escalation_score_threshold": 72.0,
    
    # Short dwell threshold in seconds for rapid forwarding
    "short_dwell_seconds_threshold": 120,
}
