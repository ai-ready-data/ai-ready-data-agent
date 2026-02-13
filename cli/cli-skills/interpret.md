---
name: interpret
description: "Present and interpret assessment reports via the CLI. Walk through results by factor and workload; triage failures with the user."
parent_skill: assess-data
---

# Interpret Results (CLI)

Present the assessment report and triage failures using the `aird` CLI. For scoring rules and threshold reference, see [../workflows/interpret.md](../workflows/interpret.md). For factor definitions, see [../factors/](../factors/).

## Forbidden Actions

- NEVER execute remediation — only suggest
- NEVER invent scores or results; use the report as source of truth
- NEVER skip triage when the user expects to decide what to fix

## When to Load

- After assess; user has a report (file or from last run)
- User wants to understand what passed/failed and why

## Prerequisites

- Report available (JSON or markdown). Get it from: (1) the report file or path from the last assess step, (2) or if the user has a saved assessment, load by id: `aird report --id <id> -o markdown` or `-o json:path/to/report.json`.
- For report **presentation** (showing results without triage), use `aird report`.
- This skill focuses on **triage** — helping the user decide what to fix.

## Workflow

### Step 1: Render the Report

If the user wants to see or re-render a report:

```bash
# Markdown to terminal
aird report --id <assessment_id> -o markdown

# JSON to file
aird report --id <assessment_id> -o json:report.json
```

Or from results:

```bash
aird report --results results.json -o markdown
```

### Step 2: Lead with Target Level

If the user stated a target workload (L1, L2, or L3) in the interview, start there. For example: "Your data scores X% for L2 (RAG) readiness. Here's what's holding you back."

Summarize: total tests, pass counts or percentages at L1/L2/L3 from the report summary.

### Step 3: Factor-by-Factor Walkthrough

Use the `factor_summary` array in the report to identify which factors have failures at the user's target level. For each factor that has failures, load the corresponding factor skill from [../factors/](../factors/) for context on why the factor matters.

Each result in the report includes `measured_value`, `threshold` (L1/L2/L3 values), and `direction` (lte or gte) — use these to explain why the test failed.

### Step 4: Failure Triage

For the main failures, ask the user:

- "Is this expected?" (e.g. high null rate on an optional column)
- "Do you want me to suggest a fix?"
- "Should we exclude this from future assessments?"

Record their decisions so you can generate fixes only for what they want to address.

**STOP:** Get user decisions before generating remediation suggestions.

### Step 5: Gaps and Limitations

If the report includes a `not_assessed` section, explain what couldn't be assessed and why.

### Step 6: Offer Next Steps

1. **Remediate** — "Want me to suggest fixes?" → Load [remediate.md](remediate.md)
2. **Compare** — "Want to compare with a previous assessment?" → Load [compare.md](compare.md)
3. **Export** — `aird report --id <id> -o json:path` or `-o markdown`

**STOP:** Wait for user to choose a next step.

## Output

- User understands scores and failures at their target level
- User has decided which failures to fix vs accept
- Ready to proceed to [remediate.md](remediate.md) for fix suggestions
