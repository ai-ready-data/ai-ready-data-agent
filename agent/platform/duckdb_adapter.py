"""DuckDB platform: connection and default suite. Registers on import."""

from urllib.parse import unquote, urlparse

import duckdb

from agent.platform.registry import register_platform, register_suite


def _connect(connection_string: str):
    parsed = urlparse(connection_string)
    path = parsed.path or parsed.netloc or ":memory:"
    if path == ":memory:" or not path:
        path = ":memory:"
    else:
        path = unquote(path)
    return duckdb.connect(path)


# Minimal common suite: one test per factor 0 (Clean) requirement placeholder
_COMMON_TESTS = [
    {
        "id": "clean_table_count",
        "factor": "clean",
        "requirement": "table_discovery",
        "query": "SELECT COUNT(*) AS cnt FROM information_schema.tables",
        "target_type": "platform",
    },
]


def _register() -> None:
    register_platform("duckdb", "duckdb", _connect, "common")
    register_suite("common", _COMMON_TESTS)


_register()
