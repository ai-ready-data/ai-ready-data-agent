# Implementation coverage by suite and platform

This doc tracks which requirement keys are implemented in which test suites and platforms. As the community adds suites (e.g. Snowflake, BigQuery, Postgres) or new factors, update the tables here so contributors can see status at a glance.

Scoping logic: [agent/run.py](../agent/run.py) `_column_matches_requirement`. Thresholds: [agent/thresholds.py](../agent/thresholds.py).

**Demo runbook:** [docs/demo-snowflake.md](../demo-snowflake.md) — run **Clean** assessment against Snowflake, scoped to your AI workload datasets. Survey is optional.

---

## Factor 0: Clean

Built-in suites: **DuckDB** (`common`), **SQLite** (`common_sqlite`), **Snowflake** (`common_snowflake`). All implement the same Clean requirement keys. Snowflake uses `COUNT_IF` and Snowflake-compatible SQL. Scoping uses inventory (column names, data types) so only relevant columns are tested; the agent's LLM can refine scope (e.g. which columns are amounts or date-like) via context or follow-up.

| Key | Implemented | Scope / notes |
|-----|-------------|----------------|
| `table_discovery` | Yes | Platform: count of user tables. |
| `null_rate` | Yes | Per column; L1/L2/L3 thresholds. |
| `duplicate_rate` | Yes | Per table; L1/L2/L3 thresholds. |
| `zero_negative_rate` | Yes | Numeric columns only (inventory `data_type`). Rate = fraction of values ≤ 0. Agent can refine which columns "should be positive" via context. |
| `type_inconsistency_rate` | Yes | Numeric columns only. Rate = fraction of non-null that fail TRY_CAST to DOUBLE/REAL. Agent can interpret failures and suggest fixes. |
| `format_inconsistency_rate` | Yes | String columns with date-like names (e.g. `date`, `time`, `created`, `updated`, `_at`). Rate = fraction of non-null that don't parse as DATE. Agent can refine which columns are dates and expected format. |

---

## Snowflake: Clean-only (milestone focus)

| Key | Implemented | Notes |
|-----|-------------|-------|
| Clean (all 6) | Yes | `common_snowflake` suite; `agent/suites/clean_snowflake.py`. Snowflake-native SQL (COUNT_IF, TRY_CAST, UPPER for system schema filter). |
| Question-based (survey) | Optional | Available via `--survey`; suite-level questions in `agent/suites/questions/common_snowflake.yaml`. Not required for the Clean-focused demo. |

---

*Add new factors or platform-specific sections below as the repo grows.*
