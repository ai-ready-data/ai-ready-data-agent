"""Test runner: generate tests from inventory, execute read-only, produce results. Optional dry_run and audit."""

from typing import Any, List, Optional

from agent.platform import get_platform
from agent.platform.executor import execute_readonly
from agent.platform.registry import get_suite
from agent.audit import AuditSink
from agent.thresholds import passes


def _quote_ident(s: str) -> str:
    """Quote identifier for SQL (DuckDB: double quotes; escape " as "")."""
    return '"' + str(s).replace('"', '""') + '"'


def expand_tests(suite_tests: List[dict], inventory: dict) -> List[dict]:
    """Expand suite test defs (with optional query_template) into concrete tests using inventory."""
    out: List[dict] = []
    for t in suite_tests:
        if t.get("query"):
            out.append({
                "id": t.get("id"),
                "factor": t.get("factor"),
                "requirement": t.get("requirement"),
                "target_type": t.get("target_type"),
                "query": t["query"],
            })
            continue
        template = t.get("query_template")
        target_type = t.get("target_type")
        if not template or not target_type:
            continue
        base_id = t.get("id", "test")
        factor = t.get("factor", "clean")
        requirement = t.get("requirement", "")
        if target_type == "column":
            for col in inventory.get("columns", []):
                schema_q = _quote_ident(col["schema"])
                table_q = _quote_ident(col["table"])
                column_q = _quote_ident(col["column"])
                query = template.format(schema_q=schema_q, table_q=table_q, column_q=column_q)
                out.append({
                    "id": f"{base_id}|{col['schema']}|{col['table']}|{col['column']}",
                    "factor": factor,
                    "requirement": requirement,
                    "target_type": target_type,
                    "query": query,
                })
        elif target_type == "table":
            for tbl in inventory.get("tables", []):
                schema_q = _quote_ident(tbl["schema"])
                table_q = _quote_ident(tbl["table"])
                query = template.format(schema_q=schema_q, table_q=table_q)
                out.append({
                    "id": f"{base_id}|{tbl['schema']}|{tbl['table']}",
                    "factor": factor,
                    "requirement": requirement,
                    "target_type": target_type,
                    "query": query,
                })
    return out


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
    raw_tests = get_suite(suite)
    if not raw_tests:
        return {"results": [], "dry_run": dry_run, "test_count": 0}

    tests = expand_tests(raw_tests, inventory)
    if dry_run:
        return {
            "results": [],
            "dry_run": True,
            "test_count": len(tests),
            "preview": [{"id": t.get("id"), "factor": t.get("factor"), "requirement": t.get("requirement")} for t in tests[:15]],
        }

    results_list: List[dict] = []
    for t in tests:
        query = t.get("query") or "SELECT 1"
        req = t.get("requirement", "")
        try:
            rows = execute_readonly(conn, query)
            if audit:
                audit.log_query(
                    query,
                    target=t.get("target_type"),
                    factor=t.get("factor"),
                    requirement=req,
                )
            measured = rows[0][0] if rows else None
            try:
                mv = float(measured) if measured is not None else None
            except (TypeError, ValueError):
                mv = None
            results_list.append({
                "test_id": t.get("id"),
                "factor": t.get("factor"),
                "requirement": req,
                "target_type": t.get("target_type"),
                "measured_value": measured,
                "l1_pass": passes(req, mv, "l1"),
                "l2_pass": passes(req, mv, "l2"),
                "l3_pass": passes(req, mv, "l3"),
            })
        except Exception as e:
            results_list.append({
                "test_id": t.get("id"),
                "factor": t.get("factor"),
                "requirement": req,
                "target_type": t.get("target_type"),
                "measured_value": None,
                "l1_pass": False,
                "l2_pass": False,
                "l3_pass": False,
                "error": str(e),
            })

    return {"results": results_list, "dry_run": False, "test_count": len(results_list)}
