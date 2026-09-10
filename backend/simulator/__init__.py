"""
Live Transaction Simulator Package for Behavioural Risk Analysis.
Supports multi-bank simulation across SBI, AXIS, and IOB PostgreSQL databases.
"""

from .config import SimulatorConfig, BANK_NAMES, SPEED_PRESETS
from .engine import LiveTransactionSimulator

__all__ = ["SimulatorConfig", "BANK_NAMES", "SPEED_PRESETS", "LiveTransactionSimulator"]
