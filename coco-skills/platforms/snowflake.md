# Platform: Snowflake

Reference for Snowflake-specific patterns used across all factor assessments.

## Connection

Use the active Snowflake connection via `snowflake_sql_execute`. No explicit connection string needed — Cortex Code manages the connection context.

## Key Information Schema Views

### Tables & Structure
```sql
-- Table metadata (clustering, search optimization, change tracking)
SELECT * FROM information_schema.tables WHERE table_schema = '{schema}';

-- Column metadata (types, nullability, comments)
SELECT * FROM information_schema.columns WHERE table_schema = '{schema}';

-- Constraints (PK, FK, UNIQUE)
SELECT * FROM information_schema.table_constraints WHERE table_schema = '{schema}';
```

### Streams & Dynamic Tables
```sql
-- Active streams for CDC
SELECT * FROM information_schema.streams WHERE table_schema = '{schema}';

-- Dynamic tables with refresh info
SELECT * FROM information_schema.dynamic_tables WHERE schema_name = '{schema}';
```

### Policies & Tags
```sql
-- Masking and row access policies
SELECT * FROM information_schema.policy_references WHERE ref_schema_name = '{schema}';

-- Object and column tags (requires account_usage access)
SELECT * FROM snowflake.account_usage.tag_references 
WHERE object_schema = '{schema}' AND deleted IS NULL;
```

### Lineage
```sql
-- Access history for lineage (up to 3hr latency)
SELECT * FROM snowflake.account_usage.access_history
WHERE query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP());
```

## Important Columns by View

### information_schema.tables
| Column | Use |
|--------|-----|
| `table_name` | Table identifier |
| `table_type` | BASE TABLE, VIEW, DYNAMIC TABLE |
| `row_count` | Approximate row count |
| `bytes` | Storage size |
| `clustering_key` | Clustering columns (null if unclustered) |
| `change_tracking` | ON/OFF |
| `search_optimization` | ON/OFF |
| `comment` | Table description |
| `last_altered` | Last DDL change timestamp |

### information_schema.columns
| Column | Use |
|--------|-----|
| `column_name` | Column identifier |
| `data_type` | Data type |
| `is_nullable` | YES/NO |
| `column_default` | Default value |
| `comment` | Column description |

### information_schema.streams
| Column | Use |
|--------|-----|
| `stream_name` | Stream identifier |
| `source_name` | Source table name |
| `source_type` | TABLE, VIEW |
| `stale` | TRUE if stream is stale |
| `stale_after` | When stream becomes stale |

## Snowflake Cortex Functions

### AI_GENERATE_TABLE_DESC
```sql
-- Generate descriptions for tables/columns
SELECT SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC(
    '{database}', '{schema}', '{table}'
);
```

### Classification (Enterprise)
```sql
-- Automatic sensitive data classification
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFICATION_SCHEMA(
    TABLE_NAME => '{database}.{schema}.{table}'
));
```

## Common Patterns

### Scope Discovery
```sql
-- List all schemas in database
SHOW SCHEMAS IN DATABASE {database};

-- List all tables in schema
SELECT table_name, table_type, row_count, comment
FROM information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_type, table_name;
```

### Batch Assessment Template
```sql
-- Aggregate multiple metrics in one query
SELECT
    t.table_name,
    t.row_count,
    t.change_tracking,
    t.search_optimization,
    t.clustering_key IS NOT NULL AS is_clustered,
    t.comment IS NOT NULL AND t.comment != '' AS has_comment,
    (SELECT COUNT(*) FROM information_schema.table_constraints tc 
     WHERE tc.table_name = t.table_name 
       AND tc.table_schema = t.table_schema 
       AND tc.constraint_type = 'PRIMARY KEY') > 0 AS has_pk
FROM information_schema.tables t
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;
```

## Required Permissions

| Access | Minimum Role/Grant |
|--------|-------------------|
| `information_schema.*` | Any role with USAGE on schema |
| `snowflake.account_usage.tag_references` | IMPORTED PRIVILEGES on SNOWFLAKE database |
| `snowflake.account_usage.access_history` | IMPORTED PRIVILEGES on SNOWFLAKE database |
| `SNOWFLAKE.CORTEX.*` | USAGE on SNOWFLAKE.CORTEX schema |

### Grant Pattern
```sql
-- For governance views
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {role};

-- For Cortex functions
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE {role};
```
