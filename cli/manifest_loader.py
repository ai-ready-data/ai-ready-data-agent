"""Load connections manifest (YAML or JSON) into a list of assessment targets."""

import json
import os
from pathlib import Path
from typing import Any, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

MANIFEST_EXTENSIONS = (".yaml", ".yml", ".json")


def _expand_env(line: str) -> Optional[str]:
    """If line is env:VAR_NAME, return value from environment; else return None (not env)."""
    line = line.strip()
    if line.lower().startswith("env:"):
        var_name = line[4:].strip()
        val = os.environ.get(var_name, "").strip()
        return val if val else None
    return None


def _connection_from_entry(entry: Any, expand_env: bool = True) -> Optional[str]:
    """Extract connection string from an entry (string or dict with 'connection' or 'env')."""
    if isinstance(entry, str):
        if expand_env and entry.strip().lower().startswith("env:"):
            return _expand_env(entry)  # None if var unset
        return entry
    if isinstance(entry, dict):
        conn = entry.get("connection") or entry.get("env")
        if conn is None:
            return None
        if isinstance(conn, str):
            if expand_env and conn.strip().lower().startswith("env:"):
                return _expand_env(conn)
            return conn
    return None


def _targets_scope_from_entry(entry: Any) -> dict:
    """Extract optional scope (databases, schemas, tables) from an entry. Handles flat or nested targets."""
    if not isinstance(entry, dict):
        return {}
    raw = entry.get("targets")
    if raw is None:
        return {}
    # Flat: targets = { databases: [...], schemas: [...], tables: [...] }
    if isinstance(raw, dict):
        scope = {}
        if "databases" in raw and isinstance(raw["databases"], list):
            scope["databases"] = list(raw["databases"])
        if "schemas" in raw and isinstance(raw["schemas"], list):
            scope["schemas"] = list(raw["schemas"])
        if "tables" in raw and isinstance(raw["tables"], list):
            scope["tables"] = list(raw["tables"])
        return scope
    # Nested: targets = [ { database: X, schemas: [...] }, ... ] -> one target per slice
    if isinstance(raw, list):
        # Handled by caller: emit one assessment target per list item with same connection
        return {"_nested": raw}
    return {}


def _flatten_nested_targets(connection: str, nested: List[dict]) -> List[dict]:
    """Convert nested targets list into flat list of targets (one per slice) with same connection."""
    out: List[dict] = []
    for slice_obj in nested:
        if not isinstance(slice_obj, dict):
            continue
        scope = {}
        if "databases" in slice_obj and isinstance(slice_obj["databases"], list):
            scope["databases"] = slice_obj["databases"]
        elif "database" in slice_obj:
            scope["databases"] = [slice_obj["database"]]
        if "schemas" in slice_obj and isinstance(slice_obj["schemas"], list):
            scope["schemas"] = slice_obj["schemas"]
        if "tables" in slice_obj and isinstance(slice_obj["tables"], list):
            scope["tables"] = slice_obj["tables"]
        out.append({"connection": connection, **scope})
    return out


def load_manifest(path: Path, *, expand_env: bool = True) -> List[dict]:
    """
    Load manifest from path (YAML or JSON). Returns list of assessment targets; each target is
    { "connection": str, "schemas"?: list, "tables"?: list, "databases"?: list }.

    Root: list or object with entries/targets/connections (list). Each entry: string (connection)
    or object with connection + optional targets (databases, schemas, tables).
    """
    p = path if isinstance(path, Path) else Path(path)
    if not p.exists():
        return []

    suffix = p.suffix.lower()
    if suffix not in MANIFEST_EXTENSIONS:
        raise ValueError(f"Manifest must be YAML or JSON (use .yaml, .yml, or .json); got {suffix or '(no extension)'}")

    text = p.read_text()
    if suffix == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise ImportError("PyYAML is required for YAML manifest; install with: pip install PyYAML")
        data = yaml.safe_load(text)

    return _parse_structured(data, expand_env)


def _parse_structured(data: Any, expand_env: bool) -> List[dict]:
    # Resolve root list
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("entries") or data.get("targets") or data.get("connections")
        if not isinstance(entries, list):
            return []
    else:
        return []

    targets: List[dict] = []
    for entry in entries:
        conn = _connection_from_entry(entry, expand_env)
        if not conn:
            continue
        scope = _targets_scope_from_entry(entry) if isinstance(entry, dict) else {}
        nested = scope.get("_nested")
        if nested is not None:
            targets.extend(_flatten_nested_targets(conn, nested))
        else:
            target = {"connection": conn}
            if scope.get("schemas"):
                target["schemas"] = scope["schemas"]
            if scope.get("tables"):
                target["tables"] = scope["tables"]
            if scope.get("databases"):
                target["databases"] = scope["databases"]
            targets.append(target)
    return targets
