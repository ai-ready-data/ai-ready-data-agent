# Plan: Remediation + Snowflake-Specific Templates

**Created:** 2026-02-13  
**Status:** Draft  
**Context:** ACTION-PLAN §13 — "Remediation-first: `aird fix --dry-run` + Snowflake-specific templates (primary_key, FK, temporal)"  
**Persona 0:** Data Engineer on Snowflake

---

## 1. Current State

### 1.1 Fix command
- `aird fix` loads latest (or `--id`) assessment, extracts failed results, looks up templates by requirement key
- Output: stdout (dry-run) or SQL files to `-o <dir>`
- Templates: generic SQL with `{schema}`, `{table}`, `{column}` placeholders

### 1.2 Template coverage
- **Table/column-level:** `null_rate`, `duplicate_rate` — test_id has `req|schema|table|column` or `req|schema|table`
- **Platform-level:** `primary_key_defined`, `foreign_key_coverage`, `temporal_scope_present`, `semantic_model_coverage` — test_id is just `primary_key_defined` (no schema/table)

### 1.3 Gap
- Platform-level tests return one aggregate (e.g. "60% of tables have PKs"). We don't know *which* tables lack PKs.
- Current templates use generic SQL (e.g. `SERIAL` for PostgreSQL); Snowflake uses `IDENTITY` or `AUTOINCREMENT`.
- No platform detection: same template for DuckDB and Snowflake.

---

## 2. Goals

1. **Snowflake-specific SQL** for primary_key, foreign_key, temporal — Persona 0 focus
2. **Platform-level remediation** — handle aggregate failures by using report inventory
3. **Actionable output** — user can copy-paste and run; no manual placeholder filling where avoidable

---

## 3. Platform-Level Remediation Strategy

**Problem:** `primary_key_defined` fails → we know "X% of tables lack PKs" but not which tables.

**Options:**

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | One suggestion per table in inventory | Simple; covers all tables in scope | May suggest PK for tables that already have one |
| B | Fix command accepts `-c` and runs discovery query | Accurate: only tables without PKs | Adds connection dependency to fix; more complex |
| C | Output discovery query + template; user runs discovery first | No connection in fix; self-contained | Two-step; user must run query, then apply template |

**Recommendation:** **Option A for MVP.** Use report `inventory.tables` to generate one suggestion per table. Add a header: "Platform test failed. These tables were in scope. Run `SHOW PRIMARY KEYS IN SCHEMA <schema>` to confirm which need PKs." For tables we can't know, we output a template with a discovery query as comment, then the ALTER template. User reviews and applies only to tables that need it.

**Refinement:** If report includes `connection_fingerprint` with `snowflake://`, we can also output a Snowflake-specific discovery query:

```sql
-- Find tables without primary keys (Snowflake)
SELECT t.table_schema, t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.table_constraints pk
  ON t.table_schema = pk.table_schema AND t.table_name = pk.table_name
  AND pk.constraint_type = 'PRIMARY KEY'
WHERE UPPER(t.table_schema) NOT IN ('INFORMATION_SCHEMA')
  AND t.table_type = 'BASE TABLE'
  AND pk.table_name IS NULL;
```

---

## 4. Platform Detection

**Source:** Report `connection_fingerprint` (e.g. `snowflake://...` or `duckdb://...`).

**Logic:**
- If `connection_fingerprint` starts with `snowflake` → use Snowflake templates
- Else → use generic/fallback templates (current behavior)

**Implementation:** Add `platform` to template lookup. Template key becomes `(requirement, platform)` or we have `snowflake_primary_key_defined` as a variant. Simpler: one template dict per platform, merge with fallback to generic.

---

## 5. Snowflake-Specific Templates

### 5.1 primary_key_defined

**Snowflake syntax:**
- `ALTER TABLE x ADD CONSTRAINT pk_name PRIMARY KEY (col1, col2)` — same as standard
- Surrogate key: `ALTER TABLE x ADD COLUMN id NUMBER AUTOINCREMENT` or `IDENTITY` — Snowflake uses `AUTOINCREMENT` or `IDENTITY(1,1)`

**Template (per-table, from inventory):**

```sql
-- Add primary key to schema.table
-- Option 1: Use existing column (e.g. id)
ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_{table} PRIMARY KEY (id);

-- Option 2: Add surrogate key (Snowflake)
ALTER TABLE {schema}.{table} ADD COLUMN id NUMBER AUTOINCREMENT;
ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_{table} PRIMARY KEY (id);
```

**Platform-level handling:** When test_id has no schema/table, iterate `inventory.tables` and emit one block per table. Group under a single "primary_key_defined" suggestion with header + discovery query.

### 5.2 foreign_key_coverage

**Snowflake syntax:** Standard `FOREIGN KEY (col) REFERENCES ref_schema.ref_table(ref_col)`.

**Template (per-table):**

```sql
-- Add foreign key to schema.table (adjust ref_table and columns)
ALTER TABLE {schema}.{table}
ADD CONSTRAINT fk_{table}_<ref> FOREIGN KEY (ref_column) REFERENCES <ref_schema>.<ref_table>(id);
```

**Note:** We don't know the relationship. Template is generic; user fills in ref_table, ref_column. Could add a discovery query for "tables with no FK" if needed.

### 5.3 temporal_scope_present

**Snowflake syntax:** `TIMESTAMP_NTZ` or `TIMESTAMP_LTZ` for created_at/updated_at.

**Template (per-table):**

```sql
-- Add temporal columns for freshness tracking (Snowflake)
ALTER TABLE {schema}.{table} ADD COLUMN created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE {schema}.{table} ADD COLUMN updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
```

### 5.4 Clean factor (Snowflake variants)

**null_rate:** Snowflake uses `COUNT_IF(column IS NULL)` — current template uses standard `UPDATE ... SET ... WHERE ... IS NULL` which works.

**duplicate_rate:** Snowflake has no `ctid`; use `ROW_NUMBER() OVER (PARTITION BY ...)` for dedup. Add Snowflake-specific option:

```sql
-- Snowflake: Create deduplicated view
CREATE OR REPLACE VIEW {schema}.{table}_deduped AS
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY <key_cols> ORDER BY updated_at DESC) AS rn
  FROM {schema}.{table}
) WHERE rn = 1;
```

---

## 6. Template Registry Shape

**Current:** `REMEDIATION_TEMPLATES[requirement] = (description, sql_template)`

**Proposed:** Platform-aware. Two approaches:

**A. Nested dict:**
```python
REMEDIATION_TEMPLATES = {
    "primary_key_defined": {
        "snowflake": (desc, sql),
        "default": (desc, sql),
    },
}
```

**B. Key suffix:**
```python
REMEDIATION_TEMPLATES = {
    "primary_key_defined": (desc, sql),           # default
    "primary_key_defined.snowflake": (desc, sql), # override
}
```

**Recommendation:** **A** — clearer, easier to add platforms. Lookup: `templates.get(requirement, {}).get(platform) or templates.get(requirement, {}).get("default")`.

---

## 7. Generator Changes

1. **Platform detection:** Parse `report["connection_fingerprint"]` → `platform` (snowflake, duckdb, sqlite, generic)
2. **Platform-level expansion:** For results with `target_type == "platform"` and no schema/table in test_id:
   - Get tables from `report.get("inventory", {}).get("tables", [])`
   - For each table, generate one suggestion using template with that table's schema/table
   - Prepend discovery query (when available) as comment
3. **Template lookup:** `get_template(requirement, platform)` → prefer platform-specific, fallback to default
4. **Output grouping:** Optionally group platform-level suggestions (e.g. "12 tables need primary keys") with expandable detail

---

## 8. File Output Format

**Current:** One `.sql` file per suggestion: `01_null_rate_products.sql`, `02_duplicate_rate_products.sql`

**Platform-level:** One file per requirement covering all tables, or one per table? 

**Recommendation:** One file per requirement for platform-level (e.g. `01_primary_key_defined.sql`) containing:
- Discovery query (commented)
- One block per table from inventory

For table-level (null_rate, duplicate_rate), keep one file per failed test.

---

## 9. Tasks (Implementation Order)

- [ ] **T1** Add platform detection to generator (parse connection_fingerprint)
- [ ] **T2** Add platform-aware template lookup (nested dict, snowflake + default)
- [ ] **T3** Implement platform-level expansion: use inventory.tables when test_id has no schema/table
- [ ] **T4** Add Snowflake templates for primary_key_defined, foreign_key_coverage, temporal_scope_present
- [ ] **T5** Add Snowflake variant for duplicate_rate (ROW_NUMBER dedup)
- [ ] **T6** Update fix command output: group platform-level suggestions; discovery query in header
- [ ] **T7** Tests: Snowflake report → fix → verify Snowflake SQL in output

---

## 10. Out of Scope (This Plan)

- dbt schema.yml export — see `plan-dbt-integration.md`
- Per-table assessment for platform requirements (would require assessment changes)
- Fix command with `-c` to run discovery queries live

---

*Next: plan-dbt-integration.md*
