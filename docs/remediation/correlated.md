# Correlated Factor Remediation

**Factor 4: Correlated** — Is the data traceable from source to every decision it informs?

Reference: `/factors.md` § Observable (Correlated)

---

## object_tag_coverage

**Problem:** Tables lack tags for classification and lineage.

**Diagnosis:**
```sql
-- Check existing tags on tables
SELECT 
    t.table_name,
    COUNT(tr.tag_name) AS tag_count
FROM information_schema.tables t
LEFT JOIN snowflake.account_usage.tag_references tr 
    ON t.table_catalog = tr.object_database
    AND t.table_schema = tr.object_schema
    AND t.table_name = tr.object_name
    AND tr.domain = 'TABLE'
    AND tr.deleted IS NULL
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
GROUP BY t.table_name
ORDER BY tag_count;

-- List available tags
SHOW TAGS IN SCHEMA {schema};
```

**Fix Patterns:**

```sql
-- First, create tags if they don't exist
CREATE TAG IF NOT EXISTS {schema}.data_domain
    ALLOWED_VALUES 'customer', 'order', 'product', 'event', 'financial';

CREATE TAG IF NOT EXISTS {schema}.owner
    COMMENT = 'Team or individual responsible for this data';

CREATE TAG IF NOT EXISTS {schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS {schema}.freshness_sla
    ALLOWED_VALUES '1h', '6h', '24h', '7d', '30d';

-- Apply tags to tables
ALTER TABLE {schema}.{table} SET TAG {schema}.data_domain = '{domain}';
ALTER TABLE {schema}.{table} SET TAG {schema}.owner = '{owner_team}';
ALTER TABLE {schema}.{table} SET TAG {schema}.sensitivity = '{level}';
ALTER TABLE {schema}.{table} SET TAG {schema}.freshness_sla = '{sla}';
```

**Example Tag Application:**
```sql
-- Customer domain tables
ALTER TABLE {schema}.CUSTOMERS SET TAG {schema}.data_domain = 'customer';
ALTER TABLE {schema}.CUSTOMERS SET TAG {schema}.owner = 'customer-data-team';
ALTER TABLE {schema}.CUSTOMERS SET TAG {schema}.sensitivity = 'confidential';
ALTER TABLE {schema}.CUSTOMERS SET TAG {schema}.freshness_sla = '24h';

-- Order domain tables
ALTER TABLE {schema}.ORDERS SET TAG {schema}.data_domain = 'order';
ALTER TABLE {schema}.ORDERS SET TAG {schema}.owner = 'orders-team';
ALTER TABLE {schema}.ORDERS SET TAG {schema}.sensitivity = 'internal';
ALTER TABLE {schema}.ORDERS SET TAG {schema}.freshness_sla = '1h';
```

**Query Tags:**
```sql
-- Get tag value for specific table
SELECT SYSTEM$GET_TAG('{schema}.data_domain', '{schema}.{table}', 'TABLE');

-- Find all tables with specific tag value
SELECT * FROM snowflake.account_usage.tag_references
WHERE tag_name = 'DATA_DOMAIN' 
  AND tag_value = 'customer'
  AND domain = 'TABLE'
  AND deleted IS NULL;
```

---

## column_tag_coverage

**Problem:** Columns lack tags for classification.

**Diagnosis:**
```sql
-- Check column tags
SELECT 
    c.table_name,
    c.column_name,
    tr.tag_name,
    tr.tag_value
FROM information_schema.columns c
LEFT JOIN snowflake.account_usage.tag_references tr
    ON c.table_catalog = tr.object_database
    AND c.table_schema = tr.object_schema
    AND c.table_name = tr.object_name
    AND c.column_name = tr.column_name
    AND tr.domain = 'COLUMN'
    AND tr.deleted IS NULL
WHERE c.table_schema = '{schema}'
ORDER BY c.table_name, c.column_name;
```

**Fix Patterns:**

```sql
-- Create column-level tags
CREATE TAG IF NOT EXISTS {schema}.pii 
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card';

CREATE TAG IF NOT EXISTS {schema}.data_type_semantic
    ALLOWED_VALUES 'identifier', 'timestamp', 'amount', 'quantity', 'status', 'text';

-- Apply PII tags to sensitive columns
ALTER TABLE {schema}.{table} MODIFY COLUMN {column} 
    SET TAG {schema}.pii = '{pii_type}';

ALTER TABLE {schema}.{table} MODIFY COLUMN {column}
    SET TAG {schema}.sensitivity = '{level}';

-- Apply semantic type tags
ALTER TABLE {schema}.{table} MODIFY COLUMN {column}
    SET TAG {schema}.data_type_semantic = '{type}';
```

**Example Column Tagging:**
```sql
-- PII columns
ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN email 
    SET TAG {schema}.pii = 'email';
ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN phone 
    SET TAG {schema}.pii = 'phone';
ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN name 
    SET TAG {schema}.pii = 'name';

-- Sensitivity on PII
ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN email 
    SET TAG {schema}.sensitivity = 'confidential';

-- Semantic types
ALTER TABLE {schema}.ORDERS MODIFY COLUMN order_id 
    SET TAG {schema}.data_type_semantic = 'identifier';
ALTER TABLE {schema}.ORDERS MODIFY COLUMN total_amount 
    SET TAG {schema}.data_type_semantic = 'amount';
ALTER TABLE {schema}.ORDERS MODIFY COLUMN created_at 
    SET TAG {schema}.data_type_semantic = 'timestamp';
```

**Auto-Classification (Enterprise Feature):**
```sql
-- Use Snowflake's automatic classification (if available)
SELECT SYSTEM$CLASSIFY('{schema}.{table}', {'auto_tag': true});

-- Or classify specific columns
SELECT SYSTEM$CLASSIFY_TEXT('{schema}.{table}', '{column}');
```

---

## lineage_queryable

**Problem:** Lineage data not being captured or queryable.

**Diagnosis:**
```sql
-- Check if we can query lineage
SELECT COUNT(*) AS recent_lineage_records
FROM snowflake.account_usage.access_history
WHERE query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP());

-- Check role access to lineage
SELECT CURRENT_ROLE() AS current_role;
-- Need ACCOUNTADMIN or GOVERNANCE_VIEWER for full access
```

**Fix Patterns:**

```sql
-- Grant lineage access to appropriate roles
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {role};

-- Or create a dedicated governance viewer role
CREATE ROLE IF NOT EXISTS GOVERNANCE_VIEWER;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE GOVERNANCE_VIEWER;
GRANT ROLE GOVERNANCE_VIEWER TO USER {user};
```

**Query Lineage:**
```sql
-- Basic lineage: what queries accessed what objects
SELECT 
    query_id,
    user_name,
    query_start_time,
    direct_objects_accessed,
    base_objects_accessed,
    objects_modified
FROM snowflake.account_usage.access_history
WHERE query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
LIMIT 100;

-- Find lineage for specific table (reads)
SELECT 
    query_id,
    user_name,
    query_start_time,
    f.value:objectName::STRING AS object_name
FROM snowflake.account_usage.access_history,
    LATERAL FLATTEN(input => direct_objects_accessed) f
WHERE f.value:objectName::STRING ILIKE '%{table}%'
  AND query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP());

-- Find lineage for specific table (writes)
SELECT 
    query_id,
    user_name,
    query_start_time,
    f.value:objectName::STRING AS modified_object
FROM snowflake.account_usage.access_history,
    LATERAL FLATTEN(input => objects_modified) f
WHERE f.value:objectName::STRING ILIKE '%{table}%'
  AND query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP());
```

**Create Lineage Views:**
```sql
-- Create simplified lineage view for data consumers
CREATE OR REPLACE VIEW {schema}.TABLE_LINEAGE AS
WITH read_lineage AS (
    SELECT 
        query_id,
        user_name,
        query_start_time,
        f.value:objectName::STRING AS source_table
    FROM snowflake.account_usage.access_history,
        LATERAL FLATTEN(input => direct_objects_accessed) f
    WHERE query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
),
write_lineage AS (
    SELECT 
        query_id,
        f.value:objectName::STRING AS target_table
    FROM snowflake.account_usage.access_history,
        LATERAL FLATTEN(input => objects_modified) f
    WHERE query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
)
SELECT DISTINCT
    r.source_table,
    w.target_table,
    r.user_name,
    MIN(r.query_start_time) AS first_seen,
    MAX(r.query_start_time) AS last_seen,
    COUNT(DISTINCT r.query_id) AS query_count
FROM read_lineage r
JOIN write_lineage w ON r.query_id = w.query_id
WHERE r.source_table != w.target_table
GROUP BY r.source_table, w.target_table, r.user_name;
```

**Note on Latency:**
- `access_history` view has up to 3-hour latency
- For real-time lineage needs, consider:
  - Parsing query logs directly
  - Using external lineage tools (Atlan, Monte Carlo, etc.)
  - Implementing application-level lineage tracking
