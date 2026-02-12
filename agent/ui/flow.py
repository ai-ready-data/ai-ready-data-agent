"""Guided interactive assessment flow.

Orchestrates all interactive elements into a cohesive experience
when ``aird assess -i`` is used: welcome → discover → scope selection →
preview → confirm → run with progress → survey → summary.
"""

from __future__ import annotations

import logging

from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from agent.config import Config
from agent.ui.console import confirm, get_console

logger = logging.getLogger(__name__)


class InteractiveAssessFlow:
    """Orchestrates the full interactive assessment experience."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.console = get_console()

    def run(self) -> dict:
        """Run the full guided flow. Returns the report dict."""
        try:
            self._show_welcome()

            # Step 1: Discovery with spinner
            inv = self._discover_with_spinner()

            # Step 2: Scope selection (reuse existing discovery UI)
            inv = self._select_scope(inv)

            # Step 3: Preview tests and confirm
            if not self._preview_and_confirm(inv):
                raise SystemExit(0)

            # Step 4: Run tests with progress bar
            results = self._run_with_progress(inv)

            # Step 5: Build report (including survey if enabled)
            report = self._build_report(results, inv)

            # Step 6: Show summary panel
            self._show_summary(report)

            return report
        except KeyboardInterrupt:
            self.console.print()
            self.console.print("[warn]Aborted by user.[/warn]")
            raise SystemExit(0)

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    def _show_welcome(self) -> None:
        """Show a welcome panel with connection info and suite name."""
        connection = self.config.connection or "unknown"
        suite = self.config.suite or "auto"
        lines = [
            "[header]AI-Ready Data Assessment[/header]",
            "",
            "[muted]Connection:[/muted]  %s" % connection,
            "[muted]Suite:[/muted]       %s" % suite,
        ]
        if self.config.target_workload:
            lines.append("[muted]Workload:[/muted]    %s" % self.config.target_workload)
        if self.config.survey:
            lines.append("[muted]Survey:[/muted]      enabled")
        self.console.print()
        self.console.print(Panel("\n".join(lines), border_style="border"))

    def _discover_with_spinner(self) -> dict:
        """Run discovery with a Rich spinner."""
        from agent.discovery import discover

        self.console.print(Rule("[header]Step 1: Discovery[/header]", style="border"))
        schemas = self.config.schemas or None
        tables = self.config.tables or None

        with self.console.status("[info]Discovering schemas and tables…[/info]"):
            inv = discover(
                self.config.connection,
                schemas=schemas,
                tables=tables,
            )

        n_schemas = len(inv.get("schemas", []))
        n_tables = len(inv.get("tables", []))
        n_cols = len(inv.get("columns", []))
        self.console.print(
            "[pass]✓[/pass] Found %d schema(s), %d table(s), %d column(s)"
            % (n_schemas, n_tables, n_cols)
        )
        return inv

    def _select_scope(self, inv: dict) -> dict:
        """Show discovery tree and let user select tables."""
        from agent.ui.discovery import (
            filter_inventory,
            select_tables,
            show_discovery_tree,
        )

        self.console.print(Rule("[header]Step 2: Scope Selection[/header]", style="border"))
        show_discovery_tree(inv)
        selected = select_tables(inv)
        if selected:
            inv = filter_inventory(inv, selected)
        n_tables = len(inv.get("tables", []))
        self.console.print(
            "[pass]✓[/pass] %d table(s) selected for assessment" % n_tables
        )
        return inv

    def _preview_and_confirm(self, inv: dict) -> bool:
        """Show a dry-run preview and ask user to confirm."""
        from agent.run import run_tests
        from agent.thresholds import load_thresholds

        self.console.print(Rule("[header]Step 3: Test Preview[/header]", style="border"))

        thresholds = load_thresholds(self.config.thresholds_path)
        preview_results = run_tests(
            self.config.connection,
            inv,
            suite_name=self.config.suite,
            dry_run=True,
            thresholds=thresholds,
        )

        preview = preview_results.get("preview", [])
        test_count = preview_results.get("test_count", 0)

        # Build a Rich table grouped by factor
        factor_counts = {}  # type: dict[str, int]
        for t in preview:
            factor = t.get("factor", "unknown")
            factor_counts[factor] = factor_counts.get(factor, 0) + 1

        table = Table(title="Tests to Run", show_header=True, header_style="subheader")
        table.add_column("Factor")
        table.add_column("Tests", justify="right")

        for factor in sorted(factor_counts):
            style = "factor.%s" % factor if factor in (
                "clean", "contextual", "consumable", "current", "correlated", "compliant"
            ) else ""
            table.add_row(
                "[%s]%s[/%s]" % (style, factor.title(), style) if style else factor.title(),
                str(factor_counts[factor]),
            )
        table.add_section()
        table.add_row("[bold]Total[/bold]", "[bold]%d[/bold]" % test_count)

        self.console.print(table)
        self.console.print()

        return confirm("Proceed with assessment?", default=True)

    def _run_with_progress(self, inv: dict) -> dict:
        """Run tests with a Rich progress bar."""
        from agent.audit import AuditSink
        from agent.run import run_tests
        from agent.thresholds import load_thresholds
        from agent.ui.progress import TestProgressBar

        self.console.print(Rule("[header]Step 4: Running Tests[/header]", style="border"))

        thresholds = load_thresholds(self.config.thresholds_path)
        audit = AuditSink(self.config.db_path, self.config.audit) if self.config.audit else None

        with TestProgressBar() as pb:
            results = run_tests(
                self.config.connection,
                inv,
                suite_name=self.config.suite,
                dry_run=False,
                audit=audit,
                thresholds=thresholds,
                progress_callback=pb.callback,
            )

        self.console.print()
        return results

    def _build_report(self, results: dict, inv: dict) -> dict:
        """Build the report, optionally running the survey."""
        from agent.pipeline import _fingerprint, _load_context, _load_survey_answers
        from agent.platform.registry import get_default_suite
        from agent.questions_loader import get_suite_questions
        from agent.report import build_report
        from agent.survey import run_survey

        self.console.print(Rule("[header]Step 5: Building Report[/header]", style="border"))

        question_results = None
        if self.config.survey:
            default_suite = get_default_suite(self.config.connection)
            resolved_suite = self.config.suite if self.config.suite != "auto" else default_suite
            questions = get_suite_questions(resolved_suite)
            answers = _load_survey_answers(self.config.survey_answers_path)
            question_results = run_survey(
                questions=questions, answers=answers, interactive=self.config.interactive
            )

        context = _load_context(self.config.context_path)
        target_workload = self.config.target_workload or (context or {}).get("target_level")

        report = build_report(
            results,
            inventory=inv,
            connection_fingerprint=_fingerprint(self.config.connection),
            question_results=question_results,
            target_workload=target_workload,
        )
        if context:
            report["user_context"] = context

        self.console.print("[pass]✓[/pass] Report built")
        return report

    def _show_summary(self, report: dict) -> None:
        """Show a summary panel with pass/fail counts per factor."""
        self.console.print(Rule("[header]Step 6: Results Summary[/header]", style="border"))

        summary = report.get("summary", {})
        total = summary.get("total_tests", 0)
        factor_summary = report.get("factor_summary", [])

        # Build a Rich table for factor results
        table = Table(show_header=True, header_style="subheader")
        table.add_column("Factor")
        table.add_column("Tests", justify="right")
        table.add_column("L1 %", justify="right")
        table.add_column("L2 %", justify="right")
        table.add_column("L3 %", justify="right")

        def _pct_cell(pct: float) -> str:
            if pct >= 80:
                return "[pass]%s%%[/pass]" % pct
            elif pct >= 50:
                return "[warn]%s%%[/warn]" % pct
            else:
                return "[fail]%s%%[/fail]" % pct

        for fs in factor_summary:
            factor = fs.get("factor", "unknown")
            style = "factor.%s" % factor if factor in (
                "clean", "contextual", "consumable", "current", "correlated", "compliant"
            ) else ""
            factor_label = (
                "[%s]%s[/%s]" % (style, factor.title(), style) if style else factor.title()
            )
            table.add_row(
                factor_label,
                str(fs.get("total_tests", 0)),
                _pct_cell(fs.get("l1_pct", 0)),
                _pct_cell(fs.get("l2_pct", 0)),
                _pct_cell(fs.get("l3_pct", 0)),
            )

        table.add_section()
        table.add_row(
            "[bold]Overall[/bold]",
            "[bold]%d[/bold]" % total,
            "[bold]%s%%[/bold]" % summary.get("l1_pct", 0),
            "[bold]%s%%[/bold]" % summary.get("l2_pct", 0),
            "[bold]%s%%[/bold]" % summary.get("l3_pct", 0),
        )

        self.console.print(table)
        self.console.print()

        # Overall verdict
        l1_pct = summary.get("l1_pct", 0)
        if l1_pct == 100:
            self.console.print("[pass]✓ All L1 tests passed — data is analytics-ready![/pass]")
        elif l1_pct >= 80:
            self.console.print("[warn]! Most L1 tests passed (%s%%) — minor issues to address.[/warn]" % l1_pct)
        else:
            self.console.print("[fail]✗ L1 pass rate is %s%% — significant issues found.[/fail]" % l1_pct)
        self.console.print()

