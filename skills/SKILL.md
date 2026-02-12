---
name: assess-data
description: "Assess a database against the AI-Ready Data Framework. Use when: evaluating AI readiness, running data quality assessments, checking if data is AI-ready. Triggers: assess my data, is my data AI-ready, data readiness, run assessment, evaluate my database."
---

# AI-Ready Data Assessment

End-to-end workflow for assessing a database against the AI-Ready Data Framework. Produces a scored report across six factors (Clean, Contextual, Consumable, Current, Correlated, Compliant) at three workload levels (L1: Analytics, L2: RAG, L3: Training).

## Forbidden Actions

- NEVER execute SQL that creates, modifies, or deletes data in the user's database
- NEVER execute remediation SQL — present it for the user to review and run
- NEVER skip a STOP point — always wait for explicit user confirmation
- NEVER store or log database credentials in plain text
- NEVER proceed to the next skill without confirming the current skill's output

## Setup

**Load** [references/platforms.md](references/platforms.md) when helping users construct connection strings.

Ensure the assessment tool is installed:

```bash
cd /path/to/ai-ready-agent
pip install -e .
```

DuckDB is included. For Snowflake: `pip install -e ".[snowflake]"`.

## Intent Detection

| User Situation | Route |
|----------------|-------|
| First-time assessment, no connection yet | Start at Step 1 |
| First-time user, wants guided setup | Recommend `aird init` or start at [interview/SKILL.md](interview/SKILL.md) |
| Has connection string, wants full assessment | Skip to [connect/SKILL.md](connect/SKILL.md) |
| Already connected, wants to re-run | Skip to [assess/SKILL.md](assess/SKILL.md) |
| Has a report, wants to understand results | Skip to [interpret/SKILL.md](interpret/SKILL.md) |
| Has results, wants to fix issues | Skip to [remediate/SKILL.md](remediate/SKILL.md) |
| Wants to compare against a previous run | Skip to [compare/SKILL.md](compare/SKILL.md) |
| Wants to compare multiple datasets | Use `aird benchmark` or skip to [compare/SKILL.md](compare/SKILL.md) |

## Workflow

### Step 1: Gather Context and Platforms

**Load** [interview/SKILL.md](interview/SKILL.md) (Phase 1 only)

Ask **what platform they're using** (DuckDB, SQLite, Snowflake, …). For first-time users, recommend `aird init` for interactive guided setup. Then ask about goals, workload (L1/L2/L3), and scope.

**STOP:** Wait for user responses before proceeding.

### Step 2: Connect

**Load** [connect/SKILL.md](connect/SKILL.md)

For each platform the user named, establish a connection string (or env var) and the right driver. See [references/platforms.md](references/platforms.md). First-time users can also use `aird init` to set up their connection interactively.

**STOP:** Confirm connection established.

### Step 3: Discover and Confirm Scope

**Load** [discover/SKILL.md](discover/SKILL.md)

Enumerate schemas, tables, and columns. Then **Load** [interview/SKILL.md](interview/SKILL.md) (Phase 2) to walk through discoveries with the user — confirm scope, exclusions.

**STOP:** Present discovery summary and confirm scope.

### Step 4: Execute Assessment

**Load** [assess/SKILL.md](assess/SKILL.md)

Run the assessment CLI (assess or composable discover → run → report → save). Score results at L1/L2/L3. Options include:

- `aird assess -i` for interactive guided flow
- `--factor` to assess a single factor (e.g. `--factor clean`)
- `--dry-run` to preview which tests would run without executing them

**STOP:** Report execution completion.

### Step 5: Interpret Results

**Load** [interpret/SKILL.md](interpret/SKILL.md)

Walk through results interactively. Then **Load** [interview/SKILL.md](interview/SKILL.md) (Phase 3) for failure triage — user confirms which failures matter and which to fix.

**STOP:** Present findings and get triage decisions.

### Step 6: Generate Fixes

**Load** [remediate/SKILL.md](remediate/SKILL.md)

For each failure the user wants to fix, generate specific suggestions using factor docs and remediation templates (when present). Group by effort. Present for review only. After the user applies fixes, they can re-assess with `--compare` (and optionally same `--context`) to see progress — see [assess/SKILL.md](assess/SKILL.md) § After the user applies fixes.

**STOP:** Present fix suggestions for review.

### Step 7: Save and Compare (Optional)

**Load** [compare/SKILL.md](compare/SKILL.md)

Results are saved to history when not using `--no-save`. Use `aird history` and `aird diff` to compare runs. On re-assess, use `--compare` to show progress. Additional comparison tools:

- `aird compare` — side-by-side table comparison from the most recent assessment
- `aird rerun` — re-run only failed tests and show the delta
- `aird benchmark -c conn1 -c conn2` — N-way dataset comparison across multiple connections

## Stopping Points

- Step 1: After gathering user context
- Step 2: After connection established
- Step 3: After discovery and scope confirmation
- Step 4: After test execution
- Step 5: After results interpretation and triage
- Step 6: After fix suggestions generated
- Step 7: After comparison (if applicable)

## Output

- Assessment report (JSON or markdown, from CLI)
- Optional context file (user-controlled, e.g. `--context`)
- Assessment history (`~/.aird/assessments.db` or `AIRD_DB_PATH`)
- Remediation suggestions (presented for review; user executes)
