---
name: report
description: "Present an assessment report to the user: overall summary, factor-by-factor walkthrough, and next steps."
parent_skill: assess-data
---

# Present Report

Render and walk through an assessment report with the user. This skill is about **presenting** the report clearly; for **triaging failures** and deciding what to fix, load [interpret/SKILL.md](../interpret/SKILL.md) after this.

## Forbidden Actions

- NEVER invent scores or results; use the report JSON as the single source of truth
- NEVER skip factors that have failures — every factor with results must be mentioned
- NEVER execute remediation or suggest fixes — that is the remediate skill's job

## When to Load

- After `aird assess` completes and the user wants to see the report
- When the user asks to re-render a previously saved report (`aird report --id <id>`)
- When the user asks "show me my results" or "what does my report look like"

## Prerequisites

- A report is available: either from the last `aird assess` run (returned as JSON), from a saved assessment (`aird report --id <id> -o json:report.json`), or as a markdown file
- The report conforms to the schema defined in [docs/specs/report-spec.md](../../docs/specs/report-spec.md)

## Report Structure Reference

The canonical report shape is defined in [docs/specs/report-spec.md](../../docs/specs/report-spec.md). Key fields the agent should use:

- `target_workload` — The user's target level (l1, l2, l3, or null)
- `summary` — Overall pass counts and percentages at L1/L2/L3
- `factor_summary` — Per-factor roll-up (factor name, pass counts at each level)
- `results` — Flat list of test results with `measured_value`, `threshold`, `direction`, and pass/fail per level
- `question_results` — Optional survey answers
- `not_assessed` — Requirements or factors that could not be evaluated

## Workflow

### Step 1: Lead with Target Workload

If `target_workload` is set (e.g. `"l2"`), open with the score at that level:

> "Your data scores **X%** for L2 (RAG) readiness across N tests."

If `target_workload` is null, show all three levels:

> "Across N tests: L1 (Analytics) X%, L2 (RAG) Y%, L3 (Training) Z%."

Use the `summary` object for these numbers.

### Step 2: Overall Score Headline

Briefly state the total number of tests and the pass/fail breakdown. Highlight whether the user's target level has significant gaps (e.g. "3 of 12 tests fail at L2").

### Step 3: Factor-by-Factor Walkthrough

For each entry in `factor_summary`, present the factor with its scores. Use the corresponding results from the `results` list grouped by factor.

For each factor:

1. **Name and summary** — e.g. "Clean: 8/10 pass at L2 (80%)"
2. **Highlight failures** at the target level (or L1 if no target set). For each failing test, show:
   - Requirement key (e.g. `null_rate`)
   - Measured value vs threshold (e.g. "measured 0.15, threshold 0.05 for L2")
   - Direction (lte = "should be at most", gte = "should be at least")
3. **Passing tests** — mention briefly or skip if all pass ("All 4 contextual tests pass at L2")

Factor docs for context:
- **Clean:** [factors/factor-00-clean.md](../../factors/factor-00-clean.md)
- **Contextual:** [factors/factor-01-contextual.md](../../factors/factor-01-contextual.md)
- Additional factors: [factors/](../../factors/) (add as they exist)

### Step 4: Survey Results

If `question_results` is present, summarize under a "Survey Results" heading. Group by factor and show question + answer + pass/fail. Keep it brief.

### Step 5: Not-Assessed Gaps

If `not_assessed` is non-empty, explain what could not be assessed and why. Ask the user if they can provide the missing inputs (e.g. "Semantic model coverage could not be assessed because no semantic views were found. Do you have a semantic model defined elsewhere?").

### Step 6: Offer Next Steps

After presenting the report, offer the user a choice:

1. **Interpret and triage** — "Want me to walk through the failures and help you decide what to fix?" → Load [interpret/SKILL.md](../interpret/SKILL.md)
2. **Remediate** — "Want me to suggest fixes for the failures?" → Load [remediate/SKILL.md](../remediate/SKILL.md)
3. **Compare** — "Want to compare this with a previous assessment?" → Load [compare/SKILL.md](../compare/SKILL.md)
4. **Export** — "Want to save or re-render this report?" → `aird report --id <id> -o json:path` or `-o markdown`

**STOP:** Wait for user to choose a next step.

## Output

- User has a clear understanding of their assessment results
- Scores presented at the target workload level (or all levels)
- Every factor with results is covered
- Failures are highlighted with measured values and thresholds
- User is ready to proceed to interpret, remediate, compare, or export
