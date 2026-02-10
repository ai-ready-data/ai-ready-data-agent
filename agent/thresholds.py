"""Built-in L1/L2/L3 thresholds per requirement key. Lower is stricter for rates (0–1)."""

from typing import Optional

# Per factor-00-clean requirement keys. Pass when measured_value <= threshold.
# null_rate, duplicate_rate: fraction 0–1; pass if <= threshold.
DEFAULT_THRESHOLDS = {
    "table_discovery": {"l1": 1.0, "l2": 1.0, "l3": 1.0},  # no threshold (informational)
    "null_rate": {"l1": 0.2, "l2": 0.05, "l3": 0.01},
    "duplicate_rate": {"l1": 0.1, "l2": 0.02, "l3": 0.01},
    "format_inconsistency_rate": {"l1": 0.1, "l2": 0.05, "l3": 0.01},
    "type_inconsistency_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
    "zero_negative_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
}


def get_threshold(requirement: str, workload: str) -> float:
    """Return threshold for requirement and workload (l1, l2, l3). Default 0.0 if unknown."""
    req = DEFAULT_THRESHOLDS.get(requirement)
    if not req:
        return 0.0
    return float(req.get(workload.lower(), 0.0))


def passes(requirement: str, measured_value: Optional[float], workload: str) -> bool:
    """True if measured value passes for the workload (rate metrics: measured <= threshold)."""
    if requirement == "table_discovery":
        return True  # informational
    if measured_value is None:
        return False
    return float(measured_value) <= get_threshold(requirement, workload)
