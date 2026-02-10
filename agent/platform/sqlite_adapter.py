"""SQLite platform: connection and default suite. Registers on import."""

import sqlite3
from urllib.parse import unquote, urlparse

from agent.platform.registry import register_platform


def _connect(connection_string: str) -> sqlite3.Connection:
    parsed = urlparse(connection_string)
    path = (parsed.path or parsed.netloc or "").strip().lstrip("/")
    if not path or path == ":memory:":
        path = ":memory:"
    else:
        path = unquote(path)
    return sqlite3.connect(path)


def _register() -> None:
    register_platform("sqlite", "sqlite", _connect, "common_sqlite")


_register()
