"""Platform and suite registry. Adapters register by connection scheme or name."""

from typing import Any, Callable, Optional

# scheme -> (adapter_name, create_connection_func, default_suite_name)
_platforms: dict[str, tuple[str, Callable[[str], Any], str]] = {}
# suite_name -> list of test definitions
_suites: dict[str, list[dict]] = {}


def register_platform(
    scheme: str,
    adapter_name: str,
    create_connection_func: Callable[[str], Any],
    default_suite: str = "common",
) -> None:
    """Register a platform for a connection scheme (e.g. duckdb, snowflake)."""
    _platforms[scheme.lower()] = (adapter_name, create_connection_func, default_suite)


def _scheme_and_suite(connection_string: str) -> tuple[str, str]:
    """Parse connection string to (scheme, default_suite). Does not create a connection."""
    scheme = connection_string.split("://", 1)[0].lower() if "://" in connection_string else "duckdb"
    if scheme not in _platforms:
        raise ValueError(f"Unknown connection scheme: {scheme}. Supported: {list(_platforms.keys())}")
    _, _, default_suite = _platforms[scheme]
    return scheme, default_suite


def get_default_suite(connection_string: str) -> str:
    """Return the default suite name for the connection's scheme. Does not open a connection."""
    _, default_suite = _scheme_and_suite(connection_string)
    return default_suite


def get_platform(connection_string: str) -> tuple[str, Any, str]:
    """Resolve connection string to (adapter_name, connection_handle, default_suite). Raises if unknown scheme."""
    scheme, default_suite = _scheme_and_suite(connection_string)
    name, factory, _ = _platforms[scheme]
    conn = factory(connection_string)
    return name, conn, default_suite


def register_suite(name: str, tests: list[dict]) -> None:
    """Register (or extend) a test suite. Multiple factor files can contribute tests to the same suite name."""
    if name in _suites:
        _suites[name].extend(tests)
    else:
        _suites[name] = list(tests)


def get_suite(name: str) -> list[dict]:
    """Return test list for suite. 'auto' is not resolved here; caller passes resolved suite name."""
    if name not in _suites:
        return []
    return list(_suites[name])
