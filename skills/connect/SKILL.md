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
2. Snowflake (optional extra)
3. Other (see [CONTRIBUTING.md](../../CONTRIBUTING.md) for adding platforms)

If the user provides a connection string directly, skip to Step 3.

**STOP:** Wait for user response.

### Step 2: Construct Connection String

**Load** [references/platforms.md](../references/platforms.md) for the chosen platform's connection format and driver install.

- **DuckDB:** `duckdb:///path/to/file.duckdb` or `duckdb://:memory:`. Driver is included.
- **Snowflake:** `snowflake://user:pass@account/db/schema?warehouse=WH`. Driver: `pip install -e ".[snowflake]"`.

Help the user build the string or set `AIRD_CONNECTION_STRING` in the environment.

**STOP:** Confirm the connection string (or env) is set; do not log the full string with secrets.

### Step 3: Verify Tool and Driver

Ensure the CLI runs:

```bash
aird suites
```

If `aird` is not on PATH, use `python -m agent.cli` instead. If the driver is missing (e.g. Snowflake not installed), tell the user the exact install command from [references/platforms.md](../references/platforms.md).

**STOP:** Confirm connection can be used (user can run `aird discover -c "<connection>"` in the next skill).

## Output

- User has a connection string (or `AIRD_CONNECTION_STRING` set)
- Correct driver installed
- Ready to proceed to [discover/SKILL.md](../discover/SKILL.md)
