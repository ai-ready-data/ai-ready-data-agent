"""Platform abstraction: registry, connection, read-only executor. Platform-specific adapters register here."""

from agent.platform.registry import get_platform, get_suite, register_platform
from agent.platform.connection import create_connection
from agent.platform.executor import execute_readonly

# Register built-in platforms and Clean suites on first use
import agent.platform.duckdb_adapter  # noqa: F401
import agent.platform.sqlite_adapter  # noqa: F401
try:
    import agent.platform.snowflake_adapter  # noqa: F401 — optional: pip install aird-agent[snowflake]
except ImportError:
    pass
import agent.suites.clean_duckdb  # noqa: F401 — "common" for DuckDB
import agent.suites.clean_sqlite  # noqa: F401 — "common_sqlite" for SQLite
import agent.suites.clean_snowflake  # noqa: F401 — "common_snowflake" for Snowflake

__all__ = [
    "get_platform",
    "get_suite",
    "register_platform",
    "create_connection",
    "execute_readonly",
]
