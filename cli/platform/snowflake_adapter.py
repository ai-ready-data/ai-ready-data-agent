"""Snowflake platform via snowflake-connector-python.

Supports three connection modes:
1. Named connection:   snowflake://connection:NAME  — reads ~/.snowflake/connections.toml [NAME]
2. URL with password:  snowflake://user:pass@account/db/schema?warehouse=WH
3. URL with SSO:       snowflake://user@account/db/schema?authenticator=externalbrowser&warehouse=WH

When authenticator is set to a non-password method (externalbrowser, snowflake_jwt, oauth),
no password is required. Registers on import.
"""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from agent.platform.registry import register_platform

try:
    import snowflake.connector
except ImportError:
    snowflake = None  # type: ignore[assignment]

# Authenticators that do not require a password
_PASSWORDLESS_AUTHENTICATORS = frozenset({
    "externalbrowser",
    "snowflake_jwt",
    "oauth",
    "https://",  # prefix match handled separately for OKTA URLs
})

# Default location for Snowflake connections config (shared with Snowflake CLI and Cortex Code CLI)
_CONNECTIONS_TOML_PATH = Path.home() / ".snowflake" / "connections.toml"


def _load_named_connection(name: str, toml_path: Optional[Path] = None) -> dict:
    """Read a named connection from ~/.snowflake/connections.toml (or custom path).

    The TOML file has sections like:
        [snowhouse]
        account = "ORG-ACCOUNT"
        user = "JDOE"
        authenticator = "EXTERNALBROWSER"
        role = "ANALYST"

    Returns a dict of connection params suitable for snowflake.connector.connect().
    Raises ValueError if the file or section is not found.
    """
    p = toml_path or _CONNECTIONS_TOML_PATH
    if not p.exists():
        raise ValueError(
            f"Snowflake connections file not found: {p}. "
            "Create it or use a full connection string instead of snowflake://connection:{name}"
        )
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            raise ImportError(
                "Python 3.11+ (tomllib) or the tomli package is required to read connections.toml. "
                "Install with: pip install tomli"
            )
    with open(p, "rb") as f:
        data = tomllib.load(f)
    # Support both flat sections [name] and nested [connections.name]
    section = data.get(name) or data.get("connections", {}).get(name)
    if not section or not isinstance(section, dict):
        available = [k for k in data if isinstance(data[k], dict)]
        raise ValueError(
            f"Connection '{name}' not found in {p}. Available: {available}"
        )
    # Normalize keys to lowercase for snowflake.connector.connect()
    return {k.lower(): v for k, v in section.items()}


def _is_named_connection(connection_string: str) -> Optional[str]:
    """If connection_string is 'snowflake://connection:NAME', return NAME; else None."""
    if "://" not in connection_string:
        return None
    parsed = urlparse(connection_string)
    if parsed.scheme.lower() != "snowflake":
        return None
    # Detect snowflake://connection:NAME — urlparse puts "connection" in hostname, NAME in port or path
    # We check for the literal pattern after the scheme
    rest = connection_string.split("://", 1)[1]
    if rest.lower().startswith("connection:"):
        name = rest.split(":", 1)[1].strip().strip("/")
        return name if name else None
    return None


def _requires_password(authenticator: Optional[str]) -> bool:
    """Return True if the authenticator requires a password."""
    if not authenticator:
        return True
    auth_lower = authenticator.lower()
    if auth_lower in ("snowflake", ""):
        return True  # default password-based auth
    if auth_lower in _PASSWORDLESS_AUTHENTICATORS:
        return False
    # OKTA URLs (https://...) are passwordless
    if auth_lower.startswith("https://"):
        return False
    return False  # unknown authenticator — let the connector decide


def _parse_connection_string(connection_string: str) -> dict:
    """Parse snowflake:// URL, named connection, or env vars.

    Formats:
        snowflake://connection:NAME                              — named connection from connections.toml
        snowflake://user:password@account/database/schema?warehouse=wh  — full URL
        snowflake://user@account/db/schema?authenticator=externalbrowser — SSO (no password)
    """
    # Named connection: snowflake://connection:NAME
    named = _is_named_connection(connection_string)
    if named is not None:
        out = _load_named_connection(named)
        # Apply env var fallbacks for fields not in the TOML
        if not out.get("database"):
            out["database"] = os.environ.get("SNOWFLAKE_DATABASE", "").strip() or None
        if not out.get("schema"):
            out["schema"] = os.environ.get("SNOWFLAKE_SCHEMA", "").strip() or None
        if not out.get("warehouse"):
            out["warehouse"] = os.environ.get("SNOWFLAKE_WAREHOUSE", "").strip() or None
        return {k: v for k, v in out.items() if v is not None}

    out: dict = {}
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
        # query params: warehouse, role, authenticator, and others
        if parsed.query:
            qs = parse_qs(parsed.query, keep_blank_values=True)
            if "warehouse" in qs:
                out["warehouse"] = qs["warehouse"][0]
            if "role" in qs:
                out["role"] = qs["role"][0]
            if "authenticator" in qs:
                out["authenticator"] = qs["authenticator"][0]

    # Env fallback (for CI/notebooks/servers)
    if not out.get("account"):
        out["account"] = os.environ.get("SNOWFLAKE_ACCOUNT", "").strip() or None
    if not out.get("user"):
        out["user"] = os.environ.get("SNOWFLAKE_USER", "").strip() or None
    if not out.get("password"):
        out["password"] = os.environ.get("SNOWFLAKE_PASSWORD", "").strip() or os.environ.get("SNOWSQL_PWD", "").strip() or None
    if not out.get("authenticator"):
        out["authenticator"] = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "").strip() or None
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
            "Snowflake connection requires account and user. "
            "Use snowflake://connection:NAME (from ~/.snowflake/connections.toml), "
            "snowflake://user:pass@account/..., or set SNOWFLAKE_ACCOUNT + SNOWFLAKE_USER."
        )
    if not kwargs.get("password") and _requires_password(kwargs.get("authenticator")):
        raise ValueError(
            "Snowflake connection requires a password or a non-password authenticator. "
            "Options: (1) snowflake://connection:NAME to use ~/.snowflake/connections.toml, "
            "(2) add ?authenticator=externalbrowser to the URL for SSO, "
            "(3) set SNOWFLAKE_PASSWORD or SNOWFLAKE_AUTHENTICATOR."
        )
    raw = snowflake.connector.connect(**kwargs)
    return _SnowflakeConnectionWrapper(raw)


def _register() -> None:
    register_platform("snowflake", "snowflake", _connect, "common_snowflake")


_register()
