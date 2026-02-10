# Milestone: Clean factor E2E on DuckDB

**Date:** 2026-02-10

**Goal:** Testing suite end-to-end working for the Clean factor against a real DuckDB database.

---

## What we did

1. **Clean suite for DuckDB**  
   - Added `agent/suites/clean_duckdb.py` defining the **common** suite with Clean factor requirement keys from factor-00-clean:
     - **table_discovery** (platform): count of user tables.
     - **null_rate** (per column): query template that computes null fraction per column; expanded from inventory.
     - **duplicate_rate** (per table): query template that computes duplicate row fraction per table; expanded from inventory.
   - Query templates use `{schema_q}`, `{table_q}`, `{column_q}` placeholders filled with quoted identifiers. The suite is registered over the previous minimal “common” suite when `agent.suites.clean_duckdb` is imported (see `agent/platform/__init__.py`).

2. **Test expansion from inventory**  
   - In `agent/run.py`, added `expand_tests(suite_tests, inventory)`:
     - Tests with a static `query` are emitted as one test each.
     - Tests with `query_template` and `target_type: column` are expanded to one test per row in `inventory["columns"]`, with identifiers quoted for SQL.
     - Tests with `query_template` and `target_type: table` are expanded to one test per row in `inventory["tables"]`.
   - The runner now runs the expanded list of tests and records one result per test (with `test_id` including target, e.g. `null_rate|main|products|name`).

3. **Thresholds and pass/fail**  
   - Added `agent/thresholds.py` with `DEFAULT_THRESHOLDS` per requirement key (L1/L2/L3). For rate metrics, pass = `measured_value <= threshold`.
   - `table_discovery` is treated as informational (always pass).
   - In `run_tests()`, each result’s `measured_value` is compared to the thresholds and `l1_pass`, `l2_pass`, `l3_pass` are set accordingly.

4. **Sample DuckDB and E2E**  
   - Added `scripts/create_sample_duckdb.py` to create a DuckDB file (default `sample.duckdb` in repo root) with one table, `main.products` (id, name, amount), with intentional nulls and duplicate rows.
   - Ran E2E: `python3 -m agent.cli assess -c "duckdb:///path/to/sample.duckdb" -o markdown`. Result: 5 tests (1 platform + 3 null_rate columns + 1 duplicate_rate table), with correct pass/fail (e.g. null_rate fails on `name`, duplicate_rate fails on `main.products`).
   - `sample.duckdb` is in `.gitignore`.

---

## What’s persisted

- **Code**
  - `agent/suites/__init__.py`, `agent/suites/clean_duckdb.py` — Clean suite and templates.
  - `agent/thresholds.py` — Built-in L1/L2/L3 thresholds and `passes()`.
  - `agent/run.py` — `expand_tests()`, expansion in `run_tests()`, threshold-based pass/fail.
  - `agent/platform/__init__.py` — Import of `agent.suites.clean_duckdb` so “common” is the Clean suite.
- **Scripts**
  - `scripts/create_sample_duckdb.py` — Creates sample DuckDB for E2E.
- **Config**
  - `.gitignore` — `sample.duckdb` and existing entries.

No schema or API changes to storage or CLI; existing commands and artifacts unchanged.

---

## What’s next

- **More Clean requirements**  
  Add tests (and templates) for `format_inconsistency_rate`, `type_inconsistency_rate`, `zero_negative_rate` when we have clear SQL definitions and, if needed, inventory hints (e.g. which columns are numeric for zero_negative).

- **Threshold overrides**  
  Support `--thresholds` / `AIRD_THRESHOLDS` JSON file in the runner so users can override built-in thresholds without code changes.

- **Remediation**  
  Link failures to remediation content (e.g. per requirement key) in the report or in a separate step.

- **Other platforms**  
  Reuse the same Clean requirement keys and expander pattern for Snowflake (or other SQL) with platform-specific query templates where needed.

- **Automated E2E test**  
  Add a pytest (or script) that creates a temp DuckDB with `create_sample_duckdb`-style data, runs `assess`, and asserts on report structure and expected pass/fail counts.
