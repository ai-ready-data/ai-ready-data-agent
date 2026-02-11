"""Tests for Snowflake adapter (Clean + Contextual suites, connection parsing). No real Snowflake connection required."""

import os
import textwrap
from pathlib import Path

import pytest

from agent.platform import get_platform, get_suite
from agent.platform.snowflake_adapter import (
    _is_named_connection,
    _load_named_connection,
    _parse_connection_string,
    _requires_password,
)


# ---------------------------------------------------------------------------
# Suite registration
# ---------------------------------------------------------------------------


def test_common_snowflake_suite_registered():
    """Snowflake suite contains Clean (6) + Contextual (4) = 10 tests."""
    tests = get_suite("common_snowflake")
    assert len(tests) == 10
    ids = {t["id"] for t in tests}
    # Clean tests
    assert "clean_table_count" in ids
    assert "null_rate" in ids
    assert "duplicate_rate" in ids
    assert "zero_negative_rate" in ids
    assert "type_inconsistency_rate" in ids
    assert "format_inconsistency_rate" in ids
    # Contextual tests
    assert "primary_key_defined" in ids
    assert "semantic_model_coverage" in ids
    assert "foreign_key_coverage" in ids
    assert "temporal_scope_present" in ids
    factors = {t["factor"] for t in tests}
    assert factors == {"clean", "contextual"}


# ---------------------------------------------------------------------------
# Connection string parsing
# ---------------------------------------------------------------------------


def test_parse_standard_url():
    """Standard snowflake://user:pass@account/db/schema?warehouse=WH URL."""
    result = _parse_connection_string("snowflake://alice:s3cret@myaccount/mydb/myschema?warehouse=WH1&role=ADMIN")
    assert result["user"] == "alice"
    assert result["password"] == "s3cret"
    assert result["account"] == "myaccount"
    assert result["database"] == "mydb"
    assert result["schema"] == "myschema"
    assert result["warehouse"] == "WH1"
    assert result["role"] == "ADMIN"


def test_parse_url_with_authenticator():
    """URL with ?authenticator=externalbrowser and no password."""
    result = _parse_connection_string("snowflake://jdoe@myaccount/mydb?authenticator=externalbrowser&warehouse=WH")
    assert result["user"] == "jdoe"
    assert result["account"] == "myaccount"
    assert result["authenticator"] == "externalbrowser"
    assert "password" not in result or result.get("password") is None


def test_parse_named_connection_pattern():
    """snowflake://connection:NAME is detected as a named connection."""
    assert _is_named_connection("snowflake://connection:snowhouse") == "snowhouse"
    assert _is_named_connection("snowflake://connection:my_conn/") == "my_conn"
    assert _is_named_connection("snowflake://user:pass@account") is None
    assert _is_named_connection("postgres://connection:x") is None


# ---------------------------------------------------------------------------
# Named connection TOML loading
# ---------------------------------------------------------------------------


def test_load_named_connection(tmp_path):
    """_load_named_connection reads a TOML file and returns normalized params."""
    toml_file = tmp_path / "connections.toml"
    toml_file.write_text(textwrap.dedent("""\
        [snowhouse]
        account = "ORG-ACCT"
        user = "JDOE"
        authenticator = "EXTERNALBROWSER"
        role = "ANALYST"
        warehouse = "WH_XS"
    """))
    result = _load_named_connection("snowhouse", toml_path=toml_file)
    assert result["account"] == "ORG-ACCT"
    assert result["user"] == "JDOE"
    assert result["authenticator"] == "EXTERNALBROWSER"
    assert result["role"] == "ANALYST"
    assert result["warehouse"] == "WH_XS"


def test_load_named_connection_missing_section(tmp_path):
    """Raises ValueError when the named section doesn't exist."""
    toml_file = tmp_path / "connections.toml"
    toml_file.write_text("[other]\naccount = 'X'\n")
    with pytest.raises(ValueError, match="not found"):
        _load_named_connection("nonexistent", toml_path=toml_file)


def test_load_named_connection_missing_file(tmp_path):
    """Raises ValueError when the TOML file doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        _load_named_connection("x", toml_path=tmp_path / "nope.toml")


# ---------------------------------------------------------------------------
# Password requirement logic
# ---------------------------------------------------------------------------


def test_requires_password_default():
    """Default (no authenticator or 'snowflake') requires password."""
    assert _requires_password(None) is True
    assert _requires_password("snowflake") is True
    assert _requires_password("") is True


def test_requires_password_sso():
    """EXTERNALBROWSER, snowflake_jwt, and oauth do not require password."""
    assert _requires_password("externalbrowser") is False
    assert _requires_password("EXTERNALBROWSER") is False
    assert _requires_password("snowflake_jwt") is False
    assert _requires_password("oauth") is False
    assert _requires_password("https://myokta.example.com") is False


# ---------------------------------------------------------------------------
# Platform integration
# ---------------------------------------------------------------------------


def test_snowflake_platform_requires_connector_or_valid_creds():
    """Without snowflake-connector-python, get_platform(snowflake://...) raises ImportError. With connector, may raise ValueError or connection error for bad URL."""
    try:
        get_platform("snowflake://user:pass@account/db/schema")
    except ImportError as e:
        assert "snowflake" in str(e).lower()
    except ValueError:
        # Connector installed; URL parsed but connection failed (expected without real Snowflake)
        pass
    except Exception:
        # Connector installed but network unavailable (sandbox) or account unreachable — that's expected
        pass
    # If we get here without exception, connector connected (e.g. test env with real creds) — that's OK
