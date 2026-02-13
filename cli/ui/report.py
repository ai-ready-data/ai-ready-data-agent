"""Rich terminal renderer for assessment reports.

Renders coloured, structured output to the Rich console (stderr) when the
terminal is interactive.  Plain-text / markdown output is handled by
``agent.report.report_to_markdown`` and is unaffected.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from agent.ui.console import get_console

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Map workload names to level keys
_WORKLOAD_TO_LEVEL = {
    "analytics": "l1",
    "rag": "l2",
    "training": "l3",
}

_LEVEL_LABELS = {
    "l1": "L1 (Analytics)",
    "l2": "L2 (RAG)",
    "l3": "L3 (Training)",
}

# Map factor names to theme style tokens
_FACTOR_STYLES = {
    "clean": "factor.clean",
    "contextual": "factor.contextual",
    "consumable": "factor.consumable",
    "current": "factor.current",
    "correlated": "factor.correlated",
    "compliant": "factor.compliant",
}


def _pass_markup(passed: bool) -> str:
    """Return Rich-markup PASS/FAIL badge."""
    if passed:
        return "[pass]PASS[/pass]"
    return "[fail]FAIL[/fail]"


def _fmt_measured(value: Any) -> str:
    """Format a measured value for display."""
    if value is None:
        return "—"
    try:
        v = float(value)
        if 0 <= v <= 1:
            return f"{v:.2%}"
        return f"{v:.4g}"
    except (TypeError, ValueError):
        return str(value)


def _pct_style(pct: float) -> str:
    """Return a style name based on percentage."""
    if pct >= 90:
        return "pass"
    if pct >= 70:
        return "warn"
    return "fail"


def _render_pct_bar(label: str, pct: float, passed: int, total: int, *, highlight: bool = False) -> str:
    """Build a single readiness line with a text-based bar."""
    bar_width = 20
    filled = int(round(pct / 100 * bar_width))
    empty = bar_width - filled
    style = _pct_style(pct)
    marker = " ◀ target" if highlight else ""
    bar = f"[{style}]{'█' * filled}[/{style}][muted]{'░' * empty}[/muted]"
    return f"  {label:<16} {bar}  [{style}]{pct:5.1f}%[/{style}]  ({passed}/{total}){marker}"


# ---------------------------------------------------------------------------
# Summary panel
# ---------------------------------------------------------------------------


def _render_summary_panel(summary: dict, target_workload: Optional[str]) -> Panel:
    """Build the summary dashboard panel."""
    total = summary.get("total_tests", 0)
    target_level = _WORKLOAD_TO_LEVEL.get(target_workload) if target_workload else None

    lines = [f"[header]AI-Ready Data Assessment[/header]", ""]

    for level_key in ("l1", "l2", "l3"):
        label = _LEVEL_LABELS[level_key]
        passed = summary.get(f"{level_key}_pass", 0)
        pct = summary.get(f"{level_key}_pct", 0.0)
        highlight = (level_key == target_level)
        lines.append(_render_pct_bar(label, pct, passed, total, highlight=highlight))

    lines.append("")
    lines.append(f"  [muted]Total tests: {total}[/muted]")

    if target_workload:
        tw_label = _LEVEL_LABELS.get(target_level, target_workload)
        lines.append(f"  [info]Target workload: {tw_label}[/info]")

    content = "\n".join(lines)
    return Panel(content, title="[header]Assessment Summary[/header]", border_style="border", padding=(1, 2))




# ---------------------------------------------------------------------------
# Factor section
# ---------------------------------------------------------------------------


def _render_factor_table(
    factor_name: str,
    factor_results: List[dict],
    factor_sum: dict,
    target_level: Optional[str] = None,
) -> Table:
    """Build a Rich Table for one factor's test results."""
    style = _FACTOR_STYLES.get(factor_name, "info")
    display_name = factor_name.capitalize()

    total = factor_sum.get("total_tests", 0)

    # Build subtitle with per-level stats
    if target_level:
        lp = factor_sum.get(f"{target_level}_pass", 0)
        lpct = factor_sum.get(f"{target_level}_pct", 0)
        level_label = _LEVEL_LABELS.get(target_level, target_level.upper())
        subtitle = f"{level_label}: {lp}/{total} ({lpct}%)"
    else:
        parts = []
        for lk in ("l1", "l2", "l3"):
            lp = factor_sum.get(f"{lk}_pass", 0)
            lpct = factor_sum.get(f"{lk}_pct", 0)
            parts.append(f"{lk.upper()}: {lp}/{total} ({lpct}%)")
        subtitle = "  |  ".join(parts)

    table = Table(
        title=f"[{style}]■[/{style}] [{style} bold]{display_name}[/{style} bold]  [muted]{subtitle}[/muted]",
        show_header=True,
        header_style="subheader",
        border_style="muted",
        pad_edge=True,
        expand=True,
    )

    table.add_column("Test", style="info", no_wrap=True, ratio=3)
    table.add_column("Requirement", ratio=3)
    table.add_column("Measured", justify="right", ratio=1)

    if target_level:
        table.add_column("Threshold", justify="right", ratio=1)
        table.add_column("Result", justify="center", ratio=1)
    else:
        table.add_column("Threshold (L1/L2/L3)", justify="right", ratio=2)
        table.add_column("L1", justify="center", ratio=1)
        table.add_column("L2", justify="center", ratio=1)
        table.add_column("L3", justify="center", ratio=1)

    for r in factor_results:
        test_id = r.get("test_id", "?")
        # Truncate long test IDs
        if len(test_id) > 40:
            test_id = test_id[:37] + "..."
        requirement = r.get("requirement", "?")
        measured = _fmt_measured(r.get("measured_value"))
        thresh = r.get("threshold", {})

        if target_level:
            level_thresh = str(thresh.get(target_level, "—"))
            result = _pass_markup(r.get(f"{target_level}_pass", False))
            table.add_row(test_id, requirement, measured, level_thresh, result)
        else:
            thresh_str = f"{thresh.get('l1', '—')} / {thresh.get('l2', '—')} / {thresh.get('l3', '—')}"
            l1 = _pass_markup(r.get("l1_pass", False))
            l2 = _pass_markup(r.get("l2_pass", False))
            l3 = _pass_markup(r.get("l3_pass", False))
            table.add_row(test_id, requirement, measured, thresh_str, l1, l2, l3)

        # Show error row if present
        if r.get("error"):
            err_text = f"[fail]Error: {r['error']}[/fail]"
            if target_level:
                table.add_row("", err_text, "", "", "")
            else:
                table.add_row("", err_text, "", "", "", "", "")

    return table


# ---------------------------------------------------------------------------
# Question results
# ---------------------------------------------------------------------------


def _render_question_results(question_results: List[dict]) -> Table:
    """Build a Rich Table for survey / question results."""
    table = Table(
        title="[header]Survey Results[/header]",
        show_header=True,
        header_style="subheader",
        border_style="muted",
        expand=True,
    )
    table.add_column("Factor", style="info", ratio=1)
    table.add_column("Requirement", ratio=2)
    table.add_column("Question", ratio=3)
    table.add_column("Answer", ratio=2)
    table.add_column("Result", justify="center", ratio=1)

    for r in question_results:
        factor = r.get("factor", "?")
        style = _FACTOR_STYLES.get(factor, "info")
        factor_display = f"[{style}]{factor.capitalize()}[/{style}]"
        requirement = r.get("requirement", "?")
        question = r.get("question_text", "")
        answer = str(r.get("answer", "—"))
        result = _pass_markup(r.get("l1_pass", False))
        table.add_row(factor_display, requirement, question, answer, result)

    return table


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------


def _render_footer(report: dict) -> str:
    """Build footer text with metadata and hints."""
    parts = []
    aid = report.get("assessment_id")
    if aid:
        parts.append(f"[muted]Assessment ID:[/muted] [info]{aid}[/info]")
    created = report.get("created_at", "")
    if created:
        parts.append(f"[muted]Created:[/muted] {created}")
    conn = report.get("connection_fingerprint", "")
    if conn:
        parts.append(f"[muted]Connection:[/muted] {conn}")
    parts.append("")
    parts.append("[muted]Tip: Run [info]aird history[/info] to see past assessments, "
                 "[info]aird diff[/info] to compare runs.[/muted]")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_rich_report(report: dict) -> None:
    """Render a full assessment report to the Rich console (stderr).

    This is the TTY-friendly alternative to ``report_to_markdown()``.
    Output goes to stderr via the shared console so stdout stays clean.
    """
    con = get_console()
    summary = report.get("summary", {})
    target_workload = report.get("target_workload")
    target_level = _WORKLOAD_TO_LEVEL.get(target_workload) if target_workload else None

    # --- Summary panel ---
    con.print()
    con.print(_render_summary_panel(summary, target_workload))

    # --- Factor sections ---
    factor_summaries = {fs["factor"]: fs for fs in report.get("factor_summary", [])}
    results_by_factor: Dict[str, List[dict]] = defaultdict(list)
    for r in report.get("results", []):
        results_by_factor[r.get("factor", "unknown")].append(r)

    for factor in sorted(results_by_factor):
        fs = factor_summaries.get(factor, {})
        con.print()
        con.print(_render_factor_table(factor, results_by_factor[factor], fs, target_level))

    # --- Question results ---
    qr = report.get("question_results")
    if qr:
        con.print()
        con.print(Rule(style="muted"))
        con.print(_render_question_results(qr))

    # --- Footer ---
    con.print()
    con.print(Rule(style="muted"))
    con.print(_render_footer(report))
    con.print()