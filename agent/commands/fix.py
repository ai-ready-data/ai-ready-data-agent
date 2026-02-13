"""``aird fix`` — generate remediation scripts from failed assessment results.

Usage::

    aird fix                    # use latest assessment
    aird fix --id <uuid>        # use specific assessment
    aird fix --dry-run          # print suggestions only, do not write files
    aird fix -o ./remediation   # write scripts to directory
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from agent.config import Config
from agent import storage
from agent.report import load_report_from_storage
from agent.remediation import generate_fix_suggestions

from agent.exceptions import UsageError


def _load_report(cfg: Config) -> dict:
    """Load report from --id, or latest assessment."""
    conn = storage.get_connection(cfg.db_path)
    try:
        report_id = cfg.report_id
        if report_id:
            report = storage.get_report(conn, report_id)
            if not report:
                raise UsageError(f"Assessment not found: {report_id}")
            return report

        # Latest: get most recent from history
        items = storage.list_assessments(conn, limit=1)
        if not items:
            raise UsageError("No assessments in history. Run `aird assess` first.")
        report = storage.get_report(conn, items[0]["id"])
        if not report:
            raise UsageError("Could not load latest assessment.")
        return report
    finally:
        conn.close()


def _render_suggestions_plain(suggestions: list) -> str:
    """Render suggestions as plain text."""
    lines = []
    for i, s in enumerate(suggestions, 1):
        lines.append(f"--- {i}. {s['factor']}/{s['requirement']} ---")
        lines.append(f"Target: {s['schema']}.{s['table']}" + (f".{s['column']}" if s.get('column') else ""))
        lines.append(f"{s['description']}")
        lines.append("")
        lines.append(s["sql"])
        lines.append("")
    return "\n".join(lines)


def _render_suggestions_rich(suggestions: list) -> None:
    """Render suggestions using Rich."""
    from rich.console import Group
    from rich.panel import Panel
    from rich.syntax import Syntax
    from agent.ui.console import get_console

    console = get_console()
    for i, s in enumerate(suggestions, 1):
        target = f"{s['schema']}.{s['table']}" + (f".{s['column']}" if s.get('column') else "")
        content = Group(
            f"[dim]{s['description']}[/dim]",
            "",
            Syntax(s["sql"], "sql", theme="monokai", line_numbers=False),
        )
        console.print(Panel(content, title=f"{i}. {s['factor']}/{s['requirement']} — {target}", border_style="blue"))


def run_fix(cfg: Config) -> None:
    """Run the fix command: load report, generate suggestions, output or write."""
    report = _load_report(cfg)
    suggestions = generate_fix_suggestions(report)

    if not suggestions:
        if sys.stdout.isatty():
            from agent.ui.console import get_console
            get_console().print("[pass]No failed tests to remediate.[/pass]")
        else:
            sys.stdout.write("No failed tests to remediate.\n")
        return

    dry_run = cfg.dry_run
    output_dir = getattr(cfg, "fix_output_dir", None)

    if dry_run or not output_dir:
        # Print to stdout
        if sys.stdout.isatty():
            from agent.ui.console import get_console
            get_console().print(f"\n[bold]Remediation suggestions ({len(suggestions)} failures)[/bold]\n")
            _render_suggestions_rich(suggestions)
            if dry_run:
                get_console().print("\n[dim]--dry-run: No files written. Run without --dry-run and -o <dir> to write scripts.[/dim]")
        else:
            sys.stdout.write(_render_suggestions_plain(suggestions))
        return

    # Write to output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(suggestions, 1):
        safe_name = f"{i:02d}_{s['requirement']}_{s['table']}".replace(".", "_")
        file_path = out_path / f"{safe_name}.sql"
        file_path.write_text(f"-- {s['factor']}/{s['requirement']}: {s['description']}\n\n{s['sql']}\n")

    if sys.stdout.isatty():
        from agent.ui.console import get_console
        get_console().print(f"[pass]Wrote {len(suggestions)} remediation scripts to {out_path}[/pass]")
    else:
        sys.stdout.write(f"Wrote {len(suggestions)} scripts to {out_path}\n")
