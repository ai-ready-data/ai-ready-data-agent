"""YAML suite loader: reads declarative suite definitions and registers them.

Scans agent/suites/definitions/ for *.yaml files, validates each against the
expected schema, and calls register_suite() for each suite.

YAML schema per file:
    suite_name: str          # name to register (e.g. "common", "common_sqlite")
    platform: str            # informational (e.g. "duckdb", "snowflake")
    extends: list[str]       # optional: suite names whose tests are merged first
    tests:                   # list of test definitions (can be empty if extends is set)
      - id: str
        factor: str
        requirement: str     # must match a key in requirements_registry.yaml
        query: str           # fixed SQL (mutually exclusive with query_template)
        query_template: str  # SQL with {schema_q}, {table_q}, {column_q} placeholders
        target_type: str     # "platform", "table", or "column"
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from agent.platform.registry import get_suite, register_suite

logger = logging.getLogger(__name__)

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"

_REQUIRED_TEST_FIELDS = {"id", "factor", "requirement", "target_type"}
_VALID_TARGET_TYPES = {"platform", "table", "column"}

# Tracks which suites use extends (suite_name -> list of parent suite names).
# Populated during loading; consumed by cmd_suites for display.
_suite_extends: Dict[str, List[str]] = {}


def _validate_test(test: dict, file_path: Path, index: int) -> List[str]:
    """Validate a single test definition. Returns list of error messages (empty = valid)."""
    errors: List[str] = []
    for field in _REQUIRED_TEST_FIELDS:
        if field not in test:
            errors.append(f"  test[{index}]: missing required field '{field}'")
    if "query" not in test and "query_template" not in test:
        errors.append(f"  test[{index}]: must have 'query' or 'query_template'")
    if "query" in test and "query_template" in test:
        errors.append(f"  test[{index}]: cannot have both 'query' and 'query_template'")
    tt = test.get("target_type")
    if tt and tt not in _VALID_TARGET_TYPES:
        errors.append(f"  test[{index}]: invalid target_type '{tt}' (expected one of {_VALID_TARGET_TYPES})")
    return errors


def _resolve_extends(
    suite_name: str,
    extends: List[str],
    resolving: Optional[set] = None,
) -> list[dict]:
    """Resolve parent suites listed in ``extends`` and return their merged tests.

    Raises ValueError on circular dependencies or missing parent suites.
    """
    if resolving is None:
        resolving = set()

    if suite_name in resolving:
        cycle = " -> ".join(list(resolving) + [suite_name])
        raise ValueError(f"Circular suite dependency detected: {cycle}")

    resolving.add(suite_name)
    merged: list[dict] = []

    for parent_name in extends:
        if parent_name in resolving:
            cycle = " -> ".join(list(resolving) + [parent_name])
            raise ValueError(f"Circular suite dependency detected: {cycle}")

        parent_tests = get_suite(parent_name)
        if not parent_tests:
            raise ValueError(
                f"Suite '{suite_name}' extends '{parent_name}', but '{parent_name}' "
                f"is not registered. Ensure the parent suite file is loaded first "
                f"(files are loaded in sorted order)."
            )

        # If the parent itself was composed, its tests are already resolved
        # in the registry, so we just take them as-is.
        merged.extend(parent_tests)

    resolving.discard(suite_name)
    return merged


def load_suite_file(file_path: Path) -> None:
    """Load a single YAML suite file and register its tests.

    Supports an optional ``extends`` field: a list of suite names whose tests
    are merged before the current file's own tests.

    Raises ValueError for malformed files so callers get clear error messages.
    """
    text = file_path.read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Suite file {file_path.name}: expected YAML mapping at top level, got {type(data).__name__}")

    suite_name = data.get("suite_name")
    if not suite_name or not isinstance(suite_name, str):
        raise ValueError(f"Suite file {file_path.name}: missing or invalid 'suite_name'")

    extends = data.get("extends")
    tests_raw = data.get("tests")

    # Validate extends field
    if extends is not None:
        if not isinstance(extends, list) or not all(isinstance(s, str) for s in extends):
            raise ValueError(f"Suite file {file_path.name}: 'extends' must be a list of suite name strings")

    # tests can be empty/absent when extends is set; otherwise must be non-empty
    has_extends = extends and len(extends) > 0
    if tests_raw is None:
        tests_raw = []
    if not isinstance(tests_raw, list):
        raise ValueError(f"Suite file {file_path.name}: 'tests' must be a list")
    if not has_extends and len(tests_raw) == 0:
        raise ValueError(f"Suite file {file_path.name}: 'tests' must be a non-empty list (or use 'extends')")

    # Validate all tests before registering any
    all_errors: List[str] = []
    for i, test in enumerate(tests_raw):
        if not isinstance(test, dict):
            all_errors.append(f"  test[{i}]: expected mapping, got {type(test).__name__}")
            continue
        all_errors.extend(_validate_test(test, file_path, i))

    if all_errors:
        raise ValueError(
            f"Suite file {file_path.name}: validation errors:\n" + "\n".join(all_errors)
        )

    # Resolve parent suites if extends is specified
    merged_tests: list[dict] = []
    if has_extends:
        merged_tests = _resolve_extends(suite_name, extends)
        _suite_extends[suite_name] = list(extends)

    # Build test dicts from this file's own tests (same shape as Python suites produce)
    for test in tests_raw:
        entry = {
            "id": test["id"],
            "factor": test["factor"],
            "requirement": test["requirement"],
            "target_type": test["target_type"],
        }
        if "query" in test:
            entry["query"] = test["query"]
        if "query_template" in test:
            entry["query_template"] = test["query_template"]
        merged_tests.append(entry)

    register_suite(suite_name, merged_tests)
    logger.debug("Loaded suite '%s' (%d tests) from %s", suite_name, len(merged_tests), file_path.name)


def get_suite_extends() -> Dict[str, List[str]]:
    """Return a copy of the suite-extends mapping (suite_name -> list of parent suite names)."""
    return {name: list(parents) for name, parents in _suite_extends.items()}


def load_all_definitions() -> int:
    """Scan definitions/ directory for *.yaml files and load each.

    Returns the number of files successfully loaded.
    Files are loaded in sorted order for deterministic registration
    (important when multiple files contribute to the same suite name).
    """
    if not _DEFINITIONS_DIR.is_dir():
        logger.debug("No definitions directory at %s", _DEFINITIONS_DIR)
        return 0

    yaml_files = sorted(_DEFINITIONS_DIR.glob("*.yaml"))
    if not yaml_files:
        logger.debug("No YAML suite files found in %s", _DEFINITIONS_DIR)
        return 0

    loaded = 0
    for f in yaml_files:
        try:
            load_suite_file(f)
            loaded += 1
        except Exception as exc:
            logger.warning("Failed to load suite file %s: %s", f.name, exc)

    logger.debug("Loaded %d suite definition file(s) from %s", loaded, _DEFINITIONS_DIR)
    return loaded

