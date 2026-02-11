"""Built-in L1/L2/L3 thresholds per requirement key.

Two directions:
- "lte" (default): pass when measured_value <= threshold. Used for rate-of-bad metrics (null_rate, duplicate_rate).
- "gte": pass when measured_value >= threshold. Used for coverage metrics (primary_key_defined, semantic_model_coverage).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Per-requirement threshold direction. Default is "lte" (lower is better).
# Only requirements that use "gte" (higher is better) need an entry here.
THRESHOLD_DIRECTION: Dict[str, str] = {
    # Factor 1: Contextual — coverage metrics (higher is better)
    "primary_key_defined": "gte",
    "semantic_model_coverage": "gte",
    "foreign_key_coverage": "gte",
    "temporal_scope_present": "gte",
}

DEFAULT_THRESHOLDS = {
    # Factor 0: Clean — rate metrics (lower is better, direction: lte)
    "table_discovery": {"l1": 1.0, "l2": 1.0, "l3": 1.0},  # no threshold (informational)
    "null_rate": {"l1": 0.2, "l2": 0.05, "l3": 0.01},
    "duplicate_rate": {"l1": 0.1, "l2": 0.02, "l3": 0.01},
    "format_inconsistency_rate": {"l1": 0.1, "l2": 0.05, "l3": 0.01},
    "type_inconsistency_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
    "zero_negative_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
    # Factor 1: Contextual — coverage metrics (higher is better, direction: gte)
    "primary_key_defined": {"l1": 0.5, "l2": 0.8, "l3": 0.95},
    "semantic_model_coverage": {"l1": 0.2, "l2": 0.5, "l3": 0.8},
    "foreign_key_coverage": {"l1": 0.3, "l2": 0.6, "l3": 0.8},
    "temporal_scope_present": {"l1": 0.3, "l2": 0.6, "l3": 0.9},
    # Factor 2–5 (demo placeholders — will be replaced as factors are implemented)
    "serving_capability": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "freshness_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "lineage_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "access_control_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
}


def load_thresholds(path: Optional[Path]) -> Dict[str, Dict[str, float]]:
    """
    Load optional JSON file and merge with DEFAULT_THRESHOLDS (overrides by requirement key).
    JSON shape: { "<requirement_key>": { "l1": float, "l2": float, "l3": float, "direction"?: "lte"|"gte" }, ... }
    Returns merged dict; if path is None or missing, returns copy of DEFAULT_THRESHOLDS.
    When a user override includes "direction", it is stored in THRESHOLD_DIRECTION.
    """
    out = dict(DEFAULT_THRESHOLDS)
    if not path or not path.exists():
        return out
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        return out
    for key, val in raw.items():
        if not isinstance(key, str) or not isinstance(val, dict):
            continue
        out[key] = {
            "l1": float(val.get("l1", out.get(key, {}).get("l1", 0.0))),
            "l2": float(val.get("l2", out.get(key, {}).get("l2", 0.0))),
            "l3": float(val.get("l3", out.get(key, {}).get("l3", 0.0))),
        }
        if "direction" in val and val["direction"] in ("lte", "gte"):
            THRESHOLD_DIRECTION[key] = val["direction"]
    return out


def get_threshold(
    requirement: str,
    workload: str,
    thresholds: Optional[Dict[str, Dict[str, float]]] = None,
) -> float:
    """Return threshold for requirement and workload (l1, l2, l3). Default 0.0 if unknown."""
    t = (thresholds or DEFAULT_THRESHOLDS)
    req = t.get(requirement)
    if not req:
        return 0.0
    return float(req.get(workload.lower(), 0.0))


def get_direction(requirement: str) -> str:
    """Return threshold direction for a requirement: 'lte' (default) or 'gte'."""
    return THRESHOLD_DIRECTION.get(requirement, "lte")


def passes(
    requirement: str,
    measured_value: Optional[float],
    workload: str,
    thresholds: Optional[Dict[str, Dict[str, float]]] = None,
) -> bool:
    """True if measured value passes for the workload.

    Direction per requirement:
    - "lte" (default): pass when measured <= threshold (rate-of-bad metrics).
    - "gte": pass when measured >= threshold (coverage metrics).
    """
    if requirement == "table_discovery":
        return True  # informational
    if measured_value is None:
        return False
    threshold = get_threshold(requirement, workload, thresholds)
    if get_direction(requirement) == "gte":
        return float(measured_value) >= threshold
    return float(measured_value) <= threshold
