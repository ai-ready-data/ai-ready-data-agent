# Connections manifest spec

The **connections manifest** is the optional source of truth for what the assessment agent runs against. It is a **YAML or JSON** file with a list of entries; each entry is a connection and optional **targets** (databases, schemas, tables) so that, per platform, you can restrict which objects are assessed.

## Goals

- **Arbitrary nesting under platforms:** For each connection, optional scope can restrict which databases, schemas, or tables are in scope. Structure is platform-aware (e.g. Snowflake: database → schema → table; DuckDB: schema → table).
- **Single source of truth:** One file describes the full estate and exactly which objects are assessed.

## Format

- **File:** Must have extension `.yaml`, `.yml`, or `.json`. Path via `--connections-file` or `AIRD_CONNECTIONS_FILE`. Default: `~/.aird/connections.yaml`.
- **Root shape:** A list of entries, or an object with key `entries`, `targets`, or `connections` (value is the list).

**Entry shape:** Each entry is either:

1. **String** — A single connection string (or `env:VAR_NAME`). No scope; assess all.
2. **Object** with:
   - `connection` (required): connection string or `env:VAR_NAME`.
   - `targets` (optional): scope for this connection. Arbitrary nesting is allowed under `targets` so that platform-specific hierarchy is representable.

**Recommended `targets` shape (generic):**

- **databases** (optional): list of database names. For platforms that expose multiple databases (e.g. Snowflake, BigQuery), restrict discovery to these. If absent, platform default or all accessible databases.
- **schemas** (optional): list of schema names. Restrict discovery to these schemas. If absent, all schemas (in the selected databases, if any).
- **tables** (optional): list of fully qualified table names (e.g. `schema.table` or `database.schema.table`). If present, only these tables are in scope; `schemas` may be ignored or used as a filter.

Nesting under `targets` can be extended per platform (e.g. `catalogs`, `projects`). The assessment agent uses whatever keys the discovery layer understands; unknown keys are ignored.

**Example (flat targets):** Use quoted strings for connection values that contain `:` (e.g. `scheme://host`) so YAML does not treat them as key-value.

```yaml
entries:
  - connection: "duckdb:///prod.duckdb"
    targets:
      schemas: [main, staging]
      tables: [main.fact_sales, staging.raw_events]

  - connection: env:SNOWFLAKE_URI
    targets:
      databases: [ANALYTICS, RAW]
      schemas: [PUBLIC, STAGING]

  - env:SQLITE_URI
```

**Example (nested targets for multiple databases):**

```yaml
entries:
  - connection: env:SNOWFLAKE_URI
    targets:
      - database: ANALYTICS
        schemas: [PUBLIC, STAGING]
      - database: RAW
        tables: [RAW.PUBLIC.events]
```

When `targets` is a list of objects (as in the second example), each object describes one scope slice; the connection is assessed once per slice (or the loader may flatten to one target per slice with the same connection and derived schemas/tables — implementation choice). This spec allows both: **flat** `targets` (single scope per connection) or **nested list** (multiple scope slices per connection).

## Resolved assessment targets

The CLI **resolves** the manifest into a list of **assessment targets**. Each target has:

- **connection** (string): The connection string (after expanding `env:VAR_NAME`).
- **schemas** (optional list): Passed to `discover(connection, schemas=..., tables=...)`.
- **tables** (optional list): Passed to `discover(connection, schemas=..., tables=...)`.
- **databases** (optional list): Platform-dependent; if the platform adapter supports it, discovery may restrict to these databases. Otherwise the connection string or discovery implementation may encode the database.

So "arbitrary nesting" in the manifest is **normalized** by the loader into a flat list of targets, each with `connection` and zero or more of `schemas`, `tables`, `databases`. The pipeline then runs one discover + run per target.

**CLI flags:** `--schema` and `--tables` apply globally when a target has no scope. When a target has its own `schemas`/`tables` from the manifest, per-target scope takes precedence.

## Security

Unchanged from existing manifest: prefer `env:VAR_NAME` for secrets; do not store credentials in the file. The agent must not log or echo connection strings with credentials.
