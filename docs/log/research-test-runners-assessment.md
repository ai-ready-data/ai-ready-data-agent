# Research: Test runners and assessment scripts (last ~10 years)

**Date:** 2026-02-10

**Context:** Lessons from the last decade of test runners and assessment scripts that can inform the AI-ready assessment agent (run.py, report, thresholds, E2E, remediation).

---

## What we already align with

- **Declarative suites** — Suites (e.g. `clean_sqlite.py`) are data + query templates, not ad-hoc scripts; similar to modern “table-driven” / spec-by-example runners.
- **Read-only execution** — `execute_readonly` and no writes in the runner matches the “assessment = observe only” pattern.
- **Structured results** — Each test yields a fixed shape (test_id, factor, requirement, measured_value, l1/l2/l3_pass, optional error), which is easy to report and compare.
- **Configurable thresholds** — L1/L2/L3 and `load_thresholds()` match the idea of “policy in config, logic in code.”
- **Dry-run / preview** — `dry_run` returning test count + preview is a common “safety and debugging” feature in runners.

---

## Lessons we can reuse

### 1. Idempotent, deterministic runs

Runners (pytest, Jest, Go testing, etc.) assume: same inputs → same outcome. We’re close: discovery + inventory drive expansion; the main gap is **time or randomness in reports** (e.g. `created_at`). For E2E and regression, either freeze timestamps in tests or assert only on stable fields (summary, result counts, pass/fail).

### 2. Fail-fast vs collect-all

Many runners support “stop on first failure” vs “run everything and report.” We currently **collect-all** (every test gets a result/error). That’s ideal for assessment (full picture). If we add “critical” requirements later, we could add a small `fail_fast` or “required” set and exit early only when a required check fails.

### 3. Test and run identifiers

Stable IDs make comparison and history useful. We already have **composite test ids** (e.g. `null_rate|main|products|name`) and **assessment_id** in the API. Carrying a **run_id** (or same assessment_id) through pipeline → report → storage makes “compare two runs” and “same run, different output format” straightforward; the compare skill and report schema can key off it.

### 4. Structured failure reasons

Modern frameworks distinguish “error” (exception) from “assertion failure” (expected vs actual). We have `error` for exceptions and `l1_pass`/`l2_pass`/`l3_pass` for policy failure. One extra step that pays off: **always store a short, machine-readable reason** when a test fails (e.g. `measured_value > threshold` or `measured_value is None`). That helps remediation and interpret skills without parsing text.

### 5. Snapshot / golden outputs

Assessment and data-quality tools often use “golden” reports or key metrics. Our E2E (temp DB → assess → assert on report shape and expected pass/fail) is exactly that. A small extension: **persist one or more “golden” report snippets** (e.g. for a known bad column) and in E2E assert that the current run’s relevant slice matches (or that failures occur where expected). That catches threshold and report-structure regressions.

### 6. Timeouts and resource limits

Runners (pytest, Jest, etc.) use per-test or global timeouts to avoid hangs. Our tests are SQL; a single bad query can block the run. Adding **per-query timeouts** in `execute_readonly` (or the adapter) and treating timeout as a distinct result (e.g. `error: "timeout"`) would make the system safer in large estates and in CI.

### 7. Tags, filters, and scope

Pattern from pytest/Jest/Go: **tags or labels** (e.g. `@slow`, `@integration`) and “run only these.” We have **scope** (schemas, tables, target_type, requirement). We could add optional **tags** on suite definitions (e.g. `smoke`, `full`) and a CLI filter like `--only-tag smoke` so `expand_tests` (or a pre-step) drops tests that don’t match. That would support quick smoke runs and full assessments without new suites.

### 8. Remediation and “next step” in the report

Assessment tools (e.g. data-quality dashboards) often attach “how to fix” to each failed check. Our **remediation linkage** milestone (templates + `remediation_ref` in the report) is the same idea: the report stays the single artifact, and agents or UIs can resolve refs to human-readable guidance.

### 9. Parallel execution

Many runners parallelize by default (pytest-xdist, Jest workers). Our loop in `run_tests` is sequential. For large inventories, **running tests in parallel** (e.g. by table or by chunk of tests) with a small worker pool would reduce wall-clock time; the main constraint is connection/DB concurrency (e.g. one connection per worker or connection pool).

### 10. Single binary / single entrypoint

The trend is “one entrypoint” (e.g. `pytest`, `go test`). Our CLI with `assess` (and compare, etc.) is already that. Keeping “run assessment” as the single way to produce the report (and other commands only consuming reports) avoids script sprawl and keeps verify_setup and E2E as thin wrappers around the same pipeline.

---

## Direct mapping to our codebase

| Lesson                    | Where it fits |
|---------------------------|----------------|
| Stable run IDs            | `pipeline.run_assess` → `report` → storage; compare skill |
| Machine-readable fail reason | `agent/run.py` when appending to `results_list` (add e.g. `fail_reason`) |
| Per-query timeout         | `agent/platform/executor.py` (or adapter) around `execute_readonly` |
| Tags + filter             | Suite dicts + `expand_tests` or pre-filter; CLI `--only-tag` |
| Golden E2E                | E2E pytest + one or more golden report snippets |
| Remediation refs          | Report builder adds `remediation_ref` for failed tests |

---

## Summary

Our design already matches many modern test-runner and assessment-script patterns. The highest-leverage additions from the last decade are: **stable run/assessment IDs**, **explicit failure reasons in the report**, **per-query timeouts**, **optional tags/filters for scope**, **golden E2E**, and **remediation linkage**—most of which we’ve already identified in milestone candidates.
