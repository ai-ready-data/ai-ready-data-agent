"""Resolve args and env into a single config object. CLI layer only; no business logic."""

import os
from dataclasses import dataclass, field, fields
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

    # Quick actions
    factor_filter: Optional[str] = None  # --factor: filter to single factor
    compare_tables: list = field(default_factory=list)  # --tables for compare
    rerun_id: Optional[str] = None  # --id for rerun (defaults to most recent)

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

    def with_args(self, **overrides) -> "Config":
        """Return a new config with overrides from CLI args.

        Accepts any Config field name as a keyword argument.  Values that are
        ``None`` are ignored (the current value is kept).
        """
        valid_names = {f.name for f in fields(self)}
        bad = set(overrides) - valid_names
        if bad:
            raise TypeError(f"Unknown Config fields: {bad}")
        merged = {
            f.name: overrides[f.name] if overrides.get(f.name) is not None else getattr(self, f.name)
            for f in fields(self)
        }
        return Config(**merged)
