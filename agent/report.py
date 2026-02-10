"""Reporter: build report from results (and inventory), or load saved report by id and re-output."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent import storage


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
    """Render report as markdown."""
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


def load_report_from_storage(db_path: Path, assessment_id: str) -> Optional[dict]:
    """Load report JSON by assessment id."""
    conn = storage.get_connection(db_path)
    try:
        return storage.get_report(conn, assessment_id)
    finally:
        conn.close()
