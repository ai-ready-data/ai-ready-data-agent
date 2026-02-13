# Connections Manifest (Removed)

> **Status:** The connections manifest (`~/.aird/connections.yaml`) is **no longer used** by the AIRD CLI. It has no effect on any command. This document is kept for historical reference only.

## Why it was removed

The manifest was designed for **estate assessment** — a mode where `aird assess` (with no `-c` flag) would read a YAML file listing multiple connections and produce a single merged report across all of them.

This feature was removed in the Phase 1 refactor in favour of a simpler model:

- **One connection per assessment** — each `aird assess` targets exactly one database.
- **Explicit comparison** — `aird benchmark` compares multiple databases side-by-side by running independent assessments, rather than merging them into one report.

## What to use instead

| Goal | Command |
|------|---------|
| Assess a single database | `aird assess -c "<connection_string>"` |
| First-time interactive setup | `aird init` |
| Compare multiple databases | `aird benchmark -c conn1 -c conn2` |
| Set a default connection | `export AIRD_CONNECTION_STRING="<connection_string>"` |

See [platforms.md](platforms.md) for connection string formats by database platform.

## If you have an existing manifest file

It is safe to delete `~/.aird/connections.yaml` — the CLI never reads it. You may also keep it as personal documentation of your data estate; it simply has no effect on any `aird` command.

## Future

If a future version re-introduces multi-connection support, this spec may be revived and updated.
