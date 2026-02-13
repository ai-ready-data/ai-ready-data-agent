"""Shared Rich console instance and helper functions for AIRD CLI output.

This module provides:

* ``get_console()`` — singleton ``rich.console.Console`` with the AIRD theme.
* ``is_interactive()`` — TTY detection helper.
* ``print_table()`` / ``print_panel()`` — convenience wrappers.
* ``print_success()`` / ``print_error()`` / ``print_warning()`` — semantic output.
* ``confirm()`` — thin wrapper around ``questionary.confirm``.
"""

from __future__ import annotations

import sys
from typing import Any, Optional, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.ui.themes import AIRD_THEME

# ---------------------------------------------------------------------------
# Singleton console
# ---------------------------------------------------------------------------

_console: Optional[Console] = None


def get_console() -> Console:
    """Return the shared ``Console`` instance (created on first call).

    The console uses stderr so that machine-readable output on stdout
    is never polluted by Rich markup.
    """
    global _console
    if _console is None:
        _console = Console(theme=AIRD_THEME, stderr=True)
    return _console


# ---------------------------------------------------------------------------
# TTY / interactivity detection
# ---------------------------------------------------------------------------


def is_interactive() -> bool:
    """Return ``True`` when stdin **and** stderr are connected to a TTY.

    This is the guard used to decide whether to show spinners, prompts,
    and coloured output.  When the process is piped or running inside CI
    the function returns ``False``.
    """
    return sys.stdin.isatty() and sys.stderr.isatty()


# ---------------------------------------------------------------------------
# Semantic output helpers
# ---------------------------------------------------------------------------


def print_success(message: str) -> None:
    """Print a success message with a green check-mark prefix."""
    get_console().print(f"[pass]✓[/pass] {message}")


def print_error(message: str) -> None:
    """Print an error message with a red cross prefix."""
    get_console().print(f"[fail]✗[/fail] {message}")


def print_warning(message: str) -> None:
    """Print a warning message with a yellow exclamation prefix."""
    get_console().print(f"[warn]![/warn] {message}")


# ---------------------------------------------------------------------------
# Structural helpers
# ---------------------------------------------------------------------------


def print_panel(content: str, *, title: Optional[str] = None, border_style: str = "border") -> None:
    """Render *content* inside a Rich ``Panel``.

    Parameters
    ----------
    content:
        The text (may contain Rich markup) to display.
    title:
        Optional panel title.
    border_style:
        Rich style name for the border (default ``"border"``).
    """
    get_console().print(Panel(content, title=title, border_style=border_style))


def print_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    title: Optional[str] = None,
) -> None:
    """Render a simple table to the console.

    Parameters
    ----------
    headers:
        Column header strings.
    rows:
        Iterable of row tuples/lists (one value per column).
    title:
        Optional table title.
    """
    table = Table(title=title, show_header=True, header_style="subheader")
    for h in headers:
        table.add_column(str(h))
    for row in rows:
        table.add_row(*(str(cell) for cell in row))
    get_console().print(table)


# ---------------------------------------------------------------------------
# Interactive prompt wrapper
# ---------------------------------------------------------------------------


def confirm(message: str, *, default: bool = False) -> bool:
    """Ask a yes/no question via ``questionary``.

    Falls back to *default* when the session is non-interactive.
    """
    if not is_interactive():
        return default

    import questionary

    return questionary.confirm(message, default=default).ask() or default

