---
name: compare
description: "Compare two assessment runs; show history and diff between reports."
parent_skill: assess-data
---

# Compare Runs

List saved assessments and compare two reports (by id or by file). Use after re-assessment to show progress or regressions.

## Forbidden Actions

- NEVER modify or delete saved assessments from the CLI (the CLI is read-only for the data source; history is local and user-controlled)
- NEVER log connection strings when showing history

## When to Load

- User wants to see previous assessment ids or list history
- User wants to compare two runs (e.g. before vs after fixes)
- After re-assess, to show diff when `--compare` was not used or user wants a different comparison

## Prerequisites

- At least one saved assessment (from `aird assess` without `--no-save`, or `aird save --report ...`)
- CLI installed

## Workflow

### Step 1: List History

```bash
aird history
```

Optional: `--connection <filter>` to filter by connection, `-n 20` (or `--limit 20`) for limit. Default limit is 20.

Output is tab-separated: `id`, `created_at`, `L1%`, `L2%`, `L3%`, `connection_fingerprint`. Show the user the list; they need an id to re-output a report or to run diff. Full command reference: [references/cli-commands.md](../references/cli-commands.md).

### Step 2: Re-Output a Report (Optional)

If the user wants to see a saved report again in a different format:

```bash
aird report --id <assessment_id> -o markdown
```

Or `-o json:path/to/report.json`.

### Step 3: Diff Two Reports

Compare two assessments by id:

```bash
aird diff <id1> <id2>
```

Or by file paths if they have report JSON files:

```bash
aird diff --left path/to/report1.json --right path/to/report2.json
```

Present the diff output: score deltas, tests added/removed, pass/fail changes.

### Step 4: Re-Assess with Compare

On a re-run, user can get an automatic diff vs the previous run for the same connection:

```bash
aird assess -c "<connection>" --compare -o markdown
```

So they don't need to run `aird diff` separately if they only want "compare to last run."

## Output

- History list (ids and summary)
- Optional: re-rendered report from an id
- Diff between two reports (scores, test changes)
- Optional: recommendation to re-assess with `--compare` for ongoing progress tracking
