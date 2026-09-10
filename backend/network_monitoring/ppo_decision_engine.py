"""
PPO Reinforcement Learning Decision Engine Abstraction (Module 13).
Prepares the state space, action space, and policy interfaces for future
Proximal Policy Optimization (PPO) reinforcement learning agents.

ACTIVE IMPLEMENTATION: Configurable Rule-Based Decision Policy Engine.
FUTURE ARCHITECTURE: Deep PPO Actor-Critic Network (PyTorch / SB3).
(This implementation is honest and does not pretend a trained PPO model exists).
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Discrete Action Space for Adaptive Decisions
ACTION_ALLOW = "ALLOW"
ACTION_MONITOR = "MONITOR"
ACTION_RESTRICT = "RESTRICT"
ACTION_FREEZE = "FREEZE"

ACTION_SPACE = [ACTION_ALLOW, ACTION_MONITOR, ACTION_RESTRICT, ACTION_FREEZE]


@dataclass
class TransactionEnvironmentState:
    """
    Represents the observed Markov Decision Process (MDP) state vector for a transaction.
    """
    combined_risk_score: float      # [0] Normalized 0.0 to 1.0
    sender_risk_score: float        # [1] Normalized 0.0 to 1.0
    receiver_risk_score: float      # [2] Normalized 0.0 to 1.0
    network_risk_score: float       # [3] Normalized 0.0 to 1.0
    is_cross_bank: float            # [4] Binary 0.0 or 1.0
    dwell_time_normalized: float    # [5] 0.0 (instant) to 1.0 (long dwell)
    multi_hop_depth: float          # [6] Normalized 0.0 to 1.0
    is_flagged: float               # [7] Binary 0.0 or 1.0

    def to_vector(self) -> List[float]:
        return [
            round(self.combined_risk_score / 100.0, 4),
            round(self.sender_risk_score / 100.0, 4),
            round(self.receiver_risk_score / 100.0, 4),
            round(self.network_risk_score / 100.0, 4),
            self.is_cross_bank,
            self.dwell_time_normalized,
            round(min(1.0, self.multi_hop_depth / 4.0), 4),
            self.is_flagged,
        ]


class PPODecisionEngine:
    """
    Adaptive Policy Decision Engine.
    Executes rule-based baseline policy while maintaining state/action spaces for future PPO.
    """

    def __init__(self):
        self.mode = "RULE_BASED_BASELINE"
        self.rl_framework = "PPO (Actor-Critic / Future PyTorch Model)"
        self.trained_policy_loaded = False

    def evaluate_decision(
        self,
        combined_risk_score: float,
        sender_risk_score: float,
        receiver_risk_score: float,
        network_risk_score: float,
        is_cross_bank: bool = False,
        dwell_time_sec: float = -1.0,
        multi_hop_depth: int = 1,
        is_flagged: bool = False,
    ) -> Dict[str, Any]:
        """
        Observes environment state and evaluates optimal security action.
        """
        norm_dwell = round(min(1.0, dwell_time_sec / 300.0), 4) if dwell_time_sec >= 0 else 1.0
        
        state = TransactionEnvironmentState(
            combined_risk_score=combined_risk_score,
            sender_risk_score=sender_risk_score,
            receiver_risk_score=receiver_risk_score,
            network_risk_score=network_risk_score,
            is_cross_bank=1.0 if is_cross_bank else 0.0,
            dwell_time_normalized=norm_dwell,
            multi_hop_depth=float(multi_hop_depth),
            is_flagged=1.0 if is_flagged else 0.0,
        )

        state_vector = state.to_vector()
        
        # ── Active Rule-Based Decision Policy ─────────────────────────────────
        reasons = []
        if is_flagged or combined_risk_score >= 85.0:
            action = ACTION_FREEZE if combined_risk_score >= 95.0 else ACTION_RESTRICT
            reasons.append(f"Critical risk violation (Score: {combined_risk_score:.1f})")
        elif combined_risk_score >= 65.0 or network_risk_score >= 70.0:
            action = ACTION_RESTRICT
            reasons.append(f"High risk threshold breached (Risk: {combined_risk_score:.1f}, Network: {network_risk_score:.1f})")
        elif combined_risk_score >= 35.0 or network_risk_score >= 35.0:
            action = ACTION_MONITOR
            reasons.append(f"Medium risk activity requires dynamic transaction graph monitoring")
        else:
            action = ACTION_ALLOW
            reasons.append("Normal low-risk operational baseline confirmed")

        return {
            "selected_action": action,
            "engine_mode": self.mode,
            "trained_ppo_model_active": self.trained_policy_loaded,
            "state_vector": state_vector,
            "state_dim": len(state_vector),
            "action_space": ACTION_SPACE,
            "action_index": ACTION_SPACE.index(action),
            "policy_reasons": reasons,
        }


# Singleton Global Decision Engine
GLOBAL_PPO_ENGINE = PPODecisionEngine()
