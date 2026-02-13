# Milestone scale-back: Clean-focused Snowflake demo

**Date:** 2026-02

**Decision:** Scale back the Snowflake demo milestone. Do not force the questions implementation as the main path. Focus on showing how **Clean** works and making Clean very good and Snowflake-specific.

## What changed

1. **Snowflake suite is Clean-only** — Removed the five factor placeholder tests (contextual, consumable, current, correlated, compliant) from `common_snowflake`. The report for Snowflake now shows only Clean tests (table_discovery, null_rate, duplicate_rate, zero_negative_rate, type_inconsistency_rate, format_inconsistency_rate).

2. **Survey is optional** — The demo runbook leads with `aird assess -c "snowflake://..."` (no `--survey`). Survey is documented as an optional add-on. We do not require question-based flow for the main demo.

3. **Clean on Snowflake improved** — Suite uses Snowflake-native SQL; table count query uses `UPPER(table_schema)` so system schemas are excluded regardless of casing. Doc section "What Clean measures on Snowflake" added to the runbook.

4. **Docs and tests** — Demo runbook rewritten to be Clean-first. Coverage README updated. `test_snowflake_adapter` expects 6 tests and factor set `{"clean"}` only.

## What stays

- Question-based flow (registry, survey, report) remains in the codebase; it is available via `--survey` and suite-level question files. We are not removing it, only not making it the default or required for the milestone.
- DuckDB and SQLite suites are unchanged (Clean + their existing suites).
- Thresholds for the old factor placeholders remain in `agent/thresholds.py` for backward compatibility if any other suite uses them.

## Outcome

A person can run `aird assess -c "snowflake://..."` with scope (`-s`/`-t` or `--context`) and get a **Clean-only** report that is Snowflake-specific and easy to explain. Optional: add `--survey` for question-based results.
