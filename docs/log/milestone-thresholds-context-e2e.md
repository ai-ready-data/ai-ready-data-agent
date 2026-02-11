# Milestone: Threshold overrides, context file, E2E tests

**Date:** 2026-02-10

**Goals:** (1) Wire threshold overrides from JSON. (2) Wire context YAML into discovery and report. (3) Add automated E2E tests for the assess pipeline.

---

## 1. Threshold overrides

- **agent/thresholds.py:** Added `load_thresholds(path)` — loads optional JSON and merges with `DEFAULT_THRESHOLDS` by requirement key. `get_threshold()` and `passes()` accept optional `thresholds` dict; when None, built-in defaults are used.
- **agent/run.py:** `run_tests(..., thresholds=...)` passes loaded thresholds into `passes()` for each result.
- **agent/pipeline.py:** Loads thresholds via `load_thresholds(config.thresholds_path)` once per `run_assess`, passes to single and estate paths.
- **Docs:** CLI spec documents JSON shape; keys merge over built-in (e.g. `null_rate`, `duplicate_rate`).

## 2. Context file

- **agent/pipeline.py:** Added `_load_context(path)` — loads optional YAML; returns dict or None. Scope resolution: per-target `schemas`/`tables` > context file > config. Report includes `user_context` when context is loaded.
- **Discovery:** No change; pipeline passes `schemas` and `tables` derived from target + context + config into existing `discover(connection, schemas=..., tables=...)`.
- **Docs:** CLI spec and skills/references/context-file.md document YAML shape (`schemas`, `tables`).

## 3. Automated E2E tests

- **tests/test_e2e_assess.py:** Three tests:
  - `test_e2e_assess_report_structure_and_failures`: Temp DuckDB with nulls/duplicates → run_assess → assert report shape and at least one L1 failure.
  - `test_e2e_assess_with_threshold_override`: Custom thresholds JSON → assert null_rate failures when strict.
  - `test_e2e_assess_with_context_scope`: Context YAML with schemas → assert report has `user_context` and tests run.
- **pyproject.toml:** Optional dependency `dev = ["pytest>=7.0"]`. Run with `pip install -e ".[dev]"` then `pytest tests/ -v`.

---

## What’s next (reflection)

After this milestone, the natural next steps are:

- **Remediation linkage** (candidate 2): Link failures to remediation content; add templates per requirement key; report includes ref for interpret skill.
- **First community platform**: Use add-platform skill to add one platform (e.g. Snowflake or Postgres); document in CONTRIBUTING and docs/coverage.

See [milestone-next-candidates.md](milestone-next-candidates.md) § Moving forward for prioritization and how to move forward.
