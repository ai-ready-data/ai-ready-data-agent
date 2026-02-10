"""Platform abstraction: registry, connection, read-only executor. Platform-specific adapters register here."""

from agent.platform.registry import get_platform, get_suite, register_platform
from agent.platform.connection import create_connection
from agent.platform.executor import execute_readonly

# Register built-in platforms and Clean suites on first use
import agent.platform.duckdb_adapter  # noqa: F401
import agent.platform.sqlite_adapter  # noqa: F401
import agent.suites.clean_duckdb  # noqa: F401 — "common" for DuckDB
import agent.suites.clean_sqlite  # noqa: F401 — "common_sqlite" for SQLite

__all__ = [
    "get_platform",
    "get_suite",
    "register_platform",
    "create_connection",
    "execute_readonly",
]
