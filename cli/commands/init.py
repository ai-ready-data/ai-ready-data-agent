"""Interactive init wizard: guides first-time users through AIRD setup.

Uses ``questionary`` for keyboard-driven prompts (arrow-key selection,
validated text input, confirm dialogs) and ``rich`` via ``agent.ui`` for
styled terminal output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from agent.ui import print_error, print_panel, print_success, print_warning

try:
    import questionary
    from questionary import Choice

    _HAS_QUESTIONARY = True
except ImportError:  # pragma: no cover
    _HAS_QUESTIONARY = False

# Platform choices shown to the user: (label, scheme, example connection string)
PLATFORMS = [
    ("DuckDB", "duckdb", "duckdb:///path/to/your/database.duckdb"),
    ("SQLite", "sqlite", "sqlite:///path/to/your/database.db"),
    ("Snowflake", "snowflake", "snowflake://user:pass@account/database/schema?warehouse=WH"),
]

# Workload choices: (label, config value, description)
WORKLOADS = [
    ("Analytics (L1)", "analytics", "dashboards, BI, basic reporting"),
    ("RAG (L2)", "rag", "retrieval-augmented generation, search"),
    ("Training (L3)", "training", "model training, fine-tuning"),
]

CONFIG_DIR = Path.home() / ".aird"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_connection(text: str) -> object:
    """Return *True* if valid, or an error string for questionary validation."""
    if not text or not text.strip():
        return "Connection string cannot be empty."
    if "://" not in text:
        return "Connection string must contain '://' (e.g. duckdb:///path.db)."
    return True


# ---------------------------------------------------------------------------
# Step functions (questionary-based)
# ---------------------------------------------------------------------------


def _step_platform() -> Tuple[str, str, str]:
    """Step 1: Choose platform via arrow-key selection.

    Returns ``(label, scheme, example)``.
    """
    choices = [
        Choice(title=label, value=(label, scheme, example))
        for label, scheme, example in PLATFORMS
    ]
    result = questionary.select(
        "Choose your data platform:",
        choices=choices,
        instruction="(use arrow keys)",
    ).ask()
    if result is None:
        # User pressed Ctrl-C inside questionary
        raise KeyboardInterrupt
    return result


def _step_connection(scheme: str, example: str) -> str:
    """Step 2: Get connection string with validation and placeholder example."""
    result = questionary.text(
        "Enter your connection string:",
        instruction=example,
        validate=_validate_connection,
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result.strip()


def _step_test_connection(connection_string: str) -> Tuple[str, Optional[Dict]]:
    """Step 3: Test the connection and return ``(connection_string, inventory)``.

    Retries on failure, allowing the user to supply a new connection string.
    """
    while True:
        try:
            from agent.discovery import discover

            inv = discover(connection_string)
            table_count = len(inv.get("tables", []))
            schema_count = len(inv.get("schemas", []))
            print_success(
                f"Connected! Found {table_count} table(s) in {schema_count} schema(s)."
            )
            return connection_string, inv
        except Exception as e:
            print_error(f"Connection failed: {e}")
            retry = questionary.confirm(
                "Retry with a different connection string?", default=True
            ).ask()
            if retry is None or not retry:
                raise SystemExit(1)
            new_conn = questionary.text(
                "Enter your connection string:",
                validate=_validate_connection,
            ).ask()
            if new_conn is None:
                raise KeyboardInterrupt
            connection_string = new_conn.strip()


def _step_workload() -> str:
    """Step 4: Choose target workload via arrow-key selection.

    Returns the config value (``analytics`` / ``rag`` / ``training``).
    """
    choices = [
        Choice(title=f"{label} — {desc}", value=value)
        for label, value, desc in WORKLOADS
    ]
    result = questionary.select(
        "What will you use this data for?",
        choices=choices,
        instruction="(use arrow keys)",
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def _step_save(connection_string: str, workload: str) -> None:
    """Step 5: Optionally save config to ``~/.aird/config.yaml``."""
    save = questionary.confirm(
        f"Save configuration to {CONFIG_PATH}?", default=True
    ).ask()
    if save is None:
        raise KeyboardInterrupt
    if not save:
        print_warning("Skipped saving configuration.")
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = (
        f"# Generated by aird init\n"
        f'connection: "{connection_string}"\n'
        f"target_workload: {workload}\n"
    )
    CONFIG_PATH.write_text(content)
    print_success(f"Saved to {CONFIG_PATH}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_init() -> None:
    """Main entry point for the init wizard."""
    # Non-interactive detection
    if not sys.stdin.isatty():
        print_error("aird init requires an interactive terminal.")
        sys.exit(1)

    if not _HAS_QUESTIONARY:
        print_error(
            "The 'questionary' package is required for the init wizard. "
            "Install it with: pip install questionary"
        )
        sys.exit(1)

    try:
        print_panel(
            "[bold]Welcome to AIRD[/bold] — AI-Ready Data Assessment\n\n"
            "This wizard will help you configure your first connection.",
            title="aird init",
        )

        label, scheme, example = _step_platform()
        connection_string = _step_connection(scheme, example)
        connection_string, _inv = _step_test_connection(connection_string)
        workload = _step_workload()
        _step_save(connection_string, workload)

        print_success(
            f'You\'re all set! Run: [bold]aird assess -c "{connection_string}"[/bold]'
        )

    except KeyboardInterrupt:
        print_warning("\nCancelled.")
        sys.exit(0)

