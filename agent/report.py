"""Reporter: build report from results (and inventory), or load saved report by id and re-output."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agent import storage


def build_estate_report(platforms: list[dict[str, Any]]) -> dict:
    """Build a report from multiple per-connection results (estate mode).

    Each entry in platforms has: connection_fingerprint, summary, results, inventory (optional), error (optional).
    Returns report with platforms list and aggregate_summary (roll-up L1/L2/L3 across connections).
    """
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Aggregate: sum pass counts and total tests across successful platforms
    total_l1 = total_l2 = total_l3 = total_tests = 0
    for p in platforms:
        if p.get("error"):
            continue
        s = p.get("summary", {})
        total_l1 += s.get("l1_pass", 0)
        total_l2 += s.get("l2_pass", 0)
        total_l3 += s.get("l3_pass", 0)
        total_tests += s.get("total_tests", 0)
    if total_tests == 0:
        total_tests = 1
    aggregate_summary = {
        "total_tests": total_tests,
        "l1_pass": total_l1,
        "l2_pass": total_l2,
        "l3_pass": total_l3,
        "l1_pct": round(100 * total_l1 / total_tests, 1),
        "l2_pct": round(100 * total_l2 / total_tests, 1),
        "l3_pct": round(100 * total_l3 / total_tests, 1),
        "platforms_count": len(platforms),
    }
    return {
        "created_at": created,
        "connection_fingerprint": "",  # estate has no single fingerprint
        "summary": aggregate_summary,
        "platforms": platforms,
        "aggregate_summary": aggregate_summary,
        "results": [],  # flat list not used in estate; per-platform results are in platforms[].results
        "inventory": None,
        "environment": {},
        "user_context": {},
    }


def build_report(
    results: dict,
    *,
    inventory: Optional[dict] = None,
    connection_fingerprint: str = "",
) -> dict:
    """Build full report dict from results. Optionally attach inventory and connection fingerprint."""
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    results_list = results.get("results", [])
    l1_pass = sum(1 for r in results_list if r.get("l1_pass"))
    l2_pass = sum(1 for r in results_list if r.get("l2_pass"))
    l3_pass = sum(1 for r in results_list if r.get("l3_pass"))
    total = len(results_list) or 1
    summary = {
        "total_tests": len(results_list),
        "l1_pass": l1_pass,
        "l2_pass": l2_pass,
        "l3_pass": l3_pass,
        "l1_pct": round(100 * l1_pass / total, 1),
        "l2_pct": round(100 * l2_pass / total, 1),
        "l3_pct": round(100 * l3_pass / total, 1),
    }
    return {
        "created_at": created,
        "connection_fingerprint": connection_fingerprint,
        "summary": summary,
        "results": results_list,
        "inventory": inventory,
        "environment": {},
        "user_context": {},
    }


def report_to_markdown(report: dict) -> str:
    """Render report as markdown. Handles both single-connection and estate (multi-connection) reports."""
    if report.get("platforms") is not None:
        return _estate_report_to_markdown(report)
    s = report.get("summary", {})
    lines = [
        "# AI-Ready Data Assessment Report",
        "",
        f"**Created:** {report.get('created_at', '')}",
        "",
        "## Summary",
        f"- Total tests: {s.get('total_tests', 0)}",
        f"- L1 pass: {s.get('l1_pass', 0)} ({s.get('l1_pct', 0)}%)",
        f"- L2 pass: {s.get('l2_pass', 0)} ({s.get('l2_pct', 0)}%)",
        f"- L3 pass: {s.get('l3_pass', 0)} ({s.get('l3_pct', 0)}%)",
        "",
        "## Results",
        "",
    ]
    for r in report.get("results", []):
        status = "PASS" if r.get("l1_pass") else "FAIL"
        lines.append(f"- **{r.get('test_id', '?')}** ({r.get('factor')}/{r.get('requirement')}): {status}")
    return "\n".join(lines)


def _estate_report_to_markdown(report: dict) -> str:
    """Render estate (multi-connection) report as markdown."""
    agg = report.get("aggregate_summary") or report.get("summary", {})
    lines = [
        "# AI-Ready Data Assessment Report (Estate)",
        "",
        f"**Created:** {report.get('created_at', '')}",
        f"**Platforms:** {agg.get('platforms_count', 0)}",
        "",
        "## Aggregate Summary",
        f"- Total tests: {agg.get('total_tests', 0)}",
        f"- L1 pass: {agg.get('l1_pass', 0)} ({agg.get('l1_pct', 0)}%)",
        f"- L2 pass: {agg.get('l2_pass', 0)} ({agg.get('l2_pct', 0)}%)",
        f"- L3 pass: {agg.get('l3_pass', 0)} ({agg.get('l3_pct', 0)}%)",
        "",
        "## Per-connection results",
        "",
    ]
    for i, p in enumerate(report.get("platforms", []), 1):
        fp = p.get("connection_fingerprint", "?") or "?"
        lines.append(f"### {i}. {fp}")
        if p.get("error"):
            lines.append(f"- **Error:** {p['error']}")
            lines.append("")
            continue
        s = p.get("summary", {})
        lines.append(f"- L1: {s.get('l1_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l1_pct', 0)}%)")
        lines.append(f"- L2: {s.get('l2_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l2_pct', 0)}%)")
        lines.append(f"- L3: {s.get('l3_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l3_pct', 0)}%)")
        lines.append("")
        for r in p.get("results", []):
            status = "PASS" if r.get("l1_pass") else "FAIL"
            lines.append(f"  - **{r.get('test_id', '?')}** ({r.get('factor')}/{r.get('requirement')}): {status}")
        lines.append("")
    return "\n".join(lines)


def load_report_from_storage(db_path: Path, assessment_id: str) -> Optional[dict]:
    """Load report JSON by assessment id."""
    conn = storage.get_connection(db_path)
    try:
        return storage.get_report(conn, assessment_id)
    finally:
        conn.close()
