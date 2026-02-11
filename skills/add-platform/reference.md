# Platform / suite / discovery contract (reference)

## Test definition shape

Each test in a suite is a dict with:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique within suite (e.g. `null_rate`, `clean_table_count`). |
| `factor` | Yes | Factor name, e.g. `"clean"`. |
| `requirement` | Yes | Requirement key (e.g. `null_rate`, `table_discovery`). |
| `target_type` | Yes | One of `platform`, `table`, `column`. |
| `query` | Cond. | Fixed SQL for this test (use for platform-level tests). |
| `query_template` | Cond. | SQL with placeholders `{schema_q}`, `{table_q}`, `{column_q}`; expander fills quoted identifiers. Use for table/column tests. |

Exactly one of `query` or `query_template` must be set. The expander in `agent/run.py`:

- For `target_type == "platform"`: uses `query` as-is (no expansion).
- For `target_type == "table"`: iterates inventory tables, replaces `{schema_q}`, `{table_q}` (no column).
- For `target_type == "column"`: iterates inventory columns, keeps only those where `_column_matches_requirement(col, requirement)`; replaces `{schema_q}`, `{table_q}`, `{column_q}`.

Quoting: the expander uses double-quote identifier quoting (DuckDB/SQL standard); escape `"` as `""`. If the platform uses different quoting (e.g. BigQuery backticks), the **suite** may use a custom quote function and format templates manually, or the runner can be extended to pass platform-specific quoting later.

## Query result contract

Every executed query must return a **single row, single column** (or first row/first column is used). The value is interpreted as a float for threshold comparison (rates 0–1). For `table_discovery`, the value is informational only (no threshold).

## Discovery inventory shape

`discover(connection_string, ...)` must return:

```python
{
    "schemas": ["list", "of", "schema", "names"],
    "tables": [
        {"schema": "s", "table": "t", "full_name": "s.t"}
    ],
    "columns": [
        {"schema": "s", "table": "t", "column": "c", "data_type": "VARCHAR"}
    ]
}
```

- `data_type` is used by `_column_matches_requirement` (e.g. numeric types for `zero_negative_rate`/`type_inconsistency_rate`, string for `format_inconsistency_rate`).
- Column names are used for date-like heuristics (e.g. `date`, `time`, `created`, `updated`, `_at`).

## Executor contract

Connections must support:

- `connection.execute(sql)` or `connection.execute(sql, params)` (PEP 249-style).
- Return value has `.fetchall()` returning a list of rows (tuples or dict-like).

Only read-only SQL is allowed (SELECT, DESCRIBE, SHOW, EXPLAIN, WITH). Validated in `agent/platform/executor.py`.

## Platform registration

```python
# In agent/platform/<name>_adapter.py
from agent.platform.registry import register_platform

def _connect(connection_string: str):
    # ... parse and return connection
    return conn

def _register() -> None:
    register_platform(
        scheme="snowflake",           # URL scheme (e.g. snowflake://...)
        adapter_name="snowflake",     # Used in discovery branch, logs
        create_connection_func=_connect,
        default_suite="common_snowflake",  # Suite name for this platform
    )
_register()
```

## Suite registration

```python
# In agent/suites/clean_<name>.py
from agent.platform.registry import register_suite

SUITE = [
    {"id": "clean_table_count", "factor": "clean", "requirement": "table_discovery", "query": "SELECT ...", "target_type": "platform"},
    # ... one entry per requirement key
]

def _register() -> None:
    register_suite("common_snowflake", SUITE)
_register()
```

## Requirement keys (Factor 0: Clean)

All six must be implemented for a full Clean suite:

- `table_discovery` (platform)
- `null_rate` (column)
- `duplicate_rate` (table)
- `zero_negative_rate` (column)
- `type_inconsistency_rate` (column)
- `format_inconsistency_rate` (column)

Thresholds are global in `agent/thresholds.py`; no per-platform threshold file.
