# Connections manifest

The **connections manifest** is the optional **source of truth** for which platforms (and which databases/schemas/tables within them) the assessment agent runs against. It is a **YAML or JSON** file. Each entry is a connection and optional **targets** (databases, schemas, tables). **The manifest is optional** — single-DB users can use `-c` or `AIRD_CONNECTION_STRING` and never touch the manifest.

Full spec: [docs/specs/manifest-spec.md](../../docs/specs/manifest-spec.md).

## Purpose

- **Single source of truth** for the user's data estate (platforms and, optionally, what to assess within each).
- **Estate assessment:** Run `aird assess` with no connection args to assess all entries in the manifest (when the default manifest exists or `AIRD_CONNECTIONS_FILE` is set).
- **Arbitrary nesting under platforms:** Each connection can have optional **targets** (databases, schemas, tables) so only those objects are in scope for discovery and tests.
- **Agent workflow:** Step 1 = ask what platforms → for each, get connection details and optional scope → add to manifest. Later: `aird assess` (no `-c`) uses the manifest.

## Format

The manifest file must use extension **.yaml**, **.yml**, or **.json**. Root is a list of entries or an object with key `entries`, `targets`, or `connections` (value = list). Each entry is either a connection string (or `env:VAR_NAME`) or an object with `connection` and optional `targets` (databases, schemas, tables). Quote connection strings that contain `:` in YAML (e.g. `"duckdb:///path/to/file.duckdb"`).

```yaml
entries:
  - connection: "duckdb:///path/to/prod.duckdb"
    targets:
      schemas: [main, staging]
      tables: [main.fact_sales, staging.raw_events]
  - connection: env:SNOWFLAKE_URI
    targets:
      databases: [ANALYTICS, RAW]
      schemas: [PUBLIC, STAGING]
  - env:SQLITE_URI
```

**Security:** Prefer **paths** for file-based DBs and **env:VAR_NAME** for any connection that contains credentials. Do not store credentials in the manifest unless the user explicitly accepts the risk. The agent must never log or echo the full manifest if it contains secrets.

## Location

| Source | Path |
|--------|------|
| **Default** | `~/.aird/connections.yaml` |
| **Override** | `AIRD_CONNECTIONS_FILE` (env) or `--connections-file` (CLI) |

When the user has not set `AIRD_CONNECTIONS_FILE` or passed `--connections-file`, the CLI uses the default path if that file exists (so "assess from manifest" = `aird assess` with no `-c` after the manifest is populated).

## How the agent uses it

1. **First step (interview/connect):** Ask "What platforms do you have access to?" (DuckDB, SQLite, Snowflake, …). For each platform the user names, get the connection string (or env var) and optional scope, then **add that entry to the manifest** (create the file if it doesn't exist, otherwise append). Confirm the path: "I've added this to your connections manifest at `~/.aird/connections.yaml` (or `AIRD_CONNECTIONS_FILE` if set)."
2. **Later:** When the user wants to assess their full estate, run `aird assess` with no `-c` (or `aird assess --connections-file ~/.aird/connections.yaml`). The CLI reads the manifest and assesses each target in one run.
3. **Adding more:** When the user adds a new platform in a later session, load the connect skill, get the connection (and optional targets), then append to the same manifest file.

## Creating or appending

- If the manifest file does not exist, create it (and create `~/.aird/` if needed). Use YAML or JSON with an `entries` list and the first entry.
- If it exists, append a new entry to the `entries` list (or equivalent). Never overwrite the whole file without explicit user request.
