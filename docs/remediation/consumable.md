# Consumable Factor Remediation

**Factor 2: Consumable** — Is the data served in the right format and at the right latencies for AI workloads?

Reference: `/factors.md` § Accessible (Consumable)

---

## clustering_coverage

**Problem:** Large tables lack clustering keys for query performance.

**Diagnosis:**
```sql
-- Find large tables without clustering
SELECT 
    table_name,
    row_count,
    bytes / (1024*1024*1024) AS size_gb,
    clustering_key,
    CASE WHEN clustering_key IS NULL THEN 'NEEDS CLUSTERING' ELSE 'OK' END AS status
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
  AND row_count > 10000
ORDER BY row_count DESC;

-- Check clustering depth (if already clustered)
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLUSTERING_INFORMATION('{schema}', '{table}'));
```

**Fix Patterns:**

```sql
-- Add clustering key on frequently filtered/joined columns
ALTER TABLE {schema}.{table} CLUSTER BY ({column1}, {column2});

-- Common patterns:
-- Time-series data: cluster by timestamp
ALTER TABLE {schema}.EVENTS CLUSTER BY (event_timestamp);

-- Transactional data: cluster by date + ID
ALTER TABLE {schema}.ORDERS CLUSTER BY (TO_DATE(created_at), customer_id);

-- Lookup tables: cluster by primary lookup column
ALTER TABLE {schema}.PRODUCTS CLUSTER BY (category, product_id);
```

**Monitor Clustering:**
```sql
-- Check clustering history
SELECT * FROM TABLE(INFORMATION_SCHEMA.AUTOMATIC_CLUSTERING_HISTORY(
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_DATE()),
    TABLE_NAME => '{schema}.{table}'
));

-- Check clustering depth (lower is better, 1-2 is ideal)
SELECT SYSTEM$CLUSTERING_DEPTH('{schema}.{table}');
```

**Clustering Best Practices:**
- Cluster on columns used in WHERE clauses and JOINs
- Put most selective column first
- Limit to 3-4 columns max
- Time-series tables: always include timestamp first
- Consider query patterns, not just data distribution

---

## search_optimization_coverage

**Problem:** Tables lack search optimization for text queries.

**Diagnosis:**
```sql
-- Check search optimization status
SELECT 
    table_name,
    search_optimization,
    search_optimization_progress,
    search_optimization_bytes
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE';

-- Find tables with text columns that might benefit
SELECT 
    t.table_name,
    COUNT_IF(c.data_type IN ('VARCHAR', 'TEXT', 'STRING')) AS text_column_count,
    t.search_optimization
FROM information_schema.tables t
JOIN information_schema.columns c 
  ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
GROUP BY t.table_name, t.search_optimization
ORDER BY text_column_count DESC;
```

**Fix Patterns:**

```sql
-- Enable search optimization on entire table
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION;

-- Enable for specific columns (more targeted, lower cost)
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION 
ON SUBSTRING({text_column});

-- Enable for equality searches (e.g., email lookup)
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION 
ON EQUALITY({column});

-- Combine multiple columns
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION 
ON SUBSTRING(name), SUBSTRING(description), EQUALITY(email);
```

**Use Cases for Search Optimization:**
```sql
-- Substring/LIKE queries
SELECT * FROM PRODUCTS WHERE name ILIKE '%wireless%';

-- Equality on high-cardinality columns
SELECT * FROM CUSTOMERS WHERE email = 'user@example.com';

-- VARIANT/JSON field searches
SELECT * FROM EVENTS WHERE event_data:user_id = '12345';

-- Geo-spatial queries
SELECT * FROM LOCATIONS WHERE ST_WITHIN(point, polygon);
```

**Monitor Search Optimization:**
```sql
-- Check progress (can take time for large tables)
SELECT 
    table_name,
    search_optimization_progress,
    search_optimization_bytes / (1024*1024) AS search_opt_mb
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND search_optimization = 'ON';
```

**Cost Considerations:**
- Search optimization uses storage (typically 25-50% of table size)
- Maintenance is automatic but consumes compute
- Best for tables with frequent substring/equality searches
- May not be cost-effective for small tables or infrequent queries
