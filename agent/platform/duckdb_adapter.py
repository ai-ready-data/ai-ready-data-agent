"""DuckDB platform: connection and default suite. Registers on import."""

from urllib.parse import unquote, urlparse

import duckdb

from agent.platform.registry import register_platform


def _connect(connection_string: str):
    parsed = urlparse(connection_string)
    path = parsed.path or parsed.netloc or ":memory:"
    if path == ":memory:" or not path:
        path = ":memory:"
    else:
        path = unquote(path)
    return duckdb.connect(path)


def _register() -> None:
    register_platform("duckdb", "duckdb", _connect, "common")


_register()
