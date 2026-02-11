# Plan: Contextual factor (Factor 1) — requirements, Snowflake suite, Cortex Code CLI

**Date:** 2026-02-11

**Status:** In progress. Factor doc written. Implementation next.

---

## Goal

Define Factor 1 (Contextual) with real requirements, implement a Snowflake test suite, and ensure the full flow works seamlessly with Cortex Code CLI. This is the proof of the "one factor at a time" pattern — factor doc → tests → thresholds → questions → verify.

---

## Decisions made

1. **One factor at a time.** Write the factor doc, implement tests, verify end-to-end before moving to the next factor. Interleaving validates that requirement keys are actually queryable.

2. **Factor order after Contextual:** Current (Factor 3) → Compliant (Factor 5) → Correlated (Factor 4) → Consumable (Factor 2). Based on what's queryable on Snowflake.

3. **Suite architecture:** Each factor file appends to the same `common_snowflake` suite. `register_suite` in `registry.py` needs to be changed from replace to extend so multiple factor files can contribute tests to one suite name.

4. **Semantic model coverage is platform-agnostic as a requirement.** The requirement is "a semantic model exists and covers these tables." On Snowflake, the test queries `information_schema.semantic_views` / `SHOW SEMANTIC VIEWS`. On other platforms, it might be dbt semantic layer, a catalog API, or question-based. Per-platform suites determine where to look.

5. **Threshold direction.** Contextual requirements are "higher is better" (coverage rates). The `passes()` function in `thresholds.py` currently only supports `measured <= threshold` (lower is better). Needs to support `measured >= threshold` for coverage metrics. Options: per-requirement direction flag, or invert the metric. Decision deferred to implementation — will resolve when wiring thresholds.

6. **Scope for v1:** Four measured requirements, one per semantic dimension. Keep it tight for the first round.

---

## Four semantic dimensions of Contextual

From the factor definition:

- **Structural Semantics (What the data is):** Typed schemas, constraint declarations, evolution contracts.
- **Business Semantics (What the data means):** Versioned definitions, calculation logic, controlled vocabularies.
- **Entity Semantics (How the data connects):** Typed, scoped, probabilistic relationships; referential integrity of meaning.
- **Contextual Semantics (When/where it applies):** Temporal scope, jurisdictional applicability, provenance, confidence.

---

## Requirements (v1)

| Dimension | Key | What it measures | Snowflake query approach |
|---|---|---|---|
| **Structural** | `primary_key_defined` | Fraction of tables with a declared primary key | `SHOW PRIMARY KEYS IN SCHEMA` or constraints metadata |
| **Business** | `semantic_model_coverage` | Fraction of assessed tables represented in a semantic model | `information_schema.semantic_views` + `DESCRIBE SEMANTIC VIEW` |
| **Entity** | `foreign_key_coverage` | Fraction of tables with declared FK relationships | `SHOW IMPORTED KEYS` or constraints metadata |
| **Contextual** | `temporal_scope_present` | Fraction of tables with identifiable temporal columns (created_at, updated_at, valid_from, etc.) | Query `information_schema.columns` for TIMESTAMP/DATE types + temporal name heuristics |

### L1/L2/L3 gradient

- **L1 (Analytics):** Moderate tolerance. Humans compensate for missing context.
- **L2 (RAG):** Low tolerance. Model has no tribal knowledge; meaning must be colocated.
- **L3 (Training):** Very low tolerance. Ambiguous semantics propagate into learned representations.

### Dropped/deferred

- `schema_type_coverage` — dropped for simplicity in v1 (hard to threshold without being opinionated about when VARCHAR is wrong).
- `column_description_coverage`, `table_description_coverage` — subsumed by `semantic_model_coverage` (a proper semantic model defines business meaning).
- `referential_integrity` — belongs in Clean (whether data violates constraints, not whether constraints exist).
- `not_null_constraint_coverage` — deferred; can add later.
- `staleness_metadata` — belongs in Current (Factor 3).

---

## Implementation plan

### Step 1: Fix suite registration (extend, not replace)

Change `register_suite` in `agent/platform/registry.py` to extend when a suite name already exists, so multiple factor files can contribute tests to `common_snowflake`.

### Step 2: Implement Snowflake Contextual tests

Create `agent/suites/contextual_snowflake.py` with four tests:

1. **`primary_key_defined`** — target_type: `table`. For each table in inventory, check if a PK is declared. Metric: fraction of tables with PK.
2. **`semantic_model_coverage`** — target_type: `platform`. Query semantic views; compare against inventory tables. Metric: fraction of assessed tables covered by a semantic model.
3. **`foreign_key_coverage`** — target_type: `table`. For each table in inventory, check if FKs are declared. Metric: fraction of tables with at least one FK.
4. **`temporal_scope_present`** — target_type: `table`. For each table, check if at least one column has TIMESTAMP/DATE type or temporal name pattern. Metric: fraction of tables with temporal columns.

All register into `common_snowflake` (appending to existing Clean tests).

### Step 3: Thresholds

Add real thresholds to `agent/thresholds.py` for the four new keys. These are coverage metrics (higher is better), so resolve the threshold direction issue:

- Option A: Add a `direction` field to threshold config (`gte` or `lte`). Update `passes()` to check direction.
- Option B: Invert metrics (measure "fraction without" so lower is still better). Keeps `passes()` simple but makes metric names confusing.
- **Recommendation:** Option A. Cleaner semantics; one-time change to `passes()`.

Proposed thresholds (coverage, 0–1):

| Key | L1 | L2 | L3 |
|-----|----|----|-----|
| `primary_key_defined` | 0.5 | 0.8 | 0.95 |
| `semantic_model_coverage` | 0.2 | 0.5 | 0.8 |
| `foreign_key_coverage` | 0.3 | 0.6 | 0.8 |
| `temporal_scope_present` | 0.3 | 0.6 | 0.9 |

### Step 4: Column scoping in run.py

Update `_column_matches_requirement` in `agent/run.py` if any Contextual tests use column-level expansion. Most Contextual tests are table- or platform-level, so this may be minimal.

### Step 5: Survey questions

Update `agent/suites/questions/common_snowflake.yaml` with Contextual-specific questions (replace or supplement the current single Contextual question). Candidates:
- "Is there a documented naming convention for tables and columns?"
- "Who maintains the semantic model or business definitions?"
- "Are there controlled vocabularies or enumerations for categorical columns?"

### Step 6: Coverage doc

Update `docs/coverage/README.md` with Contextual section for Snowflake.

### Step 7: Verify end-to-end

Run `aird assess -c "snowflake://..." -o markdown` and confirm:
- Report shows both Clean and Contextual results
- Contextual tests produce real pass/fail at L1/L2/L3
- Survey questions (if `--survey`) include Contextual

### Step 8: Cortex Code CLI validation

Run the full agentic workflow through Cortex Code CLI:
- Agent reads AGENTS.md → follows skills → connects → discovers → assesses → interprets
- Confirm no friction points specific to Cortex Code CLI
- Document any issues or fixes needed

---

## Open questions

1. **Semantic model coverage mechanism.** How does the test determine which assessed tables are "covered" by a semantic view? Approach: query `DESCRIBE SEMANTIC VIEW` for each semantic view in scope, extract base table names, compare against inventory. If a table appears as a base table in any semantic view, it's covered. Need to handle: semantic views in different schemas, tables referenced across databases.

2. **`SHOW` commands and the executor.** The read-only executor validates SQL prefixes. `SHOW PRIMARY KEYS`, `SHOW IMPORTED KEYS`, and `SHOW SEMANTIC VIEWS` all start with `SHOW` which is already allowed. But `SHOW` returns results differently than `SELECT` on some platforms — need to confirm DuckDB adapter isn't affected (Contextual tests are Snowflake-only for now).

3. **Threshold direction rollout.** When we add `direction: "gte"` to thresholds, existing Clean thresholds (all `lte`) must not break. Default direction should be `lte` for backward compatibility.

---

## After Contextual

Next factor: **Current (Factor 3)** — freshness, staleness, refresh cadence. Then **Compliant (Factor 5)** — governance, access control, masking. Same pattern: factor doc → Snowflake tests → thresholds → verify.
