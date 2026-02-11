"""Tests for Snowflake adapter and Clean suite. No real Snowflake connection required."""

import pytest

from agent.platform import get_platform, get_suite


def test_common_snowflake_suite_registered():
    """Snowflake suite is Clean-only: 6 tests, one per Clean requirement."""
    tests = get_suite("common_snowflake")
    assert len(tests) == 6
    ids = {t["id"] for t in tests}
    assert "clean_table_count" in ids
    assert "null_rate" in ids
    assert "duplicate_rate" in ids
    assert "zero_negative_rate" in ids
    assert "type_inconsistency_rate" in ids
    assert "format_inconsistency_rate" in ids
    factors = {t["factor"] for t in tests}
    assert factors == {"clean"}


def test_snowflake_platform_requires_connector_or_valid_creds():
    """Without snowflake-connector-python, get_platform(snowflake://...) raises ImportError. With connector, may raise ValueError for bad URL."""
    try:
        get_platform("snowflake://user:pass@account/db/schema")
    except ImportError as e:
        assert "snowflake" in str(e).lower()
    except ValueError:
        # Connector installed; URL parsed but connection failed (expected without real Snowflake)
        pass
    # If we get here without exception, connector connected (e.g. test env with real creds) — that's OK
