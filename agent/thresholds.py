"""Built-in L1/L2/L3 thresholds per requirement key.

Two directions:
- "lte" (default): pass when measured_value <= threshold. Used for rate-of-bad metrics (null_rate, duplicate_rate).
- "gte": pass when measured_value >= threshold. Used for coverage metrics (primary_key_defined, semantic_model_coverage).

Defaults are loaded from agent/requirements_registry.yaml at module init time.
User overrides via load_thresholds(path) merge on top.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# ---------------------------------------------------------------------------
# Load defaults from the canonical requirements registry YAML
# ---------------------------------------------------------------------------
_REGISTRY_PATH = Path(__file__).parent / "requirements_registry.yaml"


def _load_registry() -> tuple:
    """Parse requirements_registry.yaml and return (default_thresholds, threshold_direction)."""
    thresholds: Dict[str, Dict[str, float]] = {}
    directions: Dict[str, str] = {}
    if not _REGISTRY_PATH.exists():
        return thresholds, directions
    raw = yaml.safe_load(_REGISTRY_PATH.read_text())
    if not isinstance(raw, dict):
        return thresholds, directions
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        dt = entry.get("default_thresholds", {})
        thresholds[key] = {
            "l1": float(dt.get("l1", 0.0)),
            "l2": float(dt.get("l2", 0.0)),
            "l3": float(dt.get("l3", 0.0)),
        }
        direction = entry.get("direction", "lte")
        if direction != "lte":
            directions[key] = direction
    return thresholds, directions


# Per-requirement threshold direction. Default is "lte" (lower is better).
# Only requirements that use "gte" (higher is better) need an entry here.
# Populated from requirements_registry.yaml at module load time.
THRESHOLD_DIRECTION: Dict[str, str] = {}

# Default L1/L2/L3 thresholds per requirement key.
# Populated from requirements_registry.yaml at module load time.
DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {}

# Initialize from registry
DEFAULT_THRESHOLDS, THRESHOLD_DIRECTION = _load_registry()


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
