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

**STOP:** Wait for user response.

### Step 2: Construct Connection String

**Load** [references/platforms.md](../references/platforms.md) for the chosen platform's connection format and driver install.

- **DuckDB:** `duckdb:///path/to/file.duckdb` or `duckdb://:memory:`. Driver is included.
- **SQLite:** `sqlite:///path/to/file.db`. Driver is in the standard library.
- **Snowflake:** `snowflake://user:pass@account/db/schema?warehouse=WH`. Driver: `pip install -e ".[snowflake]"`.

Help the user build the string or set an env var. **For secrets, prefer an env var** (e.g. `SNOWFLAKE_URI`) so we can put `env:SNOWFLAKE_URI` in the manifest and keep the file safe.

**STOP:** Confirm the connection string (or env) is set; do not log the full string with secrets.

### Step 3: Verify Tool and Driver

Ensure the CLI runs:

```bash
aird suites
```

If `aird` is not on PATH, use `python -m agent.cli` instead. If the driver is missing (e.g. Snowflake not installed), tell the user the exact install command from [references/platforms.md](../references/platforms.md).

**STOP:** Confirm connection can be used (user can run `aird discover -c "<connection>"` in the next skill).

### Step 4: Add to Connections Manifest (optional but recommended for estate)

**Load** [references/connections-manifest.md](../references/connections-manifest.md).

Add this connection to the user's **connections manifest** (source of truth for their platforms):

- **Manifest path:** `~/.aird/connections.yaml` unless the user has set `AIRD_CONNECTIONS_FILE`. Create the file (YAML with `entries` list) and `~/.aird/` if they don't exist; otherwise **append** to the entries list (never overwrite without explicit request).
- **Line to add:** The connection string (for file paths) or `env:VAR_NAME` if the user is using an env var for the connection. Prefer `env:VAR_NAME` for any connection that contains credentials.
- Confirm: "I've added this to your connections manifest at … . You can run `aird assess` with no `-c` to assess all connections in the manifest."

If the user has only one DB and prefers not to use a manifest, skip this step.

**STOP:** Confirm manifest updated (or user declined).

## Output

- User has a connection string (or env var set)
- Correct driver installed
- Connection added to the connections manifest (or user chose single-connection only)
- Ready to proceed to [discover/SKILL.md](../discover/SKILL.md)
