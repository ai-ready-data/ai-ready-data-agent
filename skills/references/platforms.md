# Platform Connection Reference

Shared reference for supported database platforms. Used by [connect/SKILL.md](../connect/SKILL.md) when constructing connection strings. **CLI:** Invoke as `aird` or `python -m agent.cli`; if `aird` is not on PATH, use `python -m agent.cli`.

## Built-in Platforms

The agent ships with built-in support for **DuckDB**. Snowflake is available as an optional extra.

---

## DuckDB

**Connection format:**
```
duckdb://path/to/file.duckdb
duckdb://:memory:
```

**Parameters:**
| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| path | Yes | :memory: | Path to .duckdb file, or :memory: |

**Driver:** Included with the package (`pip install -e .`). No extra install.

**Read-only enforcement:** Application-level SQL validation (only SELECT, DESCRIBE, SHOW, EXPLAIN, WITH).

**Suite:** `common` (Clean factor: null_rate, duplicate_rate, table_discovery; ANSI SQL + information_schema).

**Example:**
```
duckdb:///Users/me/data/sample.duckdb
duckdb://:memory:
```

---

## Snowflake (optional)

**Connection format:**
```
snowflake://user:password@account/database/schema?warehouse=WH&role=ROLE
```

**Driver:** `pip install -e ".[snowflake]"` or `pip install snowflake-connector-python`

**Suite:** When implemented, platform-native suite in addition to common.

**Example:**
```
snowflake://jdoe:password@xy12345.us-east-1/ANALYTICS/PUBLIC?warehouse=COMPUTE_WH
```

---

## Environment Variables

The CLI respects these (see [docs/specs/cli-spec.md](../../docs/specs/cli-spec.md)):

| Variable | Purpose |
|----------|---------|
| `AIRD_CONNECTION_STRING` | Connection string (fallback when `--connection` not passed) |
| `AIRD_CONTEXT` | Path to context YAML file |
| `AIRD_THRESHOLDS` | Path to thresholds JSON |
| `AIRD_OUTPUT` | Default output (e.g. markdown, stdout, json:path) |
| `AIRD_DB_PATH` | SQLite path for history (default `~/.aird/assessments.db`) |
| `AIRD_LOG_LEVEL` | Log level (debug, info, warn, error) |
| `AIRD_AUDIT` | Set to 1 to enable audit log (queries + conversation in same DB) |

Never log or store connection strings with credentials in plain text.
