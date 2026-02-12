"""N-way benchmark comparison matrix for ``aird benchmark``.

Generalises the 2-way comparison in ``agent.ui.compare`` to an
arbitrary number of datasets (2–10+).  Each dataset gets one L1% and
one L2% column; rows are the six assessment factors plus an OVERALL
summary.  Colour coding highlights best/worst per row.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from agent.ui.compare import _extract_factor_stats, _pct
from agent.ui.console import get_console, is_interactive


# Six assessment factors in canonical order
_FACTORS = ["clean", "contextual", "consumable", "current", "correlated", "compliant"]


# ---------------------------------------------------------------------------
# Colour helpers (N-way: best = green, worst = red, middle = yellow)
# ---------------------------------------------------------------------------


def _colour_cell_nway(value: float, all_values: List[float]) -> str:
    """Return Rich-styled string based on rank among *all_values*.

    * Best (max) → ``[pass]``  (green)
    * Worst (min) → ``[fail]`` (red)
    * Tied for best or worst, or in between → ``[warn]`` (yellow)
    """
    text = "{0}%".format(value)
    best = max(all_values)
    worst = min(all_values)
    if best == worst:
        # All values identical — neutral
        return "[warn]{0}[/warn]".format(text)
    if value == best:
        return "[pass]{0}[/pass]".format(text)
    if value == worst:
        return "[fail]{0}[/fail]".format(text)
    return "[warn]{0}[/warn]".format(text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_benchmark(
    reports: Dict[str, dict],
    labels: Optional[List[str]] = None,
) -> None:
    """Render an N-way benchmark comparison matrix.

    Parameters
    ----------
    reports:
        Mapping of dataset label → report dict (same shape as
        ``build_report()`` output).
    labels:
        Ordered list of dataset labels.  Defaults to sorted keys of
        *reports*.
    """
    names = labels or sorted(reports.keys())
    if len(names) < 2:
        return

    # Extract per-factor stats for every dataset
    all_stats = {}  # type: Dict[str, Dict[str, Dict[str, Any]]]
    for name in names:
        all_stats[name] = _extract_factor_stats(reports[name])

    # Collect factors present in any report (canonical order first)
    all_factors = []  # type: List[str]
    for f in _FACTORS:
        for name in names:
            if f in all_stats[name]:
                all_factors.append(f)
                break
    # Append non-canonical factors
    seen = set(all_factors)
    for name in names:
        for f in sorted(all_stats[name].keys()):
            if f not in seen:
                all_factors.append(f)
                seen.add(f)

    if is_interactive():
        _render_rich(names, all_stats, all_factors)
    else:
        _render_plain(names, all_stats, all_factors)


# ---------------------------------------------------------------------------
# Helpers shared by both renderers
# ---------------------------------------------------------------------------

_EMPTY = {"total": 0, "l1": 0, "l2": 0, "l3": 0}


def _compute_row(
    factor: str,
    names: List[str],
    all_stats: Dict[str, Dict[str, Dict[str, Any]]],
) -> List[float]:
    """Return flat list [l1_0, l2_0, l1_1, l2_1, …] for one factor row."""
    values = []  # type: List[float]
    for name in names:
        s = all_stats[name].get(factor, _EMPTY)
        values.append(_pct(s["l1"], s["total"]))
        values.append(_pct(s["l2"], s["total"]))
    return values


def _compute_overall(
    names: List[str],
    all_stats: Dict[str, Dict[str, Dict[str, Any]]],
    factors: List[str],
) -> List[float]:
    """Return flat list of average L1%/L2% per dataset across all factors."""
    overall = []  # type: List[float]
    for name in names:
        l1_vals = []  # type: List[float]
        l2_vals = []  # type: List[float]
        for f in factors:
            s = all_stats[name].get(f, _EMPTY)
            l1_vals.append(_pct(s["l1"], s["total"]))
            l2_vals.append(_pct(s["l2"], s["total"]))
        avg_l1 = round(sum(l1_vals) / len(l1_vals), 1) if l1_vals else 0.0
        avg_l2 = round(sum(l2_vals) / len(l2_vals), 1) if l2_vals else 0.0
        overall.append(avg_l1)
        overall.append(avg_l2)
    return overall


# ---------------------------------------------------------------------------
# Rich (interactive) renderer
# ---------------------------------------------------------------------------


def _render_rich(
    names: List[str],
    all_stats: Dict[str, Dict[str, Dict[str, Any]]],
    factors: List[str],
) -> None:
    """Render Rich table to stderr console."""
    from rich.table import Table

    console = get_console()
    title = "Benchmark: {0}".format(" vs ".join(names))
    table = Table(title=title, show_header=True, header_style="subheader")
    table.add_column("Factor")
    for name in names:
        table.add_column("{0} L1%".format(name), justify="right")
        table.add_column("{0} L2%".format(name), justify="right")

    # Factor rows
    for f in factors:
        row_vals = _compute_row(f, names, all_stats)
        l1_vals = row_vals[0::2]
        l2_vals = row_vals[1::2]
        cells = []  # type: List[str]
        for i, name in enumerate(names):
            cells.append(_colour_cell_nway(l1_vals[i], l1_vals))
            cells.append(_colour_cell_nway(l2_vals[i], l2_vals))
        table.add_row(f, *cells)

    # OVERALL row
    overall = _compute_overall(names, all_stats, factors)
    l1_overall = overall[0::2]
    l2_overall = overall[1::2]
    overall_cells = []  # type: List[str]
    for i, name in enumerate(names):
        overall_cells.append(_colour_cell_nway(l1_overall[i], l1_overall))
        overall_cells.append(_colour_cell_nway(l2_overall[i], l2_overall))
    table.add_row("[bold]OVERALL[/bold]", *overall_cells, end_section=True)

    console.print(table)

    # Winner line
    if l1_overall:
        best_idx = l1_overall.index(max(l1_overall))
        console.print(
            "\U0001f3c6 Best overall (L1): {0} ({1}%)".format(
                names[best_idx], l1_overall[best_idx]
            )
        )


# ---------------------------------------------------------------------------
# Plain-text (piped) renderer
# ---------------------------------------------------------------------------


def _render_plain(
    names: List[str],
    all_stats: Dict[str, Dict[str, Dict[str, Any]]],
    factors: List[str],
) -> None:
    """Render tab-separated plain text to stdout (no ANSI)."""
    # Header
    parts = ["Factor"]
    for name in names:
        parts.append("{0} L1%".format(name))
        parts.append("{0} L2%".format(name))
    sys.stdout.write("\t".join(parts) + "\n")

    # Factor rows
    for f in factors:
        row_vals = _compute_row(f, names, all_stats)
        row_parts = [f]
        for v in row_vals:
            row_parts.append("{0}%".format(v))
        sys.stdout.write("\t".join(row_parts) + "\n")

    # OVERALL row
    overall = _compute_overall(names, all_stats, factors)
    ov_parts = ["OVERALL"]
    for v in overall:
        ov_parts.append("{0}%".format(v))
    sys.stdout.write("\t".join(ov_parts) + "\n")

    # Winner line
    l1_overall = overall[0::2]
    if l1_overall:
        best_idx = l1_overall.index(max(l1_overall))
        sys.stdout.write(
            "Best overall (L1): {0} ({1}%)\n".format(
                names[best_idx], l1_overall[best_idx]
            )
        )

