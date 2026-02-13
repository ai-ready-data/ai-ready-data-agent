---
name: remediate
description: "Generate fix suggestions for failures the user wants to address. Use factor docs and remediation templates; never execute."
parent_skill: assess-data
---

# Suggest Fixes (Remediation)

For each failure the user decided to fix (from interpret/triage), generate concrete, actionable suggestions. Use the factor docs and any remediation templates. **You never execute remediation** — only suggest. The user reviews and runs changes.

## Forbidden Actions

- NEVER execute SQL or commands that modify the user's database
- NEVER run remediation scripts on behalf of the user
- NEVER store credentials in suggested scripts or logs
- NEVER suggest fixes for failures the user said to accept or exclude

## When to Load

- After interpret; user has triaged and asked for fix suggestions for specific failures
- User says "suggest fixes", "how do I fix X?", "remediation for these failures"

## Prerequisites

- Report (or results) with failing tests
- User has indicated which failures to address
- Factor docs in [../factors/](../factors/) (e.g. [0-clean.md](../factors/0-clean.md) for Clean)

## Workflow

### Step 1: Map Failures to Requirements

For each failure the user wants to fix, note:
- Factor and requirement (e.g. clean, null_rate)
- Target (e.g. schema.table.column or table)
- Measured value and threshold (from report)

### Step 2: Use Factor Docs and Templates

- Read the relevant factor doc (e.g. Clean) for the requirement's meaning and why it matters.
- Remediation templates are optional; when added, their location will be documented in the spec or README. If templates exist (e.g. under `agent/remediation/` or `remediation/`), use them for generic fix patterns and SQL examples.
- If no template exists, reason from the factor doc and suggest concrete steps (e.g. "add a default", "backfill nulls", "add a unique constraint").

### Step 3: Generate User-Specific Suggestions

Substitute the user's actual schema, table, and column names into the fix patterns. Present:

- **What** — Requirement and why it failed (brief).
- **Fix** — Concrete steps or SQL for their environment.
- **Review** — Remind them to review and run changes themselves.

Group by effort if helpful (e.g. quick wins vs larger changes).

### Step 4: Present for Review

Present suggestions in a clear order. For each, state that it is for the user to review and execute.

**STOP:** Do not execute any suggested SQL or commands.

## Output

- Per-failure (or grouped) remediation suggestions
- All suggestions marked as "for user to review and run"
- Optional: next steps (e.g. re-assess with `--compare` after they apply fixes)
