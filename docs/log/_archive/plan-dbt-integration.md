# Plan: dbt Integration

**Created:** 2026-02-13  
**Status:** Draft  
**Context:** ACTION-PLAN §8 (remediation), §13 (priorities); roadmap "Auto-detection from dbt profiles.yml"  
**Persona 0:** Data Engineer on Snowflake (typically uses dbt)

---

## 1. Goals

1. **Connection from dbt** — Use dbt `profiles.yml` so Persona 0 doesn't re-enter credentials
2. **Export to dbt tests** — Write `schema.yml` (or equivalent) so failed requirements become dbt tests they can run in their pipeline
3. **dbt-ready remediation** — Fix output includes dbt macro syntax where applicable (e.g. `generate_surrogate_key`, `unique_combination_of_columns`)

---

## 2. Scope (In / Out)

**In scope:**
- `aird assess -c dbt://profile_name` or `--dbt-profile profile_name` — resolve connection from profiles.yml
- `aird fix -o ./dbt --format dbt` — export as dbt schema.yml (models + tests)
- Remediation templates: add dbt macro variants (e.g. for surrogate keys)


**Out of scope (for now):**
- Running dbt tests from aird (we assess, we don't run dbt)
- dbt Cloud / dbt Mesh integration
- Parsing dbt project structure (models/, sources) — we use our own discovery

---

## 3. Connection from profiles.yml

**Assumption:** The dbt project targets Snowflake. We only resolve Snowflake outputs from profiles.yml.

### 3.1 profiles.yml location and format

- **Location:** `~/.dbt/profiles.yml` or `DBT_PROFILES_DIR` env
- **Structure:** YAML with `profile_name` → `targets` → `outputs` (dev, prod, etc.)
- **Snowflake output:** `type: snowflake`, `account`, `user`, `database`, `warehouse`, `schema`, `role`, auth fields

### 3.2 Connection string derivation

**Flag** `aird assess --dbt-profile my_project --dbt-target prod`
- Same resolution logic; outputs `snowflake://...` internally
- No new scheme; explicit flag


### 3.3 Implementation tasks

- [ ] **T1** Add `dbt` to `_KNOWN_SCHEMES` in cli.py
- [ ] **T2** Create `agent/platform/dbt_adapter.py` (or connection resolver):
  - `resolve_dbt_connection(profile: str, target: str | None) -> str`
  - Load `~/.dbt/profiles.yml` (or `DBT_PROFILES_DIR`)
  - Parse YAML, find profile → target
  - Map Snowflake output to `snowflake://...` connection string
- [ ] **T3** Handle auth: `password` in profiles is plain text; `private_key_path` requires key file. Document: aird reads profiles; user must ensure profiles.yml is secure.
- [ ] **T4** Snowflake only; non-Snowflake profiles output a clear error

---

## 4. Export to dbt Test Suite (schema.yml)

### 4.1 Requirement → dbt test mapping

| AI-Ready requirement | dbt test | Level | Notes |
|----------------------|---------|-------|-------|
| `null_rate` | `not_null` | column | dbt built-in |
| `duplicate_rate` | `unique` | column(s) or model | dbt built-in; may need composite |
| `primary_key_defined` | `unique` + optional custom | model | unique on PK column(s) |
| `foreign_key_coverage` | `relationships` | column | dbt built-in; ref to parent |
| `temporal_scope_present` | — | — | No direct dbt test; custom SQL or skip |
| `format_inconsistency_rate` | custom | column | Custom test or `accepted_values` |
| `type_inconsistency_rate` | custom | column | Custom SQL test |

### 4.2 schema.yml shape

dbt expects:

```yaml
models:
  - name: customers
    description: ""
    columns:
      - name: id
        data_tests:
          - unique
          - not_null
      - name: email
        data_tests:
          - not_null
```

For failed tests only, we generate tests that correspond to what failed. We don't create full model definitions — we append to existing or create minimal stubs.

### 4.3 Export modes

**A. Append to existing schema.yml** — Risky; we'd need to parse and merge. Complex.

**B. Generate new schema.yml** — Write `aird_schema.yml` or user-specified path. User copies tests into their schema.yml or includes our file.

**C. Generate patch file** — Output YAML fragment (models/columns/tests) that user can paste. Simpler.

**Recommendation:** **B** — Generate `aird_generated.yml` (or `-o ./dbt/models/aird_generated.yml`). Document: "Include this in your dbt project; add to `models:` in your schema or use `{{ ref('aird_generated') }}` if we emit a models block." Actually, dbt schema files just need to be in the right place — we emit a standalone schema file that defines tests for the tables we assessed. User places it in `models/` or a subdir.

### 4.4 Table name mapping

Our inventory has `schema.table`. dbt models are usually named by table (or schema_table). We need a mapping:
- Option: `database.schema.table` → dbt `schema.table` or `table` (configurable)
- For Snowflake + dbt: often `raw.schema.table` or `analytics.table`; model name = table name or `schema_table`

**Simplest:** Use `table` as model name, add `schema` in config if needed. Or use `schema_table` as model name. Document that user may need to adjust model names to match their dbt project.

### 4.5 Implementation tasks

- [ ] **T5** Add `aird fix --format dbt` (or `-f dbt`) and `-o` for output path
- [ ] **T6** Implement `export_to_dbt_schema(report, suggestions, output_path)`:
  - Group suggestions by table (schema, table)
  - For each table, build `columns` with `data_tests` from requirement mapping
  - Emit YAML with `models:` list
- [ ] **T7** Requirement → dbt test mapping table (code)
- [ ] **T8** Handle tables not in dbt project: emit anyway; user adds models or ignores

---

## 5. dbt Macros in Remediation

### 5.1 Use cases

- **Surrogate key:** `{{ dbt_utils.generate_surrogate_key(['col1','col2']) }}` — for primary_key_defined
- **Unique combination:** `dbt_utils.unique_combination_of_columns` — for duplicate_rate
- **Not null:** dbt has built-in; we could mention `dbt test --select model_name` for null_rate

### 5.2 Template variants

Add `format` or `variant` to templates: `sql` (raw SQL) vs `dbt` (Jinja + macros).

Example for `primary_key_defined` (dbt variant):

```sql
-- In dbt model: add surrogate key
{{ config(materialized='table') }}
SELECT
  {{ dbt_utils.generate_surrogate_key(['email','created_at']) }} AS id,
  *
FROM {{ source('raw','customers') }}
```

Or for incremental:

```sql
-- Add to your model's YAML under columns:
--   - name: id
--     data_tests: [unique, not_null]
```

### 5.3 Implementation

- [ ] **T9** Add `--format dbt` to fix command (alongside `--format sql` default)
- [ ] **T10** When format=dbt, use dbt template variants: macros, source/ref syntax
- [ ] **T11** Document: requires `dbt_utils` for some macros

---

## 6. CLI Changes Summary

| Change | Command | Flag / behavior |
|--------|---------|-----------------|
| dbt connection | assess, fix, discover, run | `-c dbt://profile` or `-c dbt://profile/target` |
| dbt export | fix | `-o ./dbt/models -f dbt` or `--format dbt` |
| dbt remediation | fix | `-f dbt` uses dbt macro templates |

---

## 7. Dependency on Remediation Plan

This plan depends on [plan-remediation-snowflake-templates.md](plan-remediation-snowflake-templates.md) for:
- Platform detection (Snowflake)
- Suggestion structure (per-table, per-requirement)

dbt export consumes the same suggestions; it just renders them as schema.yml instead of raw SQL.

---

## 8. Tasks (Implementation Order)

**Phase 1: Connection**
- [ ] T1–T4: dbt connection resolution from profiles.yml

**Phase 2: Export**
- [ ] T5–T8: Export to dbt schema.yml

**Phase 3: dbt remediation**
- [ ] T9–T11: dbt format for fix output (macros, refs)

---

## 9. Open Questions

- **profiles.yml and secrets:** Should we support env var overrides (e.g. `DBT_PASSWORD`) for CI?
- **dbt project root:** Should `aird fix -o .` auto-detect `dbt_project.yml` and write to `models/`?
- **Test severity:** dbt has `warn`/`error`. Map L1→warn, L2/L3→error?

---

*Depends on: plan-remediation-snowflake-templates.md*
