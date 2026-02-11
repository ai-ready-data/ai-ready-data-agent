"""Snowflake platform via snowflake-connector-python. Works in any environment (CI, notebooks, servers). Registers on import."""

import os
from urllib.parse import parse_qs, unquote, urlparse

from agent.platform.registry import register_platform

try:
    import snowflake.connector
except ImportError:
    snowflake = None  # type: ignore[assignment]


def _parse_connection_string(connection_string: str) -> dict:
    """Parse snowflake:// URL or use env vars. URL: snowflake://user:password@account/database/schema?warehouse=wh."""
    out = {}
    if "://" in connection_string:
        parsed = urlparse(connection_string)
        if parsed.scheme.lower() != "snowflake":
            raise ValueError("Snowflake connection string must use scheme snowflake://")
        # user:password@account
        if parsed.username:
            out["user"] = unquote(parsed.username)
        if parsed.password:
            out["password"] = unquote(parsed.password)
        # hostname as account (no .snowflakecomputing.com)
        if parsed.hostname:
            out["account"] = unquote(parsed.hostname)
        # path: /database or /database/schema
        path = (parsed.path or "").strip("/")
        if path:
            parts = path.split("/")
            out["database"] = unquote(parts[0])
            if len(parts) > 1:
                out["schema"] = unquote(parts[1])
        # query: warehouse=wh, role=...
        if parsed.query:
            qs = parse_qs(parsed.query, keep_blank_values=True)
            if "warehouse" in qs:
                out["warehouse"] = qs["warehouse"][0]
            if "role" in qs:
                out["role"] = qs["role"][0]
    # Env fallback (for CI/notebooks/servers)
    if not out.get("account"):
        out["account"] = os.environ.get("SNOWFLAKE_ACCOUNT", "").strip() or None
    if not out.get("user"):
        out["user"] = os.environ.get("SNOWFLAKE_USER", "").strip() or None
    if not out.get("password"):
        out["password"] = os.environ.get("SNOWFLAKE_PASSWORD", "").strip() or os.environ.get("SNOWSQL_PWD", "").strip() or None
    if not out.get("database"):
        out["database"] = os.environ.get("SNOWFLAKE_DATABASE", "").strip() or None
    if not out.get("schema"):
        out["schema"] = os.environ.get("SNOWFLAKE_SCHEMA", "").strip() or None
    if not out.get("warehouse"):
        out["warehouse"] = os.environ.get("SNOWFLAKE_WAREHOUSE", "").strip() or os.environ.get("WAREHOUSE", "").strip() or None
    return {k: v for k, v in out.items() if v is not None}


class _SnowflakeConnectionWrapper:
    """Wraps Snowflake connection so .execute(sql, params) returns a cursor-like with .fetchall(). Uses %s placeholders."""

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, sql: str, params=None):
        """Execute SQL; convert ? placeholders to %s for Snowflake connector (pyformat). Return cursor for fetchall()."""
        if params is not None:
            sql = sql.replace("?", "%s")
        cur = self._conn.cursor()
        if params is not None:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur


def _connect(connection_string: str):
    if snowflake is None:
        raise ImportError(
            "Snowflake connector is not installed. Install with: pip install aird-agent[snowflake]"
        )
    kwargs = _parse_connection_string(connection_string)
    if not kwargs.get("account") or not kwargs.get("user"):
        raise ValueError(
            "Snowflake connection requires account and user (set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER and SNOWFLAKE_PASSWORD, or use snowflake://user:password@account/...)"
        )
    if not kwargs.get("password"):
        raise ValueError("Snowflake connection requires password (SNOWFLAKE_PASSWORD or SNOWSQL_PWD)")
    raw = snowflake.connector.connect(**kwargs)
    return _SnowflakeConnectionWrapper(raw)


def _register() -> None:
    register_platform("snowflake", "snowflake", _connect, "common_snowflake")


_register()
