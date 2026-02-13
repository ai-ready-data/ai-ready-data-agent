---
name: assess
description: "Run the assessment: discover (if not already done), execute tests, score at L1/L2/L3, produce report, optionally save."
parent_skill: assess-data
---

# Execute Assessment

Run the assessment CLI to discover (if needed), generate and execute tests, score results, and produce a report. Optionally save to history for later comparison.

## Forbidden Actions

- NEVER run SQL that creates, modifies, or deletes data
- NEVER skip read-only enforcement (the CLI enforces this; do not bypass)
- NEVER log the connection string with credentials

## When to Load

- After connect (and optionally after discover/scope confirmation)
- User wants to run or re-run the full assessment

## Prerequisites

- Connection string or `AIRD_CONNECTION_STRING`
- Optionally: inventory from a previous discover step (for composable run)

## Workflow

### Option A: One-shot (single database)

Use the connection string from the connect step, or ensure `AIRD_CONNECTION_STRING` is set. Run the full pipeline in one command:

```bash
aird assess -c "<connection>" -o markdown
```

Or output JSON for parsing:

```bash
aird assess -c "<connection>" -o json:report.json
```

For a guided interactive experience (scope selection, progress bars, colored output):

```bash
aird assess -c "<connection>" -i
```

If the command fails, report the error to the user and do not proceed; suggest checking connection string, driver, or network.

**Useful flags:** See [references/cli-commands.md](references/cli-commands.md) for the full list.
- `--no-save` — Do not persist report to history
- `--compare` — After run, output diff vs previous assessment for same connection
- `--dry-run` — Stop after generating tests; do not execute
- `--context <path>` — Path to context YAML
- `--suite <name>` — Force suite (default is auto from connection)
- `-i` / `--interactive` — Guided interactive assessment flow (discover → select scope → preview → run → results)
- `--audit` — Enable audit logging
- `--factor <factor>` — Filter assessment to a single factor (e.g., `clean`, `contextual`)
- `--survey` — Include survey questions in assessment
- `--survey-answers <path>` — Path to pre-filled survey answers YAML
- `--workload {analytics,rag,training}` — Set target workload level
- `--thresholds <path>` — Custom thresholds file

**STOP:** Confirm the command completed and report is available.

### Option B: Composable (discover already done)

If you already have an inventory file from [discover.md](discover.md):

```bash
aird run -c "<connection>" --inventory inventory.json -o results.json
aird report --results results.json -o json:report.json
aird save --report report.json
```

To output markdown for the user, also run: `aird report --results results.json -o markdown` (or re-output from saved id: `aird report --id <id> -o markdown`).

**STOP:** Confirm report is produced and, if save was used, note the assessment id for later diff.

## Output

- Report (markdown or JSON)
- Optionally: assessment id (if saved)
- Optionally: diff vs previous run (if `--compare` was used)
- Ready to proceed to [interpret.md](interpret.md)

## Related Commands

- `aird compare` — Compare results for two tables side-by-side from the most recent assessment
- `aird rerun` — Re-run only failed tests from the most recent assessment, show improvement delta
- `aird benchmark -c conn1 -c conn2` — Compare N datasets side-by-side (repeatable `-c`, at least 2 required)

## After the user applies fixes

When the user has applied remediation and wants to re-assess: run assess again with `--compare` (and optionally the same `--context` path) to show progress. Example: `aird assess -c "<connection>" --compare -o markdown`.

For a quicker alternative, use `aird rerun` to re-run only previously failed tests and show the improvement delta without re-running the full assessment.

To compare specific tables within the same assessment, use `aird compare` for a side-by-side view.

## Audit Logging

If audit logging is enabled (see [../audit/SKILL.md](../audit/SKILL.md)), log the assessment results after completion:

```sql
-- Log to ~/.snowflake/cortex/aird-audit.db
INSERT INTO assessments (
    assessment_id,
    session_id,
    connection_sanitized,
    scope_json,
    results_json,
    overall_score,
    l1_pass,
    l2_pass,
    l3_pass
)
VALUES (
    '{assessment_id}',
    '{session_id}',
    '{connection_with_credentials_removed}',
    '{json_array_of_tables}',
    '{full_results_json}',
    {overall_score},
    {1_if_l1_pass_else_0},
    {1_if_l2_pass_else_0},
    {1_if_l3_pass_else_0}
);
```

Replace placeholders with actual values from the assessment report.
