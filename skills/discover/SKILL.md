---
name: discover
description: "Enumerate schemas, tables, and columns; present scope and confirm with user before running tests."
parent_skill: assess-data
---

# Discover and Confirm Scope

Run discovery to enumerate schemas, tables, and columns. Present the summary to the user and confirm scope (and optional exclusions) before running the assessment.

## Forbidden Actions

- NEVER run SQL that modifies the database
- NEVER skip scope confirmation when the user has not yet seen discovery output
- NEVER log the connection string

## When to Load

- After connect; before running the full assessment
- User wants to see what will be assessed (tables/columns) first

## Prerequisites

- Connection string or `AIRD_CONNECTION_STRING` available
- CLI installed: `pip install -e .`

## Workflow

### Step 1: Run Discovery

Use the connection string from the connect step, or ensure `AIRD_CONNECTION_STRING` is set so you can omit `-c`. Run the CLI to discover schemas, tables, and columns:

```bash
aird discover -c "<connection>" -o inventory.json
```

Or to stdout:

```bash
aird discover -c "<connection>"
```

Optional: `--schema <name>` (repeatable), `--tables <schema.table>` (repeatable), `--context <path>` to restrict or contextualize scope. Full command reference: [references/cli-commands.md](../references/cli-commands.md).

If the command fails, report the error to the user and do not proceed; suggest checking connection string, driver, or network.

**STOP:** Ensure discovery completed without error.

### Step 2: Present Summary

Summarize for the user:

- Number of schemas and tables
- List schemas with table counts (e.g. "main: 3 tables")
- Optionally list table names if the set is small

### Step 3: Confirm Scope (Phase 2 Interview)

**Load** [interview/SKILL.md](../interview/SKILL.md) (Phase 2: post-discovery)

Ask:

1. "Should I assess all of these tables, or exclude any schemas/tables?" (e.g. staging, scratch)
2. "Are there tables that are especially critical for your target workload?"

If the user wants to exclude schemas or tables, note them. They can be passed as `--schema` / `--tables` on the next step, or recorded in a context file and passed with `--context` (see [references/context-file.md](../references/context-file.md)).

**STOP:** Get explicit confirmation before running the assessment.

## Output

- Inventory (in memory or in `inventory.json`)
- User-confirmed scope (and any exclusions)
- Ready to proceed to [assess/SKILL.md](../assess/SKILL.md)
