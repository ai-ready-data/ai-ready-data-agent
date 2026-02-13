"""Connection factory: parse connection string and return a platform connection. Delegates to registry."""

from typing import Any

from agent.platform import get_platform


def create_connection(connection_string: str) -> Any:
    """Create a connection for the given string. Returns platform-specific handle (e.g. DuckDB connection)."""
    _, conn, _ = get_platform(connection_string)
    return conn
