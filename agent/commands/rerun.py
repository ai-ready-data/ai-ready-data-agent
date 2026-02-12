"""``aird rerun`` — re-run failed tests from the most recent (or specified) assessment.

Usage::

    aird rerun -c "duckdb:///data.duckdb"
    aird rerun -c "duckdb:///data.duckdb" --id <assessment-uuid>
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List, Optional

from agent.config import Config
from agent import storage
from agent.platform import get_platform
from agent.platform.executor import execute_readonly
from agent.thresholds import get_direction, get_threshold, passes, load_thresholds

logger = logging.getLogger(__name__)


def _extract_failed_tests(report: dict) -> List[dict]:
    """Extract tests that failed at any level (l1, l2, or l3)."""
    failed = []
    for r in report.get("results", []):
        if not r.get("l1_pass") or not r.get("l2_pass") or not r.get("l3_pass"):
            failed.append(r)
    return failed


def _render_delta_rich(deltas: List[Dict[str, Any]]) -> None:
    """Render re-run delta using Rich table."""
    from rich.table import Table
    from agent.ui.console import get_console

    console = get_console()
    table = Table(title="Re-run Results", show_header=True, header_style="subheader")
    table.add_column("Test ID")
    table.add_column("Factor")
    table.add_column("L1")
    table.add_column("L2")
    table.add_column("L3")
    table.add_column("Status")

    for d in deltas:
        status_parts = []
        for level in ("l1", "l2", "l3"):
            was = d.get(f"was_{level}", False)
            now = d.get(f"now_{level}", False)
            if not was and now:
                status_parts.append(f"{level.upper()}: [pass]FIXED[/pass]")
            elif not was and not now:
                status_parts.append(f"{level.upper()}: [fail]STILL FAIL[/fail]")
        status = ", ".join(status_parts) if status_parts else "[pass]OK[/pass]"

        # Truncate long test IDs for display
        test_id = d.get("test_id", "?")
        if len(test_id) > 40:
            test_id = test_id[:37] + "..."

        l1_cell = "[pass]PASS[/pass]" if d.get("now_l1") else "[fail]FAIL[/fail]"
        l2_cell = "[pass]PASS[/pass]" if d.get("now_l2") else "[fail]FAIL[/fail]"
        l3_cell = "[pass]PASS[/pass]" if d.get("now_l3") else "[fail]FAIL[/fail]"

        table.add_row(test_id, d.get("factor", "?"), l1_cell, l2_cell, l3_cell, status)

    console.print(table)

    # Summary
    fixed = sum(1 for d in deltas if d.get("now_l1") and not d.get("was_l1"))
    still_fail = sum(1 for d in deltas if not d.get("now_l1"))
    console.print(f"\n[pass]Fixed:[/pass] {fixed}  [fail]Still failing:[/fail] {still_fail}  Total re-run: {len(deltas)}")


def _render_delta_plain(deltas: List[Dict[str, Any]]) -> None:
    """Render re-run delta as plain text."""
    for d in deltas:
        test_id = d.get("test_id", "?")
        parts = []
        for level in ("l1", "l2", "l3"):
            was = d.get(f"was_{level}", False)
            now = d.get(f"now_{level}", False)
            if not was and now:
                parts.append(f"{level.upper()}:FIXED")
            elif not was and not now:
                parts.append(f"{level.upper()}:STILL_FAIL")
        status = " ".join(parts) if parts else "OK"
        sys.stdout.write(f"{test_id}\t{d.get('factor', '?')}\t{status}\n")


def run_rerun(config: Config) -> None:
    """Load most recent assessment, re-run failed tests, show delta."""
    if not config.connection:
        raise ValueError("--connection (-c) required for rerun")

    # Load assessment
    conn = storage.get_connection(config.db_path)
    try:
        if config.rerun_id:
            report = storage.get_report(conn, config.rerun_id)
            if not report:
                raise ValueError(f"Assessment not found: {config.rerun_id}")
        else:
            assessments = storage.list_assessments(conn, limit=1)
            if not assessments:
                raise ValueError("No saved assessments found. Run 'aird assess' first.")
            report = storage.get_report(conn, assessments[0]["id"])
            if not report:
                raise ValueError("Could not load most recent assessment.")
    finally:
        conn.close()

    failed = _extract_failed_tests(report)
    if not failed:
        if sys.stderr.isatty():
            from agent.ui.console import print_success
            print_success("No failed tests to re-run!")
        else:
            sys.stdout.write("No failed tests to re-run.\n")
        return

    logger.info("Re-running %d failed tests", len(failed))

    # Re-run each failed test
    _, db_conn, _ = get_platform(config.connection)
    thresholds = load_thresholds(config.thresholds_path)
    deltas = []
    for orig in failed:
        test_id = orig.get("test_id", "")
        # We need the query — look in the original report's results for it
        query = orig.get("query")
        req = orig.get("requirement", "")
        delta = {
            "test_id": test_id,
            "factor": orig.get("factor", ""),
            "was_l1": orig.get("l1_pass", False),
            "was_l2": orig.get("l2_pass", False),
            "was_l3": orig.get("l3_pass", False),
        }
        if not query:
            # No query stored — cannot re-run; mark as still failing
            delta.update({"now_l1": False, "now_l2": False, "now_l3": False, "error": "no query stored"})
            deltas.append(delta)
            continue
        try:
            rows = execute_readonly(db_conn, query)
            measured = rows[0][0] if rows else None
            try:
                mv = float(measured) if measured is not None else None
            except (TypeError, ValueError):
                mv = None
            delta["now_l1"] = passes(req, mv, "l1", thresholds)
            delta["now_l2"] = passes(req, mv, "l2", thresholds)
            delta["now_l3"] = passes(req, mv, "l3", thresholds)
        except Exception as e:
            logger.warning("Re-run failed for %s: %s", test_id, e)
            delta.update({"now_l1": False, "now_l2": False, "now_l3": False, "error": str(e)})
        deltas.append(delta)

    # Render
    if sys.stderr.isatty():
        _render_delta_rich(deltas)
    else:
        _render_delta_plain(deltas)

