# Platform Connection Reference

Shared reference for supported database platforms. Used by [connect.md](../connect.md) when constructing connection strings. **CLI:** Invoke as `aird` or `python -m agent.cli`; if `aird` is not on PATH, use `python -m agent.cli`.

## Built-in Platforms

The agent ships with built-in support for **DuckDB** and **SQLite**. Snowflake is available as an optional extra.

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

## SQLite

**Connection format:**
```
sqlite:///path/to/file.db
sqlite:///:memory:
```

**Parameters:**
| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| path | Yes | :memory: | Path to .db/.sqlite file, or :memory: |

**Driver:** Python standard library (`sqlite3`). No extra install.

**Read-only enforcement:** Application-level SQL validation (only SELECT, DESCRIBE, SHOW, EXPLAIN, WITH). Discovery uses `sqlite_master` and `PRAGMA table_info` (metadata only).

**Suite:** `common_sqlite` (Clean factor: null_rate, duplicate_rate, table_discovery; SQLite-compatible SQL).

**Example:**
```
sqlite:///./sample.sqlite
sqlite:///:memory:
```

---

## Snowflake (optional)

**Driver:** `pip install -e ".[snowflake]"` or `pip install snowflake-connector-python`

**Suite:** `common_snowflake` (Clean + Contextual factors; Snowflake-native SQL using `information_schema`).

### Connection modes

Snowflake supports three connection modes. Choose the one that fits your environment.

#### 1. Named connection (Cortex Code CLI / Snowflake CLI)

If you already have a `~/.snowflake/connections.toml` file (created by Cortex Code CLI, Snowflake CLI, or manually), reference a named section:

```
snowflake://connection:NAME
```

The adapter reads the `[NAME]` section from `~/.snowflake/connections.toml` and passes all fields to the Snowflake connector. This is the easiest option when using Cortex Code CLI because it reuses the same SSO session.

**Example `~/.snowflake/connections.toml`:**
```toml
[snowhouse]
account = "MYORG-MYACCOUNT"
user = "JDOE"
authenticator = "EXTERNALBROWSER"
role = "ANALYST"
warehouse = "WH_XS"
database = "ANALYTICS"
schema = "PUBLIC"
```

**Connection string:**
```
snowflake://connection:snowhouse
```

> **Tip:** Use `env:SNOWFLAKE_CONNECTION_NAME` in the connections manifest to avoid hardcoding the name.

#### 2. URL with password

The traditional URL format with embedded credentials:

```
snowflake://user:password@account/database/schema?warehouse=WH&role=ROLE
```

**Example:**
```
snowflake://jdoe:s3cret@xy12345.us-east-1/ANALYTICS/PUBLIC?warehouse=COMPUTE_WH
```

#### 3. URL with SSO (EXTERNALBROWSER)

Use when you want browser-based SSO without a password:

```
snowflake://user@account/database/schema?authenticator=externalbrowser&warehouse=WH
```

This opens a browser window for SSO on first connection. No password is needed.

**Example:**
```
snowflake://jdoe@myorg-myaccount/ANALYTICS/PUBLIC?authenticator=externalbrowser&warehouse=COMPUTE_WH
```

### Connection parameters

| Parameter | Required | Source | Notes |
|-----------|----------|--------|-------|
| account | Yes | URL hostname, TOML, or `SNOWFLAKE_ACCOUNT` | Org-account format (e.g. `MYORG-MYACCOUNT`) |
| user | Yes | URL username, TOML, or `SNOWFLAKE_USER` | |
| password | Conditional | URL password, TOML, or `SNOWFLAKE_PASSWORD` / `SNOWSQL_PWD` | Required only when authenticator is `snowflake` (default) or not set |
| authenticator | No | URL query param, TOML, or `SNOWFLAKE_AUTHENTICATOR` | `externalbrowser`, `snowflake_jwt`, `oauth`, or OKTA URL. Omit for password auth |
| database | No | URL path, TOML, or `SNOWFLAKE_DATABASE` | |
| schema | No | URL path, TOML, or `SNOWFLAKE_SCHEMA` | |
| warehouse | No | URL query param, TOML, or `SNOWFLAKE_WAREHOUSE` | |
| role | No | URL query param, TOML, or env | |

### `connections.toml` file format

The file uses TOML with one section per named connection:

```toml
[connection_name]
account = "ORG-ACCOUNT"
user = "USERNAME"
authenticator = "EXTERNALBROWSER"   # or omit for password auth
password = "..."                     # only if using password auth
role = "ROLE_NAME"
warehouse = "WAREHOUSE_NAME"
database = "DATABASE_NAME"
schema = "SCHEMA_NAME"
```

**Default location:** `~/.snowflake/connections.toml` (shared with Snowflake CLI and Cortex Code CLI).

### Connection resolution order

```
snowflake://connection:NAME     → read ~/.snowflake/connections.toml [NAME]
snowflake://user:pass@account   → existing URL parsing
snowflake://user@account?authenticator=externalbrowser → URL without password + authenticator
env vars (SNOWFLAKE_ACCOUNT, etc.) → fallback for any missing fields
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

### Snowflake-specific environment variables

| Variable | Purpose |
|----------|---------|
| `SNOWFLAKE_ACCOUNT` | Account identifier (fallback) |
| `SNOWFLAKE_USER` | Username (fallback) |
| `SNOWFLAKE_PASSWORD` | Password (fallback) |
| `SNOWSQL_PWD` | Password (alternative fallback) |
| `SNOWFLAKE_AUTHENTICATOR` | Authenticator method (fallback; e.g. `externalbrowser`) |
| `SNOWFLAKE_DATABASE` | Database name (fallback) |
| `SNOWFLAKE_SCHEMA` | Schema name (fallback) |
| `SNOWFLAKE_WAREHOUSE` | Warehouse name (fallback) |

Never log or store connection strings with credentials in plain text.
