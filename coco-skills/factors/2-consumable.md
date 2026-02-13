# Factor 2: Consumable

**Definition:** Data is served in the right format and at the right latencies for AI workloads.

## Why It Matters for AI

AI systems have specific consumption patterns. RAG needs chunked text and embeddings. ML training needs fast scans over large datasets. Real-time inference needs millisecond lookups. "Consumable" means the data is optimized for how AI will access it — not just stored correctly.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `clustering_coverage` | Fraction of large tables with clustering keys | gte | 0.30 | 0.60 | 0.80 |
| `search_optimization_coverage` | Fraction of tables with search optimization | gte | 0.20 | 0.50 | 0.70 |

**Direction `gte`** = higher is better. Value must be ≥ threshold to pass.

**Note:** Future requirements may include `ai_consumable_format` for chunking/embeddings readiness.

---

## Assessment SQL (Snowflake)

### clustering_coverage
```sql
-- Fraction of large tables (>10K rows) with clustering keys
WITH large_tables AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
      AND row_count > 10000
),
clustered AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
      AND row_count > 10000
      AND clustering_key IS NOT NULL
)
SELECT clustered.cnt::FLOAT / NULLIF(large_tables.cnt::FLOAT, 0) AS value
FROM large_tables, clustered;
```

### search_optimization_coverage
```sql
-- Fraction of tables with search optimization enabled
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
search_opt AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
      AND search_optimization = 'ON'
)
SELECT search_opt.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, search_opt;
```

### Detailed clustering status
```sql
SELECT 
    table_name,
    row_count,
    bytes / (1024*1024*1024) AS size_gb,
    clustering_key,
    CASE 
        WHEN row_count <= 10000 THEN 'SMALL (OK)'
        WHEN clustering_key IS NOT NULL THEN 'CLUSTERED'
        ELSE 'NEEDS CLUSTERING'
    END AS status
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
ORDER BY row_count DESC;
```

### Detailed search optimization status
```sql
SELECT 
    table_name,
    search_optimization,
    search_optimization_progress,
    search_optimization_bytes / (1024*1024) AS search_opt_mb
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
ORDER BY search_optimization DESC, table_name;
```

### Tables with text columns (search optimization candidates)
```sql
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
HAVING text_column_count > 0
ORDER BY text_column_count DESC;
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)

---

## Remediation

### Add Clustering Keys

```sql
-- Add clustering key on frequently filtered/joined columns
ALTER TABLE {database}.{schema}.{table} CLUSTER BY ({column1}, {column2});

-- Common patterns:

-- Time-series data: cluster by timestamp
ALTER TABLE {database}.{schema}.EVENTS CLUSTER BY (event_timestamp);

-- Transactional data: cluster by date + ID
ALTER TABLE {database}.{schema}.ORDERS CLUSTER BY (TO_DATE(created_at), customer_id);

-- Lookup tables: cluster by primary lookup column
ALTER TABLE {database}.{schema}.PRODUCTS CLUSTER BY (category, product_id);
```

**Clustering Best Practices:**
- Cluster on columns used in WHERE clauses and JOINs
- Put most selective column first
- Limit to 3-4 columns max
- Time-series tables: always include timestamp first

### Monitor Clustering
```sql
-- Check clustering depth (lower is better, 1-2 is ideal)
SELECT SYSTEM$CLUSTERING_DEPTH('{database}.{schema}.{table}');

-- Check clustering info
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLUSTERING_INFORMATION('{database}.{schema}', '{table}'));
```

### Enable Search Optimization

```sql
-- Enable search optimization on entire table
ALTER TABLE {database}.{schema}.{table} ADD SEARCH OPTIMIZATION;

-- Enable for specific columns (more targeted, lower cost)
ALTER TABLE {database}.{schema}.{table} ADD SEARCH OPTIMIZATION 
ON SUBSTRING({text_column});

-- Enable for equality searches (e.g., email lookup)
ALTER TABLE {database}.{schema}.{table} ADD SEARCH OPTIMIZATION 
ON EQUALITY({column});

-- Combine multiple columns
ALTER TABLE {database}.{schema}.{table} ADD SEARCH OPTIMIZATION 
ON SUBSTRING(name), SUBSTRING(description), EQUALITY(email);
```

**Search Optimization Use Cases:**
- Substring/LIKE queries: `WHERE name ILIKE '%wireless%'`
- Equality on high-cardinality columns: `WHERE email = 'user@example.com'`
- VARIANT/JSON field searches: `WHERE data:user_id = '12345'`

**Cost Considerations:**
- Search optimization uses storage (typically 25-50% of table size)
- Maintenance is automatic but consumes compute
- Best for tables with frequent substring/equality searches
- May not be cost-effective for small tables or infrequent queries

---

## Execution Pattern

1. **Run clustering_coverage**: Check `clustering_key` in metadata
2. **Run search_optimization_coverage**: Check `search_optimization` status
3. **List gaps**: Find large tables without clustering, text-heavy tables without search opt
4. **Compare to threshold**: Use L1/L2/L3 based on user's workload
5. **Generate fixes**: Create ALTER statements for clustering and search optimization
