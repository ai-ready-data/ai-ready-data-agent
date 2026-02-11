---
name: add-platform
description: Add a new data platform (e.g. BigQuery, Snowflake, MongoDB, AWS Redshift) to the ai-ready-agent: adapter, Clean test suite, discovery path, and coverage doc. Use when the user wants to onboard a platform, add support for a database/technology, or create a new platform with all requirements and tests.
---

# Add a new platform to ai-ready-agent

Use this skill when asked to add support for a platform (e.g. "add BigQuery", "create platform for MongoDB", "onboard AWS Redshift"). The outcome is a working platform: connection, discovery, Clean suite with all requirement keys, and docs.

## When to use

- User names a platform (BigQuery, Snowflake, Postgres, MongoDB, Redshift, etc.) and wants it integrated.
- User asks to "create a platform with all requirements and tests" or "accelerate onboarding" a technology.

## Workflow

1. **Reason about the platform**
   - **Connection**: URL scheme (e.g. `bigquery://`, `snowflake://`). How does the driver connect? (connection string, env vars, credentials.)
   - **SQL dialect**: Does it support `information_schema`? Placeholders `{schema_q}`, `{table_q}`, `column_q}` receive **already-quoted** identifiers from [agent/run.py](../../agent/run.py) (double-quote style; escape `"` as `""`). Adapt SQL to dialect (e.g. BigQuery uses backticks; Snowflake uses double quotes; convert or keep placeholders and document).
   - **Dialect quirks**: Null counting (FILTER/WHERE vs CASE/SUM), duplicate rate (DISTINCT * or list columns), TRY_CAST / SAFE_CAST / equivalent for type and format checks, date parsing (e.g. `date()` in SQLite vs `CAST(... AS DATE)` in DuckDB).
   - **Discovery**: If the platform has `information_schema.tables` and `information_schema.columns` (with `table_schema`, `table_name`, `column_name`, `data_type`), reuse the existing discovery path in [agent/discovery.py](../../agent/discovery.py). Otherwise add a `_discover_<platform>(conn)` and branch in `discover()` by platform name.
   - **Non-SQL (e.g. MongoDB)**: Discovery must produce the same inventory shape (schemas, tables, columns with data_type). Tests may need non-SQL execution (executor or suite contract extension). Prefer implementing SQL-like platforms first.

2. **Implement in order**
   - **Adapter**: [agent/platform/](../../agent/platform/) — new file `{platform}_adapter.py`. Parse connection string, create connection (PEP 249-style: `.execute(sql, params)`, `.fetchall()`). Call `register_platform(scheme, adapter_name, create_connection_func, default_suite)`.
   - **Suite**: [agent/suites/](../../agent/suites/) — new file `clean_{platform}.py`. Define one test per Clean requirement key (see [reference.md](reference.md)). Use `query` for fixed platform-level tests (e.g. table count); use `query_template` with `{schema_q}`, `{table_q}`, `{column_q}` for table/column tests. Call `register_suite(suite_name, list_of_test_defs)`.
   - **Discovery** (if not information_schema): In [agent/discovery.py](../../agent/discovery.py), add `_discover_<name>(conn)` returning `{ "schemas", "tables", "columns" }`; in `discover()`, branch on `name` (from `get_platform`) to call it.
   - **Registration**: In [agent/platform/__init__.py](../../agent/platform/__init__.py), add:
     - `import agent.platform.<platform>_adapter  # noqa: F401`
     - `import agent.suites.clean_<platform>  # noqa: F401`
   - **Coverage**: In [docs/coverage/README.md](../../docs/coverage/README.md), add a subsection for the new platform under Factor 0: Clean (or a new "Platform: X" table) with | Key | Implemented | Scope/notes |.

3. **Clean requirement keys (all must be implemented)**

   | Key | target_type | What the query returns |
   |-----|-------------|------------------------|
   | `table_discovery` | platform | Single value: count of user tables (informational). |
   | `null_rate` | column | Single value `v`: fraction of rows where column is NULL (0–1). |
   | `duplicate_rate` | table | Single value `v`: 1 - (distinct rows / total rows) (0–1). |
   | `zero_negative_rate` | column | Single value `v`: fraction of rows where column ≤ 0 (0–1). |
   | `type_inconsistency_rate` | column | Single value `v`: fraction of non-null values that fail cast to numeric (0–1). |
   | `format_inconsistency_rate` | column | Single value `v`: fraction of non-null values that don't parse as date (0–1). |

   Scoping (which columns get column tests) is in [agent/run.py](../../agent/run.py) `_column_matches_requirement`; thresholds are in [agent/thresholds.py](../../agent/thresholds.py). New platforms do not change those.

4. **Verify**
   - Run [scripts/verify_setup.py](../../scripts/verify_setup.py) if a local DB can be used; or document "run assess with connection string `scheme://...`" for the new platform.
   - Ensure all six Clean keys are present in the suite and coverage doc.

## Reference

- **Test def shape, discovery contract, executor contract**: [reference.md](reference.md)
- **Existing implementations**: [agent/suites/clean_duckdb.py](../../agent/suites/clean_duckdb.py), [agent/suites/clean_sqlite.py](../../agent/suites/clean_sqlite.py), [agent/platform/duckdb_adapter.py](../../agent/platform/duckdb_adapter.py), [agent/platform/sqlite_adapter.py](../../agent/platform/sqlite_adapter.py).
