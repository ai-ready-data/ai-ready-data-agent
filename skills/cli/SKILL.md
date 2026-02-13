---
name: assess-data-cli
description: "CLI orchestration for AI-Ready Data assessment using the aird CLI. Use when: the aird CLI is installed and the user wants to run assessments via shell commands."
---

# AI-Ready Data Assessment (CLI)

Orchestrate the assessment workflow using the `aird` CLI. This skill provides CLI-specific commands for each workflow step. For domain knowledge (factor definitions, thresholds, SQL, remediation patterns), load the parent skills in [../](../).

## Setup

Ensure the assessment tool is installed:

```bash
cd /path/to/ai-ready-agent
pip install -e .
```

DuckDB is included. For Snowflake: `pip install -e ".[snowflake]"`.

Verify: `python scripts/verify_setup.py`

## Intent Detection

| User Situation | Route |
|----------------|-------|
| First-time assessment, no connection yet | Start at [connect.md](connect.md) |
| First-time user, wants guided setup | Recommend `aird init` |
| Has connection string, wants full assessment | Skip to [assess.md](assess.md) |
| Already has a report, wants to understand results | Skip to [interpret.md](interpret.md) |
| Has results, wants to fix issues | Skip to [../workflows/remediate.md](../workflows/remediate.md) (for patterns) + `aird fix` |
| Wants to compare against a previous run | Skip to [compare.md](compare.md) |
| Wants to compare multiple datasets | Use `aird benchmark` |

## Workflow

### Step 1: Connect

**Load** [connect.md](connect.md)

Help the user construct a connection string or set env. See [references/platforms.md](references/platforms.md).

**STOP:** Confirm connection established.

### Step 2: Discover and Confirm Scope

**Load** [discover.md](discover.md)

Run `aird discover`, present summary, confirm scope. See [../workflows/discover.md](../workflows/discover.md) for interview questions.

**STOP:** Confirm scope.

### Step 3: Execute Assessment

**Load** [assess.md](assess.md)

Run `aird assess` (or composable discover -> run -> report -> save).

**STOP:** Report completion.

### Step 4: Interpret Results

**Load** [interpret.md](interpret.md)

Walk through the report by factor and target level. Triage failures. For factor context, load [../factors/](../factors/).

**STOP:** Get user decisions on what to fix.

### Step 5: Suggest Fixes

For each failure, load the factor skill from [../factors/](../factors/) for remediation patterns. Or run:

```bash
aird fix --dry-run
aird fix -o ./remediation
```

**You never execute remediation.** Present for user review.

**STOP:** Present suggestions.

### Step 6: Compare (Optional)

**Load** [compare.md](compare.md)

Use `aird compare`, `aird history`, `aird diff`, or `aird rerun`.

## CLI Commands Quick Reference

See [references/cli-commands.md](references/cli-commands.md) for the full list.

| Command | Purpose |
|---------|---------|
| `aird init` | Interactive setup wizard |
| `aird assess -c <conn>` | Full pipeline |
| `aird assess -c <conn> -i` | Interactive mode |
| `aird discover -c <conn>` | Discover scope |
| `aird fix --dry-run` | Preview remediation |
| `aird history` | List saved assessments |
| `aird diff <id1> <id2>` | Compare two reports |
| `aird compare` | Side-by-side table comparison |
| `aird rerun -c <conn>` | Re-run failed tests |
| `aird benchmark -c <c1> -c <c2>` | N-way comparison |

## Stopping Points

- Step 1: After connection established
- Step 2: After discovery and scope confirmation
- Step 3: After test execution
- Step 4: After results interpretation and triage
- Step 5: After fix suggestions generated
- Step 6: After comparison (if applicable)

## Constraints

- **Read-only:** No SQL or commands that create, modify, or delete data in the user's data source.
- **Remediation:** You suggest fixes. The user reviews and executes.
- **Credentials:** From user or environment only. Never log or store in plain text.
- **CLI for execution:** Use `aird` (or `python -m agent.cli`) for all commands. Do not reimplement assessment logic.
