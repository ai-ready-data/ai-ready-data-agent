"""AIRD UI package — Rich console helpers and interactive prompts.

Quick start::

    from agent.ui import console, is_interactive, print_success

    print_success("Assessment complete")
    if is_interactive():
        ...  # show spinners, prompts, etc.

The ``console`` object is a pre-configured ``rich.console.Console`` that
writes to *stderr* (so stdout stays clean for machine-readable output).
"""

from agent.ui.benchmark import render_benchmark
from agent.ui.console import (
    confirm,
    get_console,
    is_interactive,
    print_error,
    print_panel,
    print_success,
    print_table,
    print_warning,
)

# Convenience alias — ``from agent.ui import console``
console = get_console()

__all__ = [
    "confirm",
    "console",
    "get_console",
    "is_interactive",
    "print_error",
    "print_panel",
    "print_success",
    "print_table",
    "print_warning",
    "render_benchmark",
]

