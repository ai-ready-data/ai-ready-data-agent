"""Rich progress bar for test execution.

Provides ``TestProgressBar`` — a context manager that wraps
``rich.progress.Progress`` and exposes a callback compatible with
``run_tests(progress_callback=...)``.
"""

from __future__ import annotations

from typing import Optional

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from agent.ui.console import get_console


class TestProgressBar:
    """Context manager that displays a Rich progress bar during test execution.

    Usage::

        with TestProgressBar() as pb:
            results = run_tests(..., progress_callback=pb.callback)
    """

    def __init__(self) -> None:
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None
        self._pass_count: int = 0
        self._fail_count: int = 0

    def __enter__(self) -> "TestProgressBar":
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("[pass]✓{task.fields[passed]}[/pass]  [fail]✗{task.fields[failed]}[/fail]"),
            console=get_console(),
            transient=False,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "Running tests…",
            total=None,
            passed=0,
            failed=0,
        )
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._progress is not None:
            self._progress.stop()

    def callback(self, current_index: int, total: int, test_result: dict) -> None:
        """Progress callback compatible with ``run_tests(progress_callback=...)``."""
        if self._progress is None or self._task_id is None:
            return

        # Update total on first call (not known until tests are expanded)
        if self._progress.tasks[self._task_id].total is None:
            self._progress.update(self._task_id, total=total)

        # Track pass/fail
        passed = test_result.get("l1_pass", False)
        if passed:
            self._pass_count += 1
        else:
            self._fail_count += 1

        # Build description from test info
        test_id = test_result.get("test_id", "")
        factor = test_result.get("factor", "")
        status = "[pass]PASS[/pass]" if passed else "[fail]FAIL[/fail]"
        desc = f"{factor}/{_short_id(test_id)} {status}"

        self._progress.update(
            self._task_id,
            completed=current_index + 1,
            description=desc,
            passed=self._pass_count,
            failed=self._fail_count,
        )


def _short_id(test_id: str) -> str:
    """Shorten a test_id like 'null_rate|main|products|name' to 'products.name'."""
    parts = test_id.split("|")
    if len(parts) >= 3:
        # requirement|schema|table[|column]
        table = parts[2]
        col = parts[3] if len(parts) > 3 else None
        return f"{table}.{col}" if col else table
    return test_id

