---
name: interpret
description: "Walk through the assessment report by factor and workload; triage failures with the user."
parent_skill: assess-data
---

# Interpret Results

Read the assessment report and present results in a clear, conversational way. Walk through by factor and target workload (L1/L2/L3). Triage failures with the user so they can decide what to fix and what to accept.

## Forbidden Actions

- NEVER execute remediation — only suggest
- NEVER invent scores or results; use the report as source of truth
- NEVER skip triage when the user expects to decide what to fix

## When to Load

- After assess; user has a report (file or from last run)
- User wants to understand what passed/failed and why

## Prerequisites

- Report available (JSON or markdown). Get it from: (1) the report file or path from the last assess step, (2) or if the user has a saved assessment, load by id: `aird report --id <id> -o markdown` or `-o json:path/to/report.json`.
- Report conforms to the schema defined in [docs/specs/report-spec.md](../../docs/specs/report-spec.md). Key fields: `summary`, `factor_summary`, `results` (with `threshold` and `direction`), `not_assessed`, `target_workload`.
- For report **presentation** (showing results without triage), see [report/SKILL.md](../report/SKILL.md). This interpret skill focuses on **triage** — helping the user decide what to fix.

## Workflow

### Step 1: Lead with Target Level

If the user stated a target workload (L1, L2, or L3) in the interview, start there. For example: "Your data scores X% for L2 (RAG) readiness. Here's what's holding you back."

Summarize: total tests, pass counts or percentages at L1/L2/L3 from the report summary.

### Step 2: Factor-by-Factor Walkthrough

Use the `factor_summary` array in the report to identify which factors have failures at the user's target level. For each factor that has failures (or low scores), briefly explain what the factor means using the framework:

- **Clean:** [factors/factor-00-clean.md](../../factors/factor-00-clean.md)
- Contextual, Consumable, Current, Correlated, Compliant: factor docs in [factors/](../../factors/) (add as they exist)

Then list the failing tests for that factor. Each result in the report includes `measured_value`, `threshold` (L1/L2/L3 values), and `direction` (lte or gte) — use these to explain why the test failed (e.g. "null_rate measured 0.15, threshold is 0.05 for L2, should be at most"). Don't dump the full report; summarize and highlight.

### Step 3: Failure Triage (Phase 3 Interview)

**Load** [interview/SKILL.md](../interview/SKILL.md) (Phase 3: post-results)

For the main failures, ask the user:

- "Is this expected?" (e.g. high null rate on an optional column)
- "Do you want me to suggest a fix?"
- "Should we exclude this from future assessments?" (when context supports exclusions)

Record their decisions so you can generate fixes only for what they want to address.

**STOP:** Get user decisions before generating remediation suggestions.

### Step 4: Gaps and Limitations

If the report includes a `not_assessed` section (when present), explain what couldn't be assessed and why. Ask if they can provide missing inputs (e.g. additional metadata) if relevant.

## Output

- User understands scores and failures at their target level
- User has decided which failures to fix vs accept
- Ready to proceed to [remediate/SKILL.md](../remediate/SKILL.md) for fix suggestions
