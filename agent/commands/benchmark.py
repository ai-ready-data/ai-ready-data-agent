"""``aird benchmark`` — run assessment on multiple connections and compare results.

Usage::

    aird benchmark -c "duckdb:///a.duckdb" -c "duckdb:///b.duckdb"
    aird benchmark -c conn1 -c conn2 --label "Prod,Staging"
"""

from __future__ import annotations

import logging
import os
import re
from typing import List, Optional

from agent.config import Config
from agent.discovery import discover
from agent.run import run_tests
from agent.report import build_report
from agent.platform.registry import get_default_suite
from agent.thresholds import load_thresholds

logger = logging.getLogger(__name__)


def _label_from_connection(connection: str) -> str:
    """Extract a short label from a connection string.

    Examples:
        duckdb:///path/to/sales.duckdb  -> sales
        sqlite:///data/warehouse.db     -> warehouse
        snowflake://account/db          -> db
    """
    # Strip scheme
    rest = connection.split("://", 1)[-1] if "://" in connection else connection
    # Take the last path component and strip extension
    basename = os.path.basename(rest.rstrip("/"))
    name = re.sub(r"\.[^.]+$", "", basename) if basename else rest
    return name or connection


def _parse_labels(raw_labels: List[str], connections: List[str]) -> List[str]:
    """Resolve labels list: expand comma-separated values, auto-generate missing ones.

    If the user passes ``--label "Prod,Staging"`` we get ``["Prod,Staging"]``.
    We split on commas and pad/truncate to match the number of connections.
    """
    expanded: List[str] = []
    for item in raw_labels:
        expanded.extend(part.strip() for part in item.split(",") if part.strip())

    # Pad with auto-generated labels if fewer labels than connections
    for i in range(len(expanded), len(connections)):
        expanded.append(_label_from_connection(connections[i]))

    # Truncate if more labels than connections
    return expanded[: len(connections)]


def run_benchmark(config: Config) -> None:
    """Run assessment on each connection independently and render benchmark comparison.

    Expects ``config.benchmark_connections`` to contain at least two connection
    strings (from repeatable ``-c``).
    """
    connections = config.benchmark_connections
    if len(connections) < 2:
        raise ValueError(
            "benchmark requires at least 2 connections "
            "(use repeatable -c, e.g. aird benchmark -c conn1 -c conn2)"
        )

    labels = _parse_labels(config.benchmark_labels, connections)
    thresholds = load_thresholds(config.thresholds_path)

    reports: List[dict] = []
    for i, connection in enumerate(connections):
        label = labels[i]
        logger.info("Benchmarking [%s]: %s", label, connection)

        inv = discover(connection)
        suite_name = (
            config.suite if config.suite != "auto" else get_default_suite(connection)
        )
        results = run_tests(
            connection,
            inv,
            suite_name=suite_name,
            thresholds=thresholds,
            factor_filter=config.factor_filter,
        )
        report = build_report(results, connection_fingerprint=connection)
        report["_benchmark_label"] = label
        reports.append(report)

    # Renderer is provided by Task 24 (agent.ui.benchmark).
    # Import is deferred so the module can be created independently.
    from agent.ui.benchmark import render_benchmark  # type: ignore[import-not-found]

    render_benchmark(reports, labels=labels)

