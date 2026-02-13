# Factor 3: Current

**Definition:** Data reflects the present state, with freshness enforced by infrastructure rather than assumed by convention.

## Why It Matters for AI

Models have no concept of time. Every input is treated as ground truth. When a model receives stale data, it doesn't produce a "stale answer" — it produces a confident, wrong one. The staleness is invisible in the output.

Traditional analytics tolerates staleness through convention: "this dashboard refreshes nightly," "that report uses yesterday's data." Humans adjust their interpretation accordingly. AI systems cannot. An agent answering "what's my current balance?" will state yesterday's number as fact.

Freshness must be enforced by infrastructure:
- **Change tracking** captures when data changes
- **Streams** propagate changes incrementally
- **Dynamic tables** maintain derived data automatically
- **Freshness monitoring** alerts when data falls outside SLA

Without these mechanisms, freshness depends on pipeline schedules holding, jobs not failing, and upstream sources behaving — a chain of assumptions that eventually breaks.

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for stale data: Moderate.** Dashboards and reports often show historical data by design. Users understand "as of yesterday" or "refreshed hourly."

**L2 (RAG and retrieval systems)** — **Tolerance for stale data: Low.** Users expect current information. A support agent citing outdated policies or a knowledge base returning superseded procedures creates real harm.

**L3 (ML model training and fine-tuning)** — **Tolerance for stale data: Very low.** Training on stale data teaches the model outdated patterns. Feature stores must maintain point-in-time correctness — the features at inference must match what was available at training.

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
ALTER TABLE {database}.{schema}.{table} SET CHANGE_TRACKING = TRUE;
```

**Query Changes:**
```sql
SELECT * FROM {database}.{schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (TIMESTAMP => DATEADD('hour', -24, CURRENT_TIMESTAMP()));
```

### Create Streams
```sql
-- Standard stream (tracks all DML)
CREATE OR REPLACE STREAM {database}.{schema}.{table}_stream 
ON TABLE {database}.{schema}.{table};

-- Append-only stream (INSERT only, more efficient)
CREATE OR REPLACE STREAM {database}.{schema}.{table}_stream 
ON TABLE {database}.{schema}.{table}
APPEND_ONLY = TRUE;
```

**Stream + Task Pattern:**
```sql
CREATE OR REPLACE TASK {database}.{schema}.process_{table}_changes
WAREHOUSE = {warehouse}
SCHEDULE = '5 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('{database}.{schema}.{table}_stream')
AS
INSERT INTO {database}.{schema}.{table}_history
SELECT *, CURRENT_TIMESTAMP() AS processed_at
FROM {database}.{schema}.{table}_stream;

ALTER TASK {database}.{schema}.process_{table}_changes RESUME;
```

### Convert Views to Dynamic Tables
```sql
CREATE OR REPLACE DYNAMIC TABLE {database}.{schema}.{table_name}
TARGET_LAG = '1 hour'
WAREHOUSE = {warehouse}
AS
{view_definition_sql};
```

**Dynamic Table Options:**
- `TARGET_LAG = '1 hour'` — Time-based refresh
- `TARGET_LAG = 'DOWNSTREAM'` — Refresh when upstream changes
- Supports cascading (dynamic table reads from another dynamic table)

### Monitor Dynamic Tables
```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
    NAME => '{database}.{schema}.{table}',
    DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
));
```

---

## Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Change tracking** | Platform tracks row-level changes with timestamps | — | — |
| **Streams/CDC** | Platform supports streams for change data capture | Streams support append-only and full CDC modes | — |
| **Dynamic tables** | Platform supports automatically refreshed derived tables | Target lag configurable per table | Downstream cascade support |
| **Freshness monitoring** | Platform exposes last_altered timestamps | — | Freshness SLA alerting |

## Requirement Keys

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Change Detection | Change tracking | `change_tracking_coverage` |
| Change Detection | Stream coverage | `stream_coverage` |
| Freshness | Data freshness | `data_freshness_pass_rate` |
| Freshness | Automatic refresh | `dynamic_table_coverage` |

## Not Yet Implemented

These requirements are not yet testable via automated SQL checks:

- **Event timestamps:** Data carries explicit timestamps distinguishing event time from processing time
- **Declared freshness contracts:** Data carries its freshness SLA as metadata
- **Staleness metadata:** Data carries computed currency scores for prioritized refresh
- **Point-in-time correctness:** Feature values at inference match those available at training
- **Staleness blocking:** Circuit breakers block consumption when freshness contracts are violated

---

## Execution Pattern

1. **Run change_tracking_coverage**: Check `change_tracking` in metadata
2. **Run stream_coverage**: Check `information_schema.streams`
3. **Run dynamic_table_coverage**: Check for `DYNAMIC TABLE` types
4. **Assess freshness**: Compare `last_altered` or `MAX(timestamp_col)` to SLA
5. **List gaps**: Find tables without tracking/streams, stale streams
6. **Generate fixes**: Create ALTER and CREATE statements
