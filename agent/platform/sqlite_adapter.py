"""SQLite platform: connection and default suite. Registers on import."""

import sqlite3
from urllib.parse import unquote, urlparse

from agent.platform.registry import register_platform


def _connect(connection_string: str) -> sqlite3.Connection:
    parsed = urlparse(connection_string)
    path = (parsed.path or parsed.netloc or "").strip()
    path = unquote(path)
    if not path or path == ":memory:" or path == "/":
        path = ":memory:"
    # sqlite:///absolute/path gives path="/absolute/path"; sqlite:////Users/... gives path="//Users/..."
    elif path.startswith("//"):
        path = "/" + path[2:]  # restore absolute path
    elif path.startswith("/"):
        pass  # already absolute
    else:
        path = path.lstrip("/") or ":memory:"
    return sqlite3.connect(path)


def _register() -> None:
    register_platform("sqlite", "sqlite", _connect, "common_sqlite")


_register()
