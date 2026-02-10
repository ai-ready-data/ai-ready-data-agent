"""Platform abstraction: registry, connection, read-only executor. Platform-specific adapters register here."""

from agent.platform.registry import get_platform, get_suite, register_platform
from agent.platform.connection import create_connection
from agent.platform.executor import execute_readonly

# Register built-in platforms (DuckDB) and Clean suite on first use
import agent.platform.duckdb_adapter  # noqa: F401
import agent.suites.clean_duckdb  # noqa: F401 — overwrites "common" with Clean suite

__all__ = [
    "get_platform",
    "get_suite",
    "register_platform",
    "create_connection",
    "execute_readonly",
]
