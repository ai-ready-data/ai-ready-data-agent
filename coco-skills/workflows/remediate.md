# Workflow: Remediate

Guide for generating and presenting remediation recommendations.

## Purpose

For each failed requirement:
1. Explain why it matters
2. Generate concrete SQL fixes
3. Present for user approval (never execute without consent)

## Remediation Sources

Each factor skill references a remediation document:
- `/docs/remediation/clean.md`
- `/docs/remediation/contextual.md`
- `/docs/remediation/consumable.md`
- `/docs/remediation/current.md`
- `/docs/remediation/correlated.md`
- `/docs/remediation/compliant.md`

Read the relevant file for detailed fix patterns.

## Remediation Workflow

### 1. Identify Failures
From assessment results, list requirements that failed:
```
Failed Requirements:
- pk_coverage: 0.80 (need ≥0.90)
- comment_coverage: 0.45 (need ≥0.70)
- change_tracking_coverage: 0.60 (need ≥0.70)
```

### 2. Diagnose Specifics
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

### 3. Generate Fix SQL
For each gap, generate specific SQL:
```sql
-- Add PK to ORDERS table
ALTER TABLE {database}.{schema}.ORDERS 
ADD CONSTRAINT orders_pk PRIMARY KEY (order_id);
```

### 4. Present for Approval
```
## Recommended Fixes

### 1. Add Primary Keys (2 tables)

**Impact:** Improves pk_coverage from 0.80 → 1.00

```sql
-- Table: ORDERS (detected likely PK: order_id)
ALTER TABLE {database}.{schema}.ORDERS 
ADD CONSTRAINT orders_pk PRIMARY KEY (order_id);

-- Table: EVENTS (detected likely PK: event_id)
ALTER TABLE {database}.{schema}.EVENTS 
ADD CONSTRAINT events_pk PRIMARY KEY (event_id);
```

**Review and run?** (I will not execute these without your approval)
```

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
-- Add clustering
ALTER TABLE {schema}.{table} CLUSTER BY ({columns});

-- Enable search optimization
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION;
```

### Current
```sql
-- Enable change tracking
ALTER TABLE {schema}.{table} SET CHANGE_TRACKING = TRUE;

-- Create stream
CREATE STREAM {schema}.{table}_stream ON TABLE {schema}.{table};

-- Convert to dynamic table
CREATE DYNAMIC TABLE {schema}.{table}_dynamic
TARGET_LAG = '1 hour' WAREHOUSE = {wh}
AS SELECT * FROM {source};
```

### Correlated
```sql
-- Create and apply tags
CREATE TAG IF NOT EXISTS {schema}.data_domain 
    ALLOWED_VALUES 'customer', 'order', 'product';
ALTER TABLE {schema}.{table} SET TAG {schema}.data_domain = '{value}';
```

### Compliant
```sql
-- Create masking policy
CREATE MASKING POLICY {schema}.email_mask AS (val STRING) RETURNS STRING ->
    CASE WHEN CURRENT_ROLE() IN ('ADMIN') THEN val ELSE '***@***.***' END;

-- Apply masking
ALTER TABLE {schema}.{table} MODIFY COLUMN {col} 
    SET MASKING POLICY {schema}.email_mask;

-- Create row access policy
CREATE ROW ACCESS POLICY {schema}.team_rap AS (team VARCHAR) RETURNS BOOLEAN ->
    CURRENT_ROLE() = 'ADMIN' OR team = CURRENT_USER();
```

## Execution Rules

1. **Never execute DDL without explicit user approval**
2. **Present SQL first**, then ask "Should I run this?"
3. **One change at a time** for destructive operations
4. **Verify before dropping** — show what will be affected
5. **Suggest backups** for data-modifying operations

## Batch Remediation

For multiple fixes of the same type, present as a batch:
```sql
-- Enable change tracking on all base tables
ALTER TABLE {schema}.CUSTOMERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.PRODUCTS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.EVENTS SET CHANGE_TRACKING = TRUE;
```

User can approve all or select specific statements.
