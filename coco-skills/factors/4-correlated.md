# Factor 4: Correlated

**Definition:** Data lineage is visible, relationships are explicit, and provenance is tracked from source to every decision it informs.

## Why It Matters for AI

When an AI system produces a wrong answer, you need to trace back: what data informed it? Correlated data has explicit lineage — you can follow any output back through transformations to source tables. Without correlation, debugging AI failures becomes guesswork.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `object_tag_coverage` | Fraction of tables with at least one tag | gte | 0.30 | 0.60 | 0.90 |
| `column_tag_coverage` | Fraction of columns with tags | gte | 0.20 | 0.50 | 0.80 |
| `lineage_queryable` | Whether lineage data is accessible (binary) | gte | 0.00 | 1.00 | 1.00 |

**Direction `gte`** = higher is better. Value must be ≥ threshold to pass.

---

## Assessment SQL (Snowflake)

### object_tag_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
tagged_tables AS (
    SELECT COUNT(DISTINCT object_name) AS cnt
    FROM snowflake.account_usage.tag_references
    WHERE object_schema = '{schema}'
      AND domain = 'TABLE'
      AND deleted IS NULL
)
SELECT tagged_tables.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, tagged_tables;
```

### column_tag_coverage
```sql
WITH column_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.columns c
    JOIN information_schema.tables t 
      ON c.table_name = t.table_name AND c.table_schema = t.table_schema
    WHERE c.table_schema = '{schema}'
      AND t.table_type = 'BASE TABLE'
),
tagged_columns AS (
    SELECT COUNT(DISTINCT column_name) AS cnt
    FROM snowflake.account_usage.tag_references
    WHERE object_schema = '{schema}'
      AND domain = 'COLUMN'
      AND deleted IS NULL
)
SELECT tagged_columns.cnt::FLOAT / NULLIF(column_count.cnt::FLOAT, 0) AS value
FROM column_count, tagged_columns;
```

### lineage_queryable
```sql
-- Binary check: can we query lineage? (returns 1.0 or 0.0)
SELECT CASE 
    WHEN COUNT(*) > 0 THEN 1.0 
    ELSE 0.0 
END AS value
FROM snowflake.account_usage.access_history
WHERE query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
LIMIT 1;
```

### Detailed tag inventory
```sql
SELECT 
    t.table_name,
    COUNT(DISTINCT tr.tag_name) AS tag_count,
    LISTAGG(DISTINCT tr.tag_name, ', ') WITHIN GROUP (ORDER BY tr.tag_name) AS tags
FROM information_schema.tables t
LEFT JOIN snowflake.account_usage.tag_references tr 
    ON t.table_name = tr.object_name
    AND t.table_schema = tr.object_schema
    AND tr.domain = 'TABLE'
    AND tr.deleted IS NULL
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
GROUP BY t.table_name
ORDER BY tag_count, t.table_name;
```

### Available tags in schema
```sql
SHOW TAGS IN SCHEMA {database}.{schema};
```

### Sample lineage query
```sql
SELECT 
    query_id,
    user_name,
    query_start_time,
    direct_objects_accessed,
    objects_modified
FROM snowflake.account_usage.access_history
WHERE query_start_time > DATEADD('day', -1, CURRENT_TIMESTAMP())
LIMIT 20;
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)
- `lineage_queryable` is binary: 0.0 or 1.0

---

## Required Permissions

Querying `snowflake.account_usage.tag_references` and `access_history` requires:
- Role with `IMPORTED PRIVILEGES` on SNOWFLAKE database, OR
- `GOVERNANCE_VIEWER` role, OR
- `ACCOUNTADMIN` role

```sql
-- Grant access to governance views
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {role};

-- Or create dedicated governance role
CREATE ROLE IF NOT EXISTS GOVERNANCE_VIEWER;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE GOVERNANCE_VIEWER;
GRANT ROLE GOVERNANCE_VIEWER TO USER {user};
```

---

## Remediation

### Create Standard Tags
```sql
-- Data domain classification
CREATE TAG IF NOT EXISTS {database}.{schema}.data_domain
    ALLOWED_VALUES 'customer', 'order', 'product', 'event', 'financial';

-- Ownership
CREATE TAG IF NOT EXISTS {database}.{schema}.owner
    COMMENT = 'Team or individual responsible for this data';

-- Sensitivity level
CREATE TAG IF NOT EXISTS {database}.{schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

-- Freshness SLA
CREATE TAG IF NOT EXISTS {database}.{schema}.freshness_sla
    ALLOWED_VALUES '1h', '6h', '24h', '7d', '30d';
```

### Apply Tags to Tables
```sql
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.data_domain = '{domain}';
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.owner = '{owner_team}';
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.sensitivity = '{level}';
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.freshness_sla = '{sla}';
```

**Example:**
```sql
ALTER TABLE {database}.{schema}.CUSTOMERS SET TAG {database}.{schema}.data_domain = 'customer';
ALTER TABLE {database}.{schema}.CUSTOMERS SET TAG {database}.{schema}.owner = 'customer-data-team';
ALTER TABLE {database}.{schema}.CUSTOMERS SET TAG {database}.{schema}.sensitivity = 'confidential';
```

### Create Column-Level Tags
```sql
-- PII classification
CREATE TAG IF NOT EXISTS {database}.{schema}.pii 
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card';

-- Semantic data type
CREATE TAG IF NOT EXISTS {database}.{schema}.data_type_semantic
    ALLOWED_VALUES 'identifier', 'timestamp', 'amount', 'quantity', 'status', 'text';
```

### Apply Tags to Columns
```sql
-- PII columns
ALTER TABLE {database}.{schema}.CUSTOMERS MODIFY COLUMN email 
    SET TAG {database}.{schema}.pii = 'email';
ALTER TABLE {database}.{schema}.CUSTOMERS MODIFY COLUMN phone 
    SET TAG {database}.{schema}.pii = 'phone';

-- Semantic types
ALTER TABLE {database}.{schema}.ORDERS MODIFY COLUMN order_id 
    SET TAG {database}.{schema}.data_type_semantic = 'identifier';
ALTER TABLE {database}.{schema}.ORDERS MODIFY COLUMN total_amount 
    SET TAG {database}.{schema}.data_type_semantic = 'amount';
```

### Auto-Classification (Enterprise)
```sql
-- Use Snowflake's automatic classification
SELECT SYSTEM$CLASSIFY('{database}.{schema}.{table}', {'auto_tag': true});
```

### Query Lineage
```sql
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

---

## Execution Pattern

1. **Run object_tag_coverage**: Query `tag_references` for TABLE domain
2. **Run column_tag_coverage**: Query `tag_references` for COLUMN domain
3. **Run lineage_queryable**: Test access to `access_history`
4. **List gaps**: Find untagged tables and columns
5. **Compare to threshold**: Use L1/L2/L3 based on user's workload
6. **Generate fixes**: Create TAG and ALTER statements
