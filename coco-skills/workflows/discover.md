# Workflow: Discover

Guide for discovering and scoping data assets before assessment.

## Purpose

Before running an assessment, understand:
1. What databases/schemas are available
2. What tables exist and their sizes
3. What the user wants to assess (scope confirmation)

## Discovery Queries

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
-- Single query showing key metadata for all tables
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

## Conversation Pattern

1. **Confirm connection**: "I see you're connected to {database}. Which schema should I assess?"

2. **Show what's available**: Run discovery query, present summary table

3. **Confirm scope**: "I found {N} tables in {schema}. Should I assess all of them, or specific tables?"

4. **Confirm workload level**: "What AI workload are you targeting?
   - L1: BI/Analytics (lenient thresholds)
   - L2: RAG/Retrieval (moderate thresholds)
   - L3: ML Training (strict thresholds)"

5. **Confirm factors**: "Should I assess all 6 factors, or focus on specific ones?"

## Output Format

Present discovery results as a table:

```
| Table | Rows | Type | CDC | Clustered | Comments |
|-------|------|------|-----|-----------|----------|
| CUSTOMERS | 10,000 | BASE | ON | Yes | Yes |
| ORDERS | 500,000 | BASE | OFF | Yes | No |
| EVENTS | 2,000,000 | BASE | OFF | No | No |
```

Then proceed to scope confirmation.
