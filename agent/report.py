"""Reporter: build report from results (and inventory), or load saved report by id and re-output.

Report shape conforms to docs/specs/report-spec.md.
"""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agent import storage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_factor_summary(results_list: list[dict]) -> list[dict]:
    """Build per-factor roll-up from a flat results list.

    Returns a list of dicts sorted by factor name, each with:
      factor, total_tests, l1_pass, l2_pass, l3_pass, l1_pct, l2_pct, l3_pct
    """
    by_factor: dict[str, list[dict]] = defaultdict(list)
    for r in results_list:
        by_factor[r.get("factor", "unknown")].append(r)

    out: list[dict] = []
    for factor in sorted(by_factor):
        tests = by_factor[factor]
        total = len(tests) or 1
        l1 = sum(1 for r in tests if r.get("l1_pass"))
        l2 = sum(1 for r in tests if r.get("l2_pass"))
        l3 = sum(1 for r in tests if r.get("l3_pass"))
        out.append({
            "factor": factor,
            "total_tests": len(tests),
            "l1_pass": l1,
            "l2_pass": l2,
            "l3_pass": l3,
            "l1_pct": round(100 * l1 / total, 1),
            "l2_pct": round(100 * l2 / total, 1),
            "l3_pct": round(100 * l3 / total, 1),
        })
    return out


# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------


def build_report(
    results: dict,
    *,
    inventory: Optional[dict] = None,
    connection_fingerprint: str = "",
    question_results: Optional[list] = None,
    target_workload: Optional[str] = None,
) -> dict:
    """Build full report dict from results. Conforms to report-spec.md."""
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
    out: dict[str, Any] = {
        "created_at": created,
        "connection_fingerprint": connection_fingerprint,
        "target_workload": target_workload,
        "summary": summary,
        "factor_summary": _build_factor_summary(results_list),
        "results": results_list,
        "not_assessed": [],
        "inventory": inventory,
        "environment": {},
        "user_context": {},
    }
    if question_results is not None:
        out["question_results"] = question_results
    return out


def build_estate_report(
    platforms: list[dict[str, Any]],
    *,
    target_workload: Optional[str] = None,
) -> dict:
    """Build a report from multiple per-connection results (estate mode).

    Each entry in platforms has: connection_fingerprint, summary, results, inventory (optional), error (optional).
    Returns report with platforms list and aggregate_summary (roll-up L1/L2/L3 across connections).
    """
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Aggregate: sum pass counts and total tests across successful platforms
    total_l1 = total_l2 = total_l3 = total_tests = 0
    all_results: list[dict] = []
    for p in platforms:
        if p.get("error"):
            continue
        s = p.get("summary", {})
        total_l1 += s.get("l1_pass", 0)
        total_l2 += s.get("l2_pass", 0)
        total_l3 += s.get("l3_pass", 0)
        total_tests += s.get("total_tests", 0)
        all_results.extend(p.get("results", []))
        # Ensure each platform sub-report has factor_summary
        if "factor_summary" not in p and not p.get("error"):
            p["factor_summary"] = _build_factor_summary(p.get("results", []))
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
        "target_workload": target_workload,
        "summary": aggregate_summary,
        "factor_summary": _build_factor_summary(all_results),
        "platforms": platforms,
        "aggregate_summary": aggregate_summary,
        "results": [],  # flat list not used in estate; per-platform results are in platforms[].results
        "not_assessed": [],
        "inventory": None,
        "environment": {},
        "user_context": {},
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

_WORKLOAD_LABELS = {"l1": "L1 (Analytics)", "l2": "L2 (RAG)", "l3": "L3 (Training)"}


def _fmt_measured(value: Any) -> str:
    """Format a measured value for display."""
    if value is None:
        return "—"
    try:
        v = float(value)
        # Show as percentage if 0-1, else as number
        if 0 <= v <= 1:
            return f"{v:.2%}"
        return f"{v:.4g}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_threshold(thresh: dict) -> str:
    """Format threshold as L1/L2/L3 string."""
    if not thresh:
        return "—"
    return f"{thresh.get('l1', '—')} / {thresh.get('l2', '—')} / {thresh.get('l3', '—')}"


def _pass_icon(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _render_factor_section(factor_name: str, factor_results: list[dict], factor_sum: dict) -> list[str]:
    """Render a single factor section with summary line and results table."""
    lines: list[str] = []
    display_name = factor_name.capitalize()
    lines.append(f"## Factor: {display_name}")
    lines.append("")

    # Factor-level summary
    t = factor_sum.get("total_tests", 0)
    lines.append(
        f"L1: {factor_sum.get('l1_pass', 0)}/{t} ({factor_sum.get('l1_pct', 0)}%) "
        f"| L2: {factor_sum.get('l2_pass', 0)}/{t} ({factor_sum.get('l2_pct', 0)}%) "
        f"| L3: {factor_sum.get('l3_pass', 0)}/{t} ({factor_sum.get('l3_pct', 0)}%)"
    )
    lines.append("")

    # Results table
    lines.append("| Test | Requirement | Measured | Threshold (L1/L2/L3) | Dir | L1 | L2 | L3 |")
    lines.append("|------|-------------|----------|----------------------|-----|----|----|-----|")
    for r in factor_results:
        test_id = r.get("test_id", "?")
        # Shorten long test IDs for readability
        if "|" in test_id:
            parts = test_id.split("|")
            test_id = parts[0] if len(parts) <= 1 else f"{parts[0]}|...{parts[-1]}"
        lines.append(
            f"| {test_id} "
            f"| {r.get('requirement', '?')} "
            f"| {_fmt_measured(r.get('measured_value'))} "
            f"| {_fmt_threshold(r.get('threshold', {}))} "
            f"| {r.get('direction', 'lte')} "
            f"| {_pass_icon(r.get('l1_pass', False))} "
            f"| {_pass_icon(r.get('l2_pass', False))} "
            f"| {_pass_icon(r.get('l3_pass', False))} |"
        )
        if r.get("error"):
            lines.append(f"| | | **Error:** {r['error']} | | | | | |")
    lines.append("")
    return lines


def report_to_markdown(report: dict) -> str:
    """Render report as markdown. Handles both single-connection and estate (multi-connection) reports.

    Rendering follows the canonical section order defined in report-spec.md.
    """
    if report.get("platforms") is not None:
        return _estate_report_to_markdown(report)

    s = report.get("summary", {})
    tw = report.get("target_workload")
    tw_label = _WORKLOAD_LABELS.get(tw, "Not specified") if tw else "Not specified"

    lines = [
        "# AI-Ready Data Assessment Report",
        "",
        f"**Created:** {report.get('created_at', '')}",
        f"**Connection:** {report.get('connection_fingerprint', '')}",
        f"**Target workload:** {tw_label}",
        "",
        "## Summary",
        "",
        f"- Total tests: {s.get('total_tests', 0)}",
        f"- L1 pass: {s.get('l1_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l1_pct', 0)}%)",
        f"- L2 pass: {s.get('l2_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l2_pct', 0)}%)",
        f"- L3 pass: {s.get('l3_pass', 0)}/{s.get('total_tests', 0)} ({s.get('l3_pct', 0)}%)",
        "",
    ]

    # Factor-by-factor breakdown
    factor_summaries = {fs["factor"]: fs for fs in report.get("factor_summary", [])}
    results_by_factor: dict[str, list[dict]] = defaultdict(list)
    for r in report.get("results", []):
        results_by_factor[r.get("factor", "unknown")].append(r)

    for factor in sorted(results_by_factor):
        fs = factor_summaries.get(factor, {})
        lines.extend(_render_factor_section(factor, results_by_factor[factor], fs))

    # Survey results
    qr = report.get("question_results")
    if qr:
        lines.append("## Survey Results")
        lines.append("")
        for r in qr:
            status = _pass_icon(r.get("l1_pass", False))
            lines.append(f"- **{r.get('factor')} / {r.get('requirement')}**: {status}")
            lines.append(f"  - {r.get('question_text', '')}")
            lines.append(f"  - Answer: {r.get('answer', '—')}")
            lines.append("")

    # Not assessed
    not_assessed = report.get("not_assessed", [])
    if not_assessed:
        lines.append("## Not Assessed")
        lines.append("")
        for na in not_assessed:
            lines.append(f"- **{na.get('factor', '?')} / {na.get('requirement', '?')}**: {na.get('reason', 'Unknown')}")
        lines.append("")

    # Appendix: inventory summary
    inv = report.get("inventory")
    if inv:
        lines.append("## Appendix: Inventory")
        lines.append("")
        lines.append(f"- Schemas: {len(inv.get('schemas', []))}")
        lines.append(f"- Tables: {len(inv.get('tables', []))}")
        lines.append(f"- Columns: {len(inv.get('columns', []))}")
        lines.append("")

    return "\n".join(lines)


def _estate_report_to_markdown(report: dict) -> str:
    """Render estate (multi-connection) report as markdown."""
    agg = report.get("aggregate_summary") or report.get("summary", {})
    tw = report.get("target_workload")
    tw_label = _WORKLOAD_LABELS.get(tw, "Not specified") if tw else "Not specified"

    lines = [
        "# AI-Ready Data Assessment Report (Estate)",
        "",
        f"**Created:** {report.get('created_at', '')}",
        f"**Platforms:** {agg.get('platforms_count', 0)}",
        f"**Target workload:** {tw_label}",
        "",
        "## Aggregate Summary",
        "",
        f"- Total tests: {agg.get('total_tests', 0)}",
        f"- L1 pass: {agg.get('l1_pass', 0)}/{agg.get('total_tests', 0)} ({agg.get('l1_pct', 0)}%)",
        f"- L2 pass: {agg.get('l2_pass', 0)}/{agg.get('total_tests', 0)} ({agg.get('l2_pct', 0)}%)",
        f"- L3 pass: {agg.get('l3_pass', 0)}/{agg.get('total_tests', 0)} ({agg.get('l3_pct', 0)}%)",
        "",
    ]

    for i, p in enumerate(report.get("platforms", []), 1):
        fp = p.get("connection_fingerprint", "?") or "?"
        lines.append(f"## {i}. {fp}")
        lines.append("")
        if p.get("error"):
            lines.append(f"**Error:** {p['error']}")
            lines.append("")
            continue

        # Per-platform factor breakdown
        factor_summaries = {fs["factor"]: fs for fs in p.get("factor_summary", [])}
        results_by_factor: dict[str, list[dict]] = defaultdict(list)
        for r in p.get("results", []):
            results_by_factor[r.get("factor", "unknown")].append(r)

        for factor in sorted(results_by_factor):
            fs = factor_summaries.get(factor, {})
            # Use h3 for factor sections within a platform
            section = _render_factor_section(factor, results_by_factor[factor], fs)
            # Downgrade ## to ### for nesting under platform
            for line in section:
                if line.startswith("## "):
                    lines.append("###" + line[2:])
                else:
                    lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Load from storage
# ---------------------------------------------------------------------------


def load_report_from_storage(db_path: Path, assessment_id: str) -> Optional[dict]:
    """Load report JSON by assessment id."""
    conn = storage.get_connection(db_path)
    try:
        return storage.get_report(conn, assessment_id)
    finally:
        conn.close()
