# Workflow: Assess

Guide for executing factor assessments.

## Purpose

Run SQL queries to measure each requirement, recording results for interpretation.

## Assessment Execution Pattern

For each factor in scope:

### 1. Load Factor Skill
Read the corresponding `/coco-skills/factors/{N}-{factor}.md` file.

### 2. Execute Assessment Queries
For each requirement in the factor:
```
snowflake_sql_execute(sql="{query}", description="Assess {requirement}")
```

### 3. Record Results
Track results in this structure:
```
Factor: {name}
├── {requirement_1}: {value} (threshold: {L1/L2/L3})
├── {requirement_2}: {value} (threshold: {L1/L2/L3})
└── {requirement_N}: {value} (threshold: {L1/L2/L3})
```

## Full Assessment SQL (Snowflake)

Run this comprehensive query to gather most metrics in one pass:

```sql
WITH table_stats AS (
    SELECT 
        COUNT(*) AS total_tables,
        COUNT_IF(change_tracking = 'ON') AS cdc_tables,
        COUNT_IF(clustering_key IS NOT NULL) AS clustered_tables,
        COUNT_IF(search_optimization = 'ON') AS search_opt_tables,
        COUNT_IF(comment IS NOT NULL AND comment != '') AS commented_tables
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
column_stats AS (
    SELECT 
        COUNT(*) AS total_columns,
        COUNT_IF(c.comment IS NOT NULL AND c.comment != '') AS commented_columns
    FROM information_schema.columns c
    JOIN information_schema.tables t 
        ON c.table_name = t.table_name AND c.table_schema = t.table_schema
    WHERE c.table_schema = '{schema}'
      AND t.table_type = 'BASE TABLE'
),
pk_stats AS (
    SELECT COUNT(DISTINCT table_name) AS tables_with_pk
    FROM information_schema.table_constraints
    WHERE table_schema = '{schema}'
      AND constraint_type = 'PRIMARY KEY'
),
fk_stats AS (
    SELECT COUNT(DISTINCT table_name) AS tables_with_fk
    FROM information_schema.table_constraints
    WHERE table_schema = '{schema}'
      AND constraint_type = 'FOREIGN KEY'
),
stream_stats AS (
    SELECT COUNT(DISTINCT source_name) AS tables_with_streams
    FROM information_schema.streams
    WHERE table_schema = '{schema}'
      AND stale = 'FALSE'
),
dynamic_stats AS (
    SELECT COUNT(*) AS dynamic_tables
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'DYNAMIC TABLE'
)
SELECT
    -- Contextual
    pk_stats.tables_with_pk::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS pk_coverage,
    fk_stats.tables_with_fk::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS fk_coverage,
    column_stats.commented_columns::FLOAT / NULLIF(column_stats.total_columns::FLOAT, 0) AS comment_coverage,
    table_stats.commented_tables::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS table_comment_coverage,
    -- Consumable
    table_stats.clustered_tables::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS clustering_coverage,
    table_stats.search_opt_tables::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS search_optimization_coverage,
    -- Current
    table_stats.cdc_tables::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS change_tracking_coverage,
    stream_stats.tables_with_streams::FLOAT / NULLIF(table_stats.total_tables::FLOAT, 0) AS stream_coverage,
    dynamic_stats.dynamic_tables::FLOAT / NULLIF((
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = '{schema}' AND table_type IN ('VIEW', 'DYNAMIC TABLE')
    )::FLOAT, 0) AS dynamic_table_coverage,
    -- Metadata
    table_stats.total_tables,
    column_stats.total_columns
FROM table_stats, column_stats, pk_stats, fk_stats, stream_stats, dynamic_stats;
```

## Tag & Policy Assessment (Separate Query)

Requires account_usage access:
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
),
tagged_tables AS (
    SELECT COUNT(DISTINCT object_name) AS cnt
    FROM snowflake.account_usage.tag_references
    WHERE object_schema = '{schema}' AND domain = 'TABLE' AND deleted IS NULL
),
rap_tables AS (
    SELECT COUNT(DISTINCT ref_entity_name) AS cnt
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}' AND policy_kind = 'ROW_ACCESS_POLICY'
),
masked_columns AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}' AND policy_kind = 'MASKING_POLICY'
)
SELECT
    tagged_tables.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS object_tag_coverage,
    rap_tables.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS row_access_policy_coverage,
    masked_columns.cnt AS masked_column_count
FROM table_count, tagged_tables, rap_tables, masked_columns;
```

## Per-Table Data Quality (Clean Factor)

Run per table for accurate null/duplicate rates:
```sql
-- Replace {table} with actual table name
SELECT
    '{table}' AS table_name,
    (SELECT COUNT(*) FROM {schema}.{table}) AS row_count,
    (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM {schema}.{table})) AS distinct_count
```

## Notes

- **Batch where possible**: Use CTEs to minimize round trips
- **Handle permissions**: Tag/lineage queries may fail without account_usage access
- **Skip expensive queries**: For very large tables, sample or skip full duplicate checks
