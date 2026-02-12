---
name: connect
description: "Establish a read-only database connection for assessment. Handles connection string parsing, driver installation, and platform detection."
parent_skill: assess-data
---

# Connect to Database

Establish that the user has a read-only way to connect to their database: connection string or environment variable, and the correct driver installed.

## Forbidden Actions

- NEVER store credentials in plain text outside of environment variables or the connection string
- NEVER log the full connection string with credentials visible
- NEVER attempt to write data to the database — connections are read-only
- NEVER install drivers without confirming with the user first

## When to Load

- User wants to assess a database but hasn't connected yet
- User provides a connection string or database credentials
- User asks which platforms are supported

## Prerequisites

- Python 3.9+ installed
- Agent package installed: `pip install -e .` (from repo root)

## Workflow

### Step 1: Determine Platform

**Ask user:**

Which database platform are you using?

1. DuckDB (file or in-memory)
2. SQLite (file or in-memory)
3. Snowflake (optional extra)
4. Other (see [CONTRIBUTING.md](../../CONTRIBUTING.md) for adding platforms)

If the user already gave a connection string, skip to Step 3.

**Alternative:** For first-time users, `aird init` provides an interactive wizard that guides through platform selection, connection string construction, and verification in one step.

**STOP:** Wait for user response.

### Step 2: Construct Connection String

**Load** [references/platforms.md](../references/platforms.md) for the chosen platform's connection format and driver install.

- **DuckDB:** `duckdb:///path/to/file.duckdb` or `duckdb://:memory:`. Driver is included.
- **SQLite:** `sqlite:///path/to/file.db`. Driver is in the standard library.
- **Snowflake** (three options — pick the one that fits):
  1. **Named connection (Cortex Code CLI / Snowflake CLI):** If the user already has `~/.snowflake/connections.toml` (from Cortex Code CLI or Snowflake CLI), use `snowflake://connection:NAME` where NAME is the TOML section (e.g. `snowflake://connection:snowhouse`). No password needed — reuses the existing SSO session. This is the recommended option for Cortex Code CLI users.
  2. **URL with SSO:** `snowflake://user@account/db/schema?authenticator=externalbrowser&warehouse=WH`. Opens browser for SSO, no password stored.
  3. **URL with password:** `snowflake://user:pass@account/db/schema?warehouse=WH`. Driver: `pip install -e ".[snowflake]"`.

Help the user build the string or set an env var. **For secrets, prefer an env var** (e.g. `export SNOWFLAKE_URI='snowflake://...'`) so credentials aren't in shell history. For named connections, no secrets are needed in the connection string since `connections.toml` handles auth.

**STOP:** Confirm the connection string (or env) is set; do not log the full string with secrets.

### Step 3: Verify Tool and Driver

Ensure the CLI runs:

```bash
aird suites
```

If `aird` is not on PATH, use `python -m agent.cli` instead. If the driver is missing (e.g. Snowflake not installed), tell the user the exact install command from [references/platforms.md](../references/platforms.md).

**STOP:** Confirm connection can be used (user can run `aird discover -c "<connection>"` in the next skill). Note that `aird init` can also verify the connection interactively.

## Output

- User has a connection string (or env var set)
- Correct driver installed
- Connection string ready for use with `aird assess -c` or `aird benchmark -c`
- Ready to proceed to [discover/SKILL.md](../discover/SKILL.md)
