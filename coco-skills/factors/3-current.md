# Factor 3: Current

**Definition:** Data reflects the present state, with freshness enforced by systems rather than hoped for by humans.

## Why It Matters for AI

Stale data produces stale answers. For RAG, outdated documents surface as authoritative responses. For ML, training on yesterday's patterns misses today's drift. "Current" means freshness is measurable, tracked, and automatically maintained — not manually refreshed and crossed fingers.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `change_tracking_coverage` | Fraction of tables with change tracking enabled | gte | 0.30 | 0.70 | 0.90 |
| `stream_coverage` | Fraction of tables with active streams | gte | 0.20 | 0.50 | 0.80 |
| `data_freshness_pass_rate` | Fraction of tables meeting freshness SLA | gte | 0.70 | 0.90 | 0.99 |
| `dynamic_table_coverage` | Fraction of derived objects that are dynamic tables | gte | 0.10 | 0.30 | 0.50 |

**Direction `gte`** = higher is better. Value must be ≥ threshold to pass.

---

## Assessment SQL (Snowflake)

### change_tracking_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
tracking_enabled AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
      AND change_tracking = 'ON'
)
SELECT tracking_enabled.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, tracking_enabled;
```

### stream_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
tables_with_streams AS (
    SELECT COUNT(DISTINCT source_name) AS cnt
    FROM information_schema.streams
    WHERE table_schema = '{schema}'
      AND source_type = 'TABLE'
      AND stale = 'FALSE'
)
SELECT tables_with_streams.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, tables_with_streams;
```

### dynamic_table_coverage
```sql
WITH view_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type IN ('VIEW', 'DYNAMIC TABLE')
),
dynamic_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'DYNAMIC TABLE'
)
SELECT dynamic_count.cnt::FLOAT / NULLIF(view_count.cnt::FLOAT, 0) AS value
FROM view_count, dynamic_count;
```

### Detailed change tracking status
```sql
SELECT 
    table_name,
    change_tracking,
    last_altered,
    DATEDIFF('hour', last_altered, CURRENT_TIMESTAMP()) AS hours_since_altered
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
ORDER BY change_tracking DESC, table_name;
```

### Detailed stream status
```sql
SELECT 
    stream_name,
    source_name AS source_table,
    type AS stream_type,
    stale,
    stale_after,
    CASE WHEN stale = 'TRUE' THEN 'STALE - RECREATE' ELSE 'HEALTHY' END AS status
FROM information_schema.streams
WHERE table_schema = '{schema}'
ORDER BY stale DESC, stream_name;
```

### Dynamic table status
```sql
SELECT 
    name,
    target_lag,
    refresh_mode,
    scheduling_state,
    data_timestamp
FROM information_schema.dynamic_tables
WHERE schema_name = '{schema}'
ORDER BY name;
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)

---

## Remediation

### Enable Change Tracking
```sql
-- Enable change tracking on table
ALTER TABLE {database}.{schema}.{table} SET CHANGE_TRACKING = TRUE;

-- Batch enable for all tables
ALTER TABLE {database}.{schema}.CUSTOMERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {database}.{schema}.ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {database}.{schema}.PRODUCTS SET CHANGE_TRACKING = TRUE;
```

**Query Changes:**
```sql
-- Query changes since a point in time
SELECT * FROM {database}.{schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (TIMESTAMP => DATEADD('hour', -24, CURRENT_TIMESTAMP()));

-- Get metadata about changes
SELECT 
    *,
    METADATA$ACTION,      -- INSERT, DELETE
    METADATA$ISUPDATE,    -- TRUE if this is part of an UPDATE
    METADATA$ROW_ID       -- Unique row identifier
FROM {database}.{schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (OFFSET => -3600);  -- Last hour
```

### Create Streams
```sql
-- Create standard stream (tracks all DML)
CREATE OR REPLACE STREAM {database}.{schema}.{table}_stream 
ON TABLE {database}.{schema}.{table};

-- Create append-only stream (INSERT only, more efficient)
CREATE OR REPLACE STREAM {database}.{schema}.{table}_stream 
ON TABLE {database}.{schema}.{table}
APPEND_ONLY = TRUE;
```

**Consume Stream Changes:**
```sql
-- Query stream for pending changes
SELECT 
    *,
    METADATA$ACTION,
    METADATA$ISUPDATE,
    METADATA$ROW_ID
FROM {database}.{schema}.{table}_stream;

-- Check if stream has data
SELECT SYSTEM$STREAM_HAS_DATA('{database}.{schema}.{table}_stream');
```

**Stream + Task Pattern:**
```sql
-- Create task to process stream automatically
CREATE OR REPLACE TASK {database}.{schema}.process_{table}_changes
WAREHOUSE = {warehouse}
SCHEDULE = '5 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('{database}.{schema}.{table}_stream')
AS
INSERT INTO {database}.{schema}.{table}_history
SELECT *, CURRENT_TIMESTAMP() AS processed_at
FROM {database}.{schema}.{table}_stream;

-- Enable the task
ALTER TASK {database}.{schema}.process_{table}_changes RESUME;
```

### Convert Views to Dynamic Tables
```sql
-- Get existing view definition
SELECT GET_DDL('VIEW', '{database}.{schema}.{view_name}');

-- Create dynamic table with same query
CREATE OR REPLACE DYNAMIC TABLE {database}.{schema}.{table_name}
TARGET_LAG = '1 hour'           -- Or 'DOWNSTREAM' for real-time
WAREHOUSE = {warehouse}
AS
{view_definition_sql};

-- Drop old view if replacing
DROP VIEW IF EXISTS {database}.{schema}.{old_view_name};
```

**Dynamic Table Options:**
```sql
-- Time-based lag (refreshes at most every N time units)
CREATE DYNAMIC TABLE {database}.{schema}.{table}
TARGET_LAG = '1 hour'
WAREHOUSE = {warehouse}
AS SELECT ...;

-- Downstream lag (refreshes when upstream changes)
CREATE DYNAMIC TABLE {database}.{schema}.{table}
TARGET_LAG = 'DOWNSTREAM'
WAREHOUSE = {warehouse}
AS SELECT ...;

-- Cascading dynamic tables
CREATE DYNAMIC TABLE {database}.{schema}.base_aggregates
TARGET_LAG = '15 minutes'
WAREHOUSE = {warehouse}
AS SELECT ... FROM raw_data;

CREATE DYNAMIC TABLE {database}.{schema}.summary
TARGET_LAG = 'DOWNSTREAM'
WAREHOUSE = {warehouse}
AS SELECT ... FROM base_aggregates;
```

### Monitor Dynamic Tables
```sql
-- Check refresh history
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
    NAME => '{database}.{schema}.{table}',
    DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
));
```

---

## Execution Pattern

1. **Run change_tracking_coverage**: Check `change_tracking` in metadata
2. **Run stream_coverage**: Check `information_schema.streams`
3. **Run dynamic_table_coverage**: Check for `DYNAMIC TABLE` types
4. **Assess freshness**: Compare `last_altered` or `MAX(timestamp_col)` to SLA
5. **List gaps**: Find tables without tracking/streams, stale streams
6. **Generate fixes**: Create ALTER and CREATE statements
