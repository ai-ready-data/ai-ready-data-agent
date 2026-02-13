# Workflow: Remediate

Guide for generating and presenting remediation recommendations.

## Purpose

For each failed requirement the user wants to fix:
1. Explain why it matters
2. Generate concrete SQL fixes
3. Present for user approval (never execute without consent)

## Remediation Workflow

### 1. Identify Failures

From assessment results, list requirements that failed:
```
Failed Requirements:
- pk_coverage: 0.80 (need >=0.90)
- comment_coverage: 0.45 (need >=0.70)
- change_tracking_coverage: 0.60 (need >=0.70)
```

### 2. Load Factor Skills

For each failure, load the corresponding factor skill from `skills/factors/`:
- Clean failures -> [../factors/0-clean.md](../factors/0-clean.md)
- Contextual failures -> [../factors/1-contextual.md](../factors/1-contextual.md)
- Consumable failures -> [../factors/2-consumable.md](../factors/2-consumable.md)
- Current failures -> [../factors/3-current.md](../factors/3-current.md)
- Correlated failures -> [../factors/4-correlated.md](../factors/4-correlated.md)
- Compliant failures -> [../factors/5-compliant.md](../factors/5-compliant.md)

Each factor file contains a **Remediation** section with SQL patterns.

### 3. Diagnose Specifics

Run diagnostic queries to find exact gaps:
```sql
-- Which tables lack PKs?
SELECT t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.table_constraints tc 
    ON t.table_name = tc.table_name 
    AND tc.constraint_type = 'PRIMARY KEY'
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
  AND tc.constraint_name IS NULL;
```

### 4. Generate Fix SQL

Substitute the user's actual schema, table, and column names into the remediation patterns from the factor skill. Present:

- **What** — Requirement and why it failed (brief).
- **Fix** — Concrete SQL for their environment.
- **Impact** — Expected improvement (e.g. "Improves pk_coverage from 0.80 to 1.00").
- **Review** — Remind them to review and run changes themselves.

### 5. Present for Approval

```
## Recommended Fixes

### 1. Add Primary Keys (2 tables)

**Impact:** Improves pk_coverage from 0.80 -> 1.00

```sql
ALTER TABLE {database}.{schema}.ORDERS 
ADD CONSTRAINT orders_pk PRIMARY KEY (order_id);

ALTER TABLE {database}.{schema}.EVENTS 
ADD CONSTRAINT events_pk PRIMARY KEY (event_id);
```

**Review and run?** (I will not execute these without your approval)
```

Group by effort if helpful (quick wins vs larger changes).

**STOP:** Do not execute any suggested SQL or commands without explicit user approval.

## Quick Fix Reference

### Clean
```sql
-- Fill nulls
UPDATE {schema}.{table} SET {column} = '{default}' WHERE {column} IS NULL;

-- Deduplicate
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT * FROM {schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {pk} ORDER BY {ts} DESC) = 1;
```

### Contextual
```sql
-- Add PK
ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({column});

-- Add comments
COMMENT ON TABLE {schema}.{table} IS '{description}';
COMMENT ON COLUMN {schema}.{table}.{column} IS '{description}';

-- AI-generate description (Snowflake Cortex)
SELECT SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC('{db}', '{schema}', '{table}');
```

### Consumable
```sql
ALTER TABLE {schema}.{table} CLUSTER BY ({columns});
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION;
```

### Current
```sql
ALTER TABLE {schema}.{table} SET CHANGE_TRACKING = TRUE;
CREATE STREAM {schema}.{table}_stream ON TABLE {schema}.{table};
```

### Correlated
```sql
CREATE TAG IF NOT EXISTS {schema}.data_domain 
    ALLOWED_VALUES 'customer', 'order', 'product';
ALTER TABLE {schema}.{table} SET TAG {schema}.data_domain = '{value}';
```

### Compliant
```sql
CREATE MASKING POLICY {schema}.email_mask AS (val STRING) RETURNS STRING ->
    CASE WHEN CURRENT_ROLE() IN ('ADMIN') THEN val ELSE '***@***.***' END;
ALTER TABLE {schema}.{table} MODIFY COLUMN {col} 
    SET MASKING POLICY {schema}.email_mask;
```

## Execution Rules

1. **Never execute DDL without explicit user approval**
2. **Present SQL first**, then ask "Should I run this?"
3. **One change at a time** for destructive operations
4. **Suggest backups** for data-modifying operations
5. After fixes are applied, suggest re-assessment to measure improvement

## Output

- Per-failure remediation suggestions with concrete SQL
- All suggestions marked as "for user to review and run"
- Next steps: re-assess to measure improvement
