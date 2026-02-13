# Workflow: Discover

Guide for discovering and scoping data assets before assessment.

## Purpose

Before running an assessment, understand:
1. What databases/schemas are available
2. What tables exist and their sizes
3. What the user wants to assess (scope confirmation)

---

## Phase 1: Gather Context (Pre-Connect)

Ask in order of priority. Use progressive disclosure (1-2 questions at a time).

1. **Platform (first):** "What database platform are you using? (e.g. DuckDB, SQLite, Snowflake, PostgreSQL.)" This determines which SQL dialect and platform skill to load.

2. **Target workload:** "What are you building toward: analytics dashboards (L1), RAG/search (L2), or model training (L3)?" Drives which threshold level to emphasize and how to prioritize failures.

3. **Data products:** "Do you organize your data into data products (e.g. customer 360, feature store, event pipeline)? If so, which products should we assess?" Data products are named groups of related tables assessed together.

4. **Scope:** "Are there schemas we should skip? (e.g. staging, scratch, test.)"

5. **Infrastructure:** "Do you use dbt, a data catalog, OpenTelemetry, or Iceberg?" Helps explain what can or can't be assessed.

6. **Pain points:** "What prompted this assessment? Any known issues?" Helps validate that the assessment catches what matters.

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

Then ask:

1. **Confirm connection**: "I see you're connected to {database}. Which schema should I assess?"
2. **Scope:** "I found {N} tables in {schema}. Should I assess all of them, or exclude any?" (e.g. staging, scratch)
3. **Criticality:** "Which tables are most critical for your AI workload?" (Optional; helps prioritize in interpretation.)
4. **Confirm workload level**: "What AI workload are you targeting? L1 (BI/Analytics), L2 (RAG/Retrieval), L3 (ML Training)?"
5. **Confirm factors**: "Should I assess all 6 factors, or focus on specific ones?"

**STOP:** Get explicit confirmation before running the assessment.

## Output

- User-confirmed scope (schemas, tables, exclusions)
- Target workload level (L1/L2/L3)
- Factor scope (all or specific)
- Ready to proceed to [assess.md](assess.md)
