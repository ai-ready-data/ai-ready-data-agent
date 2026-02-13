# Workflow: Discover

Guide for discovering and scoping data assets before assessment.

## Purpose

Before running an assessment, understand:
1. What databases/schemas are available
2. What tables exist and their sizes
3. What the user wants to assess (scope confirmation)

## Question Manifest

All discovery questions are defined in [definitions/questions.yaml](../../definitions/questions.yaml). That file is the single source of truth for question text, answer types, options, and guidance. This workflow describes *when* and *how* to ask them.

---

## Phase 1: Gather Context (Pre-Connect)

Ask the `pre-connect` questions from [definitions/questions.yaml](../../definitions/questions.yaml) in priority order. Use progressive disclosure (1-2 questions at a time).

1. **`platform`** (required, ask first): "What database platform are you using?" Determines which SQL dialect and platform skill to load.

2. **`target_workload`** (required): "What are you building toward: analytics dashboards (L1), RAG/search (L2), or model training (L3)?" Drives which threshold level to apply.

3. **`data_products`**: "Do you organize your data into data products (e.g. customer 360, feature store, event pipeline)? If so, which products should we assess?" Data products are named groups of related tables assessed together.

4. **`excluded_schemas`**: "Are there schemas we should skip? (e.g. staging, scratch, test.)"

5. **`infrastructure_tools`**: "Do you use dbt, a data catalog, OpenTelemetry, or Iceberg?" Helps explain what can or can't be assessed.

6. **`pain_points`**: "What prompted this assessment? Any known issues?" Helps validate that the assessment catches what matters.

**STOP:** Wait for user responses before proceeding.

---

## Phase 2: Discovery Queries

### List Databases
```sql
SHOW DATABASES;
```

### List Schemas in Database
```sql
SHOW SCHEMAS IN DATABASE {database};
```

### List Tables with Summary
```sql
SELECT 
    table_name,
    table_type,
    row_count,
    bytes / (1024*1024) AS size_mb,
    comment,
    last_altered
FROM information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_type, row_count DESC;
```

### Quick Health Summary
```sql
SELECT
    t.table_name,
    t.row_count,
    t.table_type,
    t.change_tracking AS cdc_enabled,
    t.clustering_key IS NOT NULL AS is_clustered,
    t.search_optimization AS search_opt,
    t.comment IS NOT NULL AND t.comment != '' AS has_comment,
    COUNT(c.column_name) AS column_count
FROM information_schema.tables t
LEFT JOIN information_schema.columns c 
    ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE t.table_schema = '{schema}'
  AND t.table_type IN ('BASE TABLE', 'DYNAMIC TABLE')
GROUP BY t.table_name, t.row_count, t.table_type, 
         t.change_tracking, t.clustering_key, t.search_optimization, t.comment
ORDER BY t.row_count DESC;
```

---

## Phase 3: Scope Confirmation (Post-Discovery)

Present discovery results as a table:

```
| Table | Rows | Type | CDC | Clustered | Comments |
|-------|------|------|-----|-----------|----------|
| CUSTOMERS | 10,000 | BASE | ON | Yes | Yes |
| ORDERS | 500,000 | BASE | OFF | Yes | No |
| EVENTS | 2,000,000 | BASE | OFF | No | No |
```

Then ask the `post-discovery` questions from [definitions/questions.yaml](../../definitions/questions.yaml) in priority order:

1. **`database`** (required): "I see you're connected to {database}. Which database should I assess?"
2. **`schemas`** (required): "Which schemas should I assess?"
3. **`tables`**: "I found {N} tables in {schema}. Should I assess all of them, or exclude any?"
4. **`critical_tables`**: "Which tables are most critical for your AI workload?" (Optional; helps prioritize in interpretation.)
5. **`factor_scope`** (required): "Should I assess all 6 factors, or focus on specific ones?"

**STOP:** Get explicit confirmation before running the assessment.

## Phase 4: Save Context

After the user confirms scope, persist all answers to a context file. This makes the assessment repeatable and diffable.

**File:** `projects/<project-name>/context.yaml` — one context file per project. See [project structure spec](../../docs/specs/project-structure-spec.md) for directory conventions. If no project name is established, ask the user for a short name (e.g. `customer-360-prod`) or derive one from the database name.

**Schema:** [docs/specs/context-spec.md](../../docs/specs/context-spec.md). Keys match `answer_title` values from [definitions/questions.yaml](../../definitions/questions.yaml).

**Sample:** [definitions/context-sample.yaml](../../definitions/context-sample.yaml) and [projects/sample/context.yaml](../../projects/sample/context.yaml).

**Instructions for the agent:**

1. Collect all answers from Phase 1 and Phase 3
2. Add metadata: `created_at` (ISO 8601 UTC), `created_by` (agent name)
3. Write to `context.yaml` using YAML format
4. Omit optional keys the user didn't provide (don't write `null`)
5. Store `target_workload` as short name only (`L1`, `L2`, `L3`)
6. Create the project directory if it doesn't exist: `projects/<project-name>/reports/` and `projects/<project-name>/remediation/`
7. Confirm the file was saved: "Context saved to `projects/<project-name>/context.yaml`. You can re-run this assessment later with the same scope."

**Validation before proceeding:** All required fields must be present: `platform`, `target_workload`, `database`, `schemas`, `factor_scope`. If any are missing, ask the user before continuing.

---

## Output

- Saved `projects/<project-name>/context.yaml` with user-confirmed configuration
- User-confirmed scope (database, schemas, tables, exclusions)
- Target workload level (L1/L2/L3)
- Factor scope (all or specific)
- Ready to proceed to [assess.md](assess.md)
