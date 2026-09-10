# Configuration and constants for Live Transaction Simulator.

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

BANK_NAMES: List[str] = ["SBI", "AXIS", "IOB"]

ALL_BANK_PAIRS: List[Tuple[str, str]] = [
    ("SBI", "SBI"),
    ("SBI", "AXIS"),
    ("SBI", "IOB"),
    ("AXIS", "SBI"),
    ("AXIS", "AXIS"),
    ("AXIS", "IOB"),
    ("IOB", "SBI"),
    ("IOB", "AXIS"),
    ("IOB", "IOB"),
]

TX_TYPES: List[str] = ["UPI", "IMPS", "NEFT", "BANK_TRANSFER"]

DEVICE_TYPES: List[str] = ["Mobile", "Desktop", "Laptop", "Tablet"]

LOCATIONS: List[str] = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur",
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]

# Transaction Mix Modes
SIMULATION_MIX_MODES = ["balanced", "normal", "business", "mule"]
DEFAULT_SIMULATION_MIX = "balanced"

# Standard Transaction Statuses
TRANSACTION_STATUSES = [
    "PROCESSING",
    "COMPLETED",
    "MONITORING",
    "HONEYPOT",
    "LIEN_APPLIED",
    "RELEASED",
    "RESTRICTED",
    "FROZEN",
]

# Dedicated Honeypot Statuses
HONEYPOT_STATUSES = [
    "NOT_TRANSFERRED",
    "TRANSFERRED",
    "ACTIVE",
    "RELEASED",
]

# Dedicated Lien Statuses
LIEN_STATUSES = [
    "NO_LIEN",
    "LIEN_APPLIED",
    "LIEN_RELEASED",
]

SPEED_PRESETS = {
    "slow": {
        "delay": 2.5,
        "description": "Slow demonstration pace (2.5s delay)",
        "sim_step_seconds_range": (30, 300),
    },
    "normal": {
        "delay": 0.8,
        "description": "Normal realistic pace (0.8s delay)",
        "sim_step_seconds_range": (10, 120),
    },
    "fast": {
        "delay": 0.08,
        "description": "Fast stress-testing pace (0.08s delay)",
        "sim_step_seconds_range": (1, 30),
    },
}


@dataclass
class SimulatorConfig:
    mode: str = "normal"              # "slow", "normal", "fast"
    mix_mode: str = "balanced"        # "balanced", "normal", "business", "mule"
    custom_delay: float = None       # Overrides mode delay if provided
    total_count: int = 0             # 0 = run continuously until stopped
    burst_probability: float = 0.08  # Chance of triggering a burst sequence
    cross_bank_ratio: float = 0.65   # Target ratio for cross-bank transfers
    advance_simulation_clock: bool = True  # Advance logical simulation time after DB max timestamp
    step_seconds_range: Tuple[int, int] = (5, 90)

    @property
    def loop_delay(self) -> float:
        if self.custom_delay is not None:
            return max(0.0, float(self.custom_delay))
        preset = SPEED_PRESETS.get(self.mode.lower(), SPEED_PRESETS["normal"])
        return preset["delay"]
