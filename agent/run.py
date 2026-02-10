"""Test runner: generate tests from inventory, execute read-only, produce results. Optional dry_run and audit."""

from typing import Any, Optional

from agent.platform import get_platform
from agent.platform.executor import execute_readonly
from agent.platform.registry import get_suite
from agent.audit import AuditSink


def run_tests(
    connection_string: str,
    inventory: dict,
    suite_name: str = "common",
    *,
    dry_run: bool = False,
    audit: Optional[AuditSink] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    """Execute suite against inventory; return results artifact. If dry_run, return preview only."""
    _, conn, default_suite = get_platform(connection_string)
    suite = suite_name if suite_name != "auto" else default_suite
    tests = get_suite(suite)
    if not tests:
        return {"results": [], "dry_run": dry_run, "test_count": 0}

    if dry_run:
        return {
            "results": [],
            "dry_run": True,
            "test_count": len(tests),
            "preview": [{"id": t.get("id"), "factor": t.get("factor"), "requirement": t.get("requirement")} for t in tests[:10]],
        }

    results_list: list[dict] = []
    for t in tests:
        query = t.get("query") or "SELECT 1"
        try:
            rows = execute_readonly(conn, query)
            if audit:
                audit.log_query(
                    query,
                    target=t.get("target_type"),
                    factor=t.get("factor"),
                    requirement=t.get("requirement"),
                )
            measured = rows[0][0] if rows else None
            # Simple pass: we have a result (no threshold logic for v0)
            results_list.append({
                "test_id": t.get("id"),
                "factor": t.get("factor"),
                "requirement": t.get("requirement"),
                "target_type": t.get("target_type"),
                "measured_value": measured,
                "l1_pass": True,
                "l2_pass": True,
                "l3_pass": True,
            })
        except Exception as e:
            results_list.append({
                "test_id": t.get("id"),
                "factor": t.get("factor"),
                "requirement": t.get("requirement"),
                "target_type": t.get("target_type"),
                "measured_value": None,
                "l1_pass": False,
                "l2_pass": False,
                "l3_pass": False,
                "error": str(e),
            })

    return {"results": results_list, "dry_run": False, "test_count": len(results_list)}
