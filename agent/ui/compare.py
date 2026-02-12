"""Rich side-by-side comparison table for ``aird compare``."""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from agent.ui.console import get_console, is_interactive


# Six assessment factors in canonical order
_FACTORS = ["clean", "contextual", "consumable", "current", "correlated", "compliant"]


def _pct(passed: int, total: int) -> float:
    """Return percentage; 0.0 when total is zero."""
    if total == 0:
        return 0.0
    return round(100.0 * passed / total, 1)


def _colour_cell(value: float, other: float) -> str:
    """Return Rich-styled string: green if better, red if worse, yellow if same."""
    text = f"{value}%"
    if value > other:
        return f"[pass]{text}[/pass]"
    elif value < other:
        return f"[fail]{text}[/fail]"
    return f"[warn]{text}[/warn]"


def _extract_factor_stats(report: dict) -> Dict[str, Dict[str, Any]]:
    """Extract per-factor pass counts from a report's results list."""
    stats: Dict[str, Dict[str, Any]] = {}
    for r in report.get("results", []):
        factor = r.get("factor", "unknown")
        if factor not in stats:
            stats[factor] = {"total": 0, "l1": 0, "l2": 0, "l3": 0}
        stats[factor]["total"] += 1
        if r.get("l1_pass"):
            stats[factor]["l1"] += 1
        if r.get("l2_pass"):
            stats[factor]["l2"] += 1
        if r.get("l3_pass"):
            stats[factor]["l3"] += 1
    return stats


def render_comparison(table_results: Dict[str, dict], table_names: Optional[List[str]] = None) -> None:
    """Render side-by-side comparison of two table assessment reports.

    Parameters
    ----------
    table_results:
        Mapping of table name → report dict.
    table_names:
        Ordered list of table names (defaults to sorted keys).
    """
    names = table_names or sorted(table_results.keys())
    if len(names) < 2:
        return

    t1, t2 = names[0], names[1]
    stats1 = _extract_factor_stats(table_results[t1])
    stats2 = _extract_factor_stats(table_results[t2])

    # Collect all factors present in either report
    all_factors = []
    for f in _FACTORS:
        if f in stats1 or f in stats2:
            all_factors.append(f)
    # Add any extra factors not in canonical list
    for f in sorted(set(list(stats1.keys()) + list(stats2.keys()))):
        if f not in all_factors:
            all_factors.append(f)

    if is_interactive():
        _render_rich(t1, t2, stats1, stats2, all_factors)
    else:
        _render_plain(t1, t2, stats1, stats2, all_factors)


def _render_rich(
    t1: str, t2: str,
    stats1: Dict[str, Dict[str, Any]],
    stats2: Dict[str, Dict[str, Any]],
    factors: List[str],
) -> None:
    """Render Rich table to stderr console."""
    from rich.table import Table

    console = get_console()
    table = Table(title=f"Compare: {t1} vs {t2}", show_header=True, header_style="subheader")
    table.add_column("Factor")
    table.add_column(f"{t1} L1%", justify="right")
    table.add_column(f"{t2} L1%", justify="right")
    table.add_column(f"{t1} L2%", justify="right")
    table.add_column(f"{t2} L2%", justify="right")

    for f in factors:
        s1 = stats1.get(f, {"total": 0, "l1": 0, "l2": 0, "l3": 0})
        s2 = stats2.get(f, {"total": 0, "l1": 0, "l2": 0, "l3": 0})
        l1_1 = _pct(s1["l1"], s1["total"])
        l1_2 = _pct(s2["l1"], s2["total"])
        l2_1 = _pct(s1["l2"], s1["total"])
        l2_2 = _pct(s2["l2"], s2["total"])
        table.add_row(
            f,
            _colour_cell(l1_1, l1_2),
            _colour_cell(l1_2, l1_1),
            _colour_cell(l2_1, l2_2),
            _colour_cell(l2_2, l2_1),
        )

    console.print(table)


def _render_plain(
    t1: str, t2: str,
    stats1: Dict[str, Dict[str, Any]],
    stats2: Dict[str, Dict[str, Any]],
    factors: List[str],
) -> None:
    """Render plain-text comparison to stdout."""
    header = f"{'Factor':<15} {t1+' L1%':>10} {t2+' L1%':>10} {t1+' L2%':>10} {t2+' L2%':>10}"
    sys.stdout.write(header + "\n")
    sys.stdout.write("-" * len(header) + "\n")
    for f in factors:
        s1 = stats1.get(f, {"total": 0, "l1": 0, "l2": 0, "l3": 0})
        s2 = stats2.get(f, {"total": 0, "l1": 0, "l2": 0, "l3": 0})
        l1_1 = _pct(s1["l1"], s1["total"])
        l1_2 = _pct(s2["l1"], s2["total"])
        l2_1 = _pct(s1["l2"], s1["total"])
        l2_2 = _pct(s2["l2"], s2["total"])
        sys.stdout.write(f"{f:<15} {l1_1:>9}% {l1_2:>9}% {l2_1:>9}% {l2_2:>9}%\n")

