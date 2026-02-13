# Current Factor Remediation

**Factor 3: Current** — Does the data reflect the present state, with freshness enforced by systems?

Reference: `/factors.md` § Current

---

## change_tracking_coverage

**Problem:** Tables lack change tracking for CDC use cases.

**Diagnosis:**
```sql
-- Check change tracking status
SELECT 
    table_name,
    change_tracking,
    CASE WHEN change_tracking = 'ON' THEN 'OK' ELSE 'NEEDS TRACKING' END AS status
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
ORDER BY change_tracking, table_name;
```

**Fix Patterns:**

```sql
-- Enable change tracking on table
ALTER TABLE {schema}.{table} SET CHANGE_TRACKING = TRUE;

-- Batch enable for all tables in schema
-- (Run as separate statements)
ALTER TABLE {schema}.CUSTOMERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.ORDER_ITEMS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.PRODUCTS SET CHANGE_TRACKING = TRUE;
ALTER TABLE {schema}.EVENTS SET CHANGE_TRACKING = TRUE;
```

**Query Changes:**
```sql
-- Query changes since a point in time
SELECT * FROM {schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (TIMESTAMP => DATEADD('hour', -24, CURRENT_TIMESTAMP()));

-- Query changes between two points
SELECT * FROM {schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (TIMESTAMP => '2024-01-15 00:00:00'::TIMESTAMP)
END (TIMESTAMP => '2024-01-16 00:00:00'::TIMESTAMP);

-- Get metadata about changes
SELECT 
    *,
    METADATA$ACTION,      -- INSERT, DELETE
    METADATA$ISUPDATE,    -- TRUE if this is part of an UPDATE
    METADATA$ROW_ID       -- Unique row identifier
FROM {schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (OFFSET => -3600);  -- Last hour
```

**Use Cases:**
- Incremental data pipelines
- Real-time analytics
- Audit logging
- ML feature freshness

---

## stream_coverage

**Problem:** Tables lack streams for change data capture.

**Diagnosis:**
```sql
-- Check existing streams
SELECT 
    stream_name,
    table_name AS source_table,
    type,
    stale,
    stale_after
FROM information_schema.streams
WHERE table_schema = '{schema}';

-- Find tables without streams
SELECT t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.streams s ON t.table_name = s.table_name
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
  AND s.stream_name IS NULL;
```

**Fix Patterns:**

```sql
-- Create standard stream (tracks all DML)
CREATE OR REPLACE STREAM {schema}.{table}_stream 
ON TABLE {schema}.{table};

-- Create append-only stream (INSERT only, more efficient)
CREATE OR REPLACE STREAM {schema}.{table}_stream 
ON TABLE {schema}.{table}
APPEND_ONLY = TRUE;

-- Create stream on view (for pre-filtered changes)
CREATE OR REPLACE STREAM {schema}.{view}_stream 
ON VIEW {schema}.{view};
```

**Consume Stream Changes:**
```sql
-- Query stream for pending changes
SELECT 
    *,
    METADATA$ACTION,      -- INSERT, DELETE
    METADATA$ISUPDATE,    -- TRUE if UPDATE
    METADATA$ROW_ID
FROM {schema}.{table}_stream;

-- Process and advance stream (in a transaction)
BEGIN;
    INSERT INTO {schema}.{target_table}
    SELECT * FROM {schema}.{table}_stream 
    WHERE METADATA$ACTION = 'INSERT';
    
    -- Stream automatically advances after successful DML
COMMIT;

-- Check if stream has data (for conditional processing)
SELECT SYSTEM$STREAM_HAS_DATA('{schema}.{table}_stream');
```

**Stream + Task Pattern:**
```sql
-- Create task to process stream automatically
CREATE OR REPLACE TASK {schema}.process_{table}_changes
WAREHOUSE = {warehouse}
SCHEDULE = '5 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('{schema}.{table}_stream')
AS
INSERT INTO {schema}.{table}_history
SELECT *, CURRENT_TIMESTAMP() AS processed_at
FROM {schema}.{table}_stream;

-- Enable the task
ALTER TASK {schema}.process_{table}_changes RESUME;
```

---

## data_freshness_pass_rate

**Problem:** Data is stale (not updated recently).

**Diagnosis:**
```sql
-- Check table freshness via last_altered (DDL changes)
SELECT 
    table_name,
    last_altered,
    DATEDIFF('day', last_altered, CURRENT_TIMESTAMP()) AS days_since_altered
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
ORDER BY last_altered;

-- Check actual data freshness (if timestamp column exists)
SELECT 
    '{table}' AS table_name,
    MAX(updated_at) AS newest_record,
    DATEDIFF('hour', MAX(updated_at), CURRENT_TIMESTAMP()) AS hours_stale
FROM {schema}.{table};
```

**Fix Patterns:**

```sql
-- Option 1: Manual refresh (ad-hoc)
INSERT INTO {schema}.{table}
SELECT * FROM {source_table}
WHERE updated_at > (SELECT MAX(updated_at) FROM {schema}.{table});

-- Option 2: Scheduled task for regular refresh
CREATE OR REPLACE TASK {schema}.refresh_{table}_task
WAREHOUSE = {warehouse}
SCHEDULE = 'USING CRON 0 */6 * * * UTC'  -- Every 6 hours
AS
MERGE INTO {schema}.{table} t
USING {source_table} s ON t.id = s.id
WHEN MATCHED AND s.updated_at > t.updated_at THEN
    UPDATE SET * = s.*
WHEN NOT MATCHED THEN
    INSERT * VALUES (s.*);

ALTER TASK {schema}.refresh_{table}_task RESUME;

-- Option 3: Convert to Dynamic Table (automatic refresh)
CREATE OR REPLACE DYNAMIC TABLE {schema}.{table}_fresh
TARGET_LAG = '1 hour'
WAREHOUSE = {warehouse}
AS
SELECT * FROM {source_table};
```

**Freshness Monitoring:**
```sql
-- Create a freshness monitoring view
CREATE OR REPLACE VIEW {schema}.DATA_FRESHNESS AS
SELECT 
    table_name,
    MAX(updated_at) AS last_update,
    DATEDIFF('minute', MAX(updated_at), CURRENT_TIMESTAMP()) AS minutes_stale,
    CASE 
        WHEN DATEDIFF('hour', MAX(updated_at), CURRENT_TIMESTAMP()) > 24 THEN 'STALE'
        WHEN DATEDIFF('hour', MAX(updated_at), CURRENT_TIMESTAMP()) > 6 THEN 'WARNING'
        ELSE 'FRESH'
    END AS freshness_status
FROM (
    SELECT 'CUSTOMERS' AS table_name, MAX(updated_at) AS updated_at FROM {schema}.CUSTOMERS
    UNION ALL
    SELECT 'ORDERS', MAX(updated_at) FROM {schema}.ORDERS
    UNION ALL
    SELECT 'EVENTS', MAX(event_timestamp) FROM {schema}.EVENTS
)
GROUP BY table_name;
```

---

## dynamic_table_coverage

**Problem:** Derived tables are static views instead of dynamic tables.

**Diagnosis:**
```sql
-- Find views that could be dynamic tables
SELECT 
    table_name,
    table_type,
    CASE 
        WHEN table_type = 'DYNAMIC TABLE' THEN 'Already Dynamic'
        WHEN table_type = 'VIEW' THEN 'Candidate for Dynamic Table'
        ELSE 'Base Table'
    END AS recommendation
FROM information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_type, table_name;

-- Check existing dynamic tables
SELECT 
    name,
    target_lag,
    refresh_mode,
    scheduling_state
FROM information_schema.dynamic_tables
WHERE schema_name = '{schema}';
```

**Fix Patterns:**

```sql
-- Convert view to dynamic table
-- First, get the view definition
SELECT GET_DDL('VIEW', '{schema}.{view_name}');

-- Create dynamic table with same query
CREATE OR REPLACE DYNAMIC TABLE {schema}.{table_name}
TARGET_LAG = '1 hour'           -- Or 'DOWNSTREAM' for real-time
WAREHOUSE = {warehouse}
AS
{view_definition_sql};

-- Drop old view if replacing
DROP VIEW IF EXISTS {schema}.{old_view_name};
```

**Dynamic Table Options:**
```sql
-- Time-based lag (refreshes at most every N time units)
CREATE DYNAMIC TABLE {schema}.{table}
TARGET_LAG = '1 hour'
WAREHOUSE = {warehouse}
AS SELECT ...;

-- Downstream lag (refreshes when upstream changes)
CREATE DYNAMIC TABLE {schema}.{table}
TARGET_LAG = 'DOWNSTREAM'
WAREHOUSE = {warehouse}
AS SELECT ...;

-- Cascading dynamic tables
CREATE DYNAMIC TABLE {schema}.base_aggregates
TARGET_LAG = '15 minutes'
WAREHOUSE = {warehouse}
AS SELECT ... FROM raw_data;

CREATE DYNAMIC TABLE {schema}.summary
TARGET_LAG = 'DOWNSTREAM'  -- Refreshes after base_aggregates
WAREHOUSE = {warehouse}
AS SELECT ... FROM base_aggregates;
```

**Monitor Dynamic Tables:**
```sql
-- Check refresh history
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
    NAME => '{schema}.{table}',
    DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
));

-- Check current state
SELECT 
    name,
    target_lag,
    refresh_mode,
    data_timestamp,
    last_completed_dependency_name
FROM information_schema.dynamic_tables
WHERE schema_name = '{schema}';
```
