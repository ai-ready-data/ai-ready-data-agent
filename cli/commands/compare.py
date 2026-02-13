"""``aird compare`` — run assessment on two tables and show side-by-side comparison.

Usage::

    aird compare -c "duckdb:///data.duckdb" --tables main.t1,main.t2
"""

from __future__ import annotations

import logging
from typing import List

from agent.config import Config
from agent.discovery import discover
from agent.run import run_tests
from agent.report import build_report
from agent.platform.registry import get_default_suite
from agent.thresholds import load_thresholds
from agent.ui.compare import render_comparison

logger = logging.getLogger(__name__)


def _parse_tables(raw: str) -> List[str]:
    """Split comma-separated table names, stripping whitespace."""
    return [t.strip() for t in raw.split(",") if t.strip()]


def run_compare(config: Config) -> None:
    """Run assessment on each table independently and render comparison.

    Expects ``config.compare_tables`` to be a list with a single
    comma-separated string (from ``--tables t1,t2``), or already split.
    """
    if not config.connection:
        raise ValueError("--connection (-c) required for compare")

    # Parse table names
    raw_tables = config.compare_tables
    if isinstance(raw_tables, list) and len(raw_tables) == 1:
        table_names = _parse_tables(raw_tables[0])
    elif isinstance(raw_tables, list) and len(raw_tables) > 1:
        table_names = raw_tables
    elif isinstance(raw_tables, str):
        table_names = _parse_tables(raw_tables)
    else:
        table_names = []

    if len(table_names) < 2:
        raise ValueError("--tables requires at least two comma-separated table names (e.g., --tables t1,t2)")

    thresholds = load_thresholds(config.thresholds_path)
    connection = config.connection

    table_reports = {}
    for table_name in table_names:
        logger.info("Assessing table: %s", table_name)
        inv = discover(connection, tables=[table_name])
        suite_name = config.suite if config.suite != "auto" else get_default_suite(connection)
        results = run_tests(
            connection,
            inv,
            suite_name=suite_name,
            thresholds=thresholds,
        )
        report = build_report(results, connection_fingerprint=connection)
        table_reports[table_name] = report

    render_comparison(table_reports, table_names=table_names)

