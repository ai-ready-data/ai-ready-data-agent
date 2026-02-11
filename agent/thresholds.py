"""Built-in L1/L2/L3 thresholds per requirement key. Lower is stricter for rates (0–1)."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Per factor-00-clean requirement keys. Pass when measured_value <= threshold.
# null_rate, duplicate_rate: fraction 0–1; pass if <= threshold.
# SM2: Factor 1–5 placeholder keys: pass when v <= 1.0 so "SELECT 1 AS v" passes.
DEFAULT_THRESHOLDS = {
    "table_discovery": {"l1": 1.0, "l2": 1.0, "l3": 1.0},  # no threshold (informational)
    "null_rate": {"l1": 0.2, "l2": 0.05, "l3": 0.01},
    "duplicate_rate": {"l1": 0.1, "l2": 0.02, "l3": 0.01},
    "format_inconsistency_rate": {"l1": 0.1, "l2": 0.05, "l3": 0.01},
    "type_inconsistency_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
    "zero_negative_rate": {"l1": 0.05, "l2": 0.02, "l3": 0.01},
    # Factor 1–5 (demo placeholders)
    "column_comment_coverage": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "serving_capability": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "freshness_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "lineage_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
    "access_control_metadata": {"l1": 1.0, "l2": 1.0, "l3": 1.0},
}


def load_thresholds(path: Optional[Path]) -> Dict[str, Dict[str, float]]:
    """
    Load optional JSON file and merge with DEFAULT_THRESHOLDS (overrides by requirement key).
    JSON shape: { "<requirement_key>": { "l1": float, "l2": float, "l3": float }, ... }
    Returns merged dict; if path is None or missing, returns copy of DEFAULT_THRESHOLDS.
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


def passes(
    requirement: str,
    measured_value: Optional[float],
    workload: str,
    thresholds: Optional[Dict[str, Dict[str, float]]] = None,
) -> bool:
    """True if measured value passes for the workload (rate metrics: measured <= threshold)."""
    if requirement == "table_discovery":
        return True  # informational
    if measured_value is None:
        return False
    return float(measured_value) <= get_threshold(requirement, workload, thresholds)
