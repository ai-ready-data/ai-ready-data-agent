"""Resolve args and env into a single config object. CLI layer only; no business logic."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agent.constants import OutputFormat


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.environ.get(key, "").strip().lower()
    if v in ("1", "true", "yes"):  # noqa: SIM108
        return True
    if v in ("0", "false", "no", ""):
        return False
    return default


def default_db_path() -> Path:
    return Path.home() / ".aird" / "assessments.db"


@dataclass
class Config:
    """Resolved configuration from env + CLI args."""

    # Connection and scope
    connection: Optional[str] = None  # single connection string
    schemas: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    context_path: Optional[Path] = None

    # Pipeline
    suite: str = "auto"
    thresholds_path: Optional[Path] = None
    output: str = OutputFormat.MARKDOWN  # stdout | markdown | json:<path>
    no_save: bool = False
    compare: bool = False
    dry_run: bool = False
    interactive: bool = False
    audit: bool = False
    survey: bool = False
    survey_answers_path: Optional[Path] = None
    target_workload: Optional[str] = None  # analytics, rag, training -> maps to l1, l2, l3

    # Paths and logging
    db_path: Path = field(default_factory=default_db_path)
    log_level: str = "info"

    # Composable: artifact paths (set by CLI when invoking discover/run/report/save)
    inventory_path: Optional[str] = None  # path or "-" for stdin
    results_path: Optional[str] = None
    report_path: Optional[str] = None

    # report --id
    report_id: Optional[str] = None

    # history
    history_connection_filter: Optional[str] = None
    history_limit: int = 20

    # diff
    diff_left: Optional[str] = None  # id or path
    diff_right: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load defaults from environment only."""
        return cls(
            connection=_env("AIRD_CONNECTION_STRING"),
            context_path=Path(p) if (p := _env("AIRD_CONTEXT")) else None,
            thresholds_path=Path(p) if (p := _env("AIRD_THRESHOLDS")) else None,
            output=_env("AIRD_OUTPUT") or OutputFormat.MARKDOWN,
            log_level=_env("AIRD_LOG_LEVEL") or "info",
            audit=_env_bool("AIRD_AUDIT"),
            db_path=Path(p) if (p := _env("AIRD_DB_PATH")) else default_db_path(),
        )

    def with_args(
        self,
        *,
        connection: Optional[str] = None,
        schemas: Optional[list[str]] = None,
        tables: Optional[list[str]] = None,
        context_path: Optional[Path] = None,
        suite: Optional[str] = None,
        thresholds_path: Optional[Path] = None,
        output: Optional[str] = None,
        no_save: Optional[bool] = None,
        compare: Optional[bool] = None,
        dry_run: Optional[bool] = None,
        interactive: Optional[bool] = None,
        audit: Optional[bool] = None,
        survey: Optional[bool] = None,
        survey_answers_path: Optional[Path] = None,
        target_workload: Optional[str] = None,
        db_path: Optional[Path] = None,
        log_level: Optional[str] = None,
        inventory_path: Optional[str] = None,
        results_path: Optional[str] = None,
        report_path: Optional[str] = None,
        report_id: Optional[str] = None,
        history_connection_filter: Optional[str] = None,
        history_limit: Optional[int] = None,
        diff_left: Optional[str] = None,
        diff_right: Optional[str] = None,
    ) -> "Config":
        """Return a new config with overrides from CLI args."""
        return Config(
            connection=connection if connection is not None else self.connection,
            schemas=schemas if schemas is not None else self.schemas,
            tables=tables if tables is not None else self.tables,
            context_path=context_path if context_path is not None else self.context_path,
            suite=suite if suite is not None else self.suite,
            thresholds_path=thresholds_path if thresholds_path is not None else self.thresholds_path,
            output=output if output is not None else self.output,
            no_save=no_save if no_save is not None else self.no_save,
            compare=compare if compare is not None else self.compare,
            dry_run=dry_run if dry_run is not None else self.dry_run,
            interactive=interactive if interactive is not None else self.interactive,
            audit=audit if audit is not None else self.audit,
            survey=survey if survey is not None else self.survey,
            survey_answers_path=survey_answers_path if survey_answers_path is not None else self.survey_answers_path,
            target_workload=target_workload if target_workload is not None else self.target_workload,
            db_path=db_path if db_path is not None else self.db_path,
            log_level=log_level if log_level is not None else self.log_level,
            inventory_path=inventory_path if inventory_path is not None else self.inventory_path,
            results_path=results_path if results_path is not None else self.results_path,
            report_path=report_path if report_path is not None else self.report_path,
            report_id=report_id if report_id is not None else self.report_id,
            history_connection_filter=history_connection_filter
            if history_connection_filter is not None
            else self.history_connection_filter,
            history_limit=history_limit if history_limit is not None else self.history_limit,
            diff_left=diff_left if diff_left is not None else self.diff_left,
            diff_right=diff_right if diff_right is not None else self.diff_right,
        )
