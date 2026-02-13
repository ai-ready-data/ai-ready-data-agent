# Factor 0: Clean

**Definition:** Data is accurate, complete, valid, and free of errors that would compromise downstream consumption.

## Why It Matters for AI

Models optimize on whatever signal is present — including noise. Dirty data doesn't just degrade output quality; it gets encoded into weights and embeddings as learned patterns. Clean is Factor 0 because nothing else matters if the data is untrustworthy.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `null_rate` | Fraction of null values per column | lte | 0.20 | 0.05 | 0.01 |
| `duplicate_rate` | Fraction of duplicate rows per table | lte | 0.10 | 0.02 | 0.01 |

**Direction `lte`** = lower is better. Value must be ≤ threshold to pass.

---

## Assessment SQL (Snowflake)

### null_rate (per column)
```sql
SELECT 
  '{column}' AS column_name,
  COUNT_IF({column} IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS value
FROM {database}.{schema}.{table}
```

### duplicate_rate (per table)
```sql
WITH total AS (SELECT COUNT(*) AS cnt FROM {database}.{schema}.{table}),
     distinct_cnt AS (SELECT COUNT(*) AS cnt FROM (SELECT DISTINCT * FROM {database}.{schema}.{table}))
SELECT 1.0 - distinct_cnt.cnt::FLOAT / NULLIF(total.cnt::FLOAT, 0) AS value
FROM total, distinct_cnt
```

### Schema-wide null summary
```sql
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = '{schema}'
ORDER BY table_name, ordinal_position;
```

---

## Interpretation

| Score | Interpretation |
|-------|---------------|
| 0.00 | Perfect — no issues detected |
| ≤ threshold | Pass — within acceptable bounds for workload |
| > threshold | Fail — requires remediation |
| > 0.50 | Critical — significant data quality issue |

---

## Remediation

### High null_rate

**Option 1: Fill with default**
```sql
UPDATE {database}.{schema}.{table} 
SET {column} = '{default_value}' 
WHERE {column} IS NULL;
```

**Option 2: Add NOT NULL constraint (after filling)**
```sql
ALTER TABLE {database}.{schema}.{table} 
ALTER COLUMN {column} SET NOT NULL;
```

**Option 3: Set default for future inserts**
```sql
ALTER TABLE {database}.{schema}.{table} 
ALTER COLUMN {column} SET DEFAULT '{default_value}';
```

### High duplicate_rate

**Deduplicate keeping latest occurrence**
```sql
CREATE OR REPLACE TABLE {database}.{schema}.{table} AS
SELECT * FROM {database}.{schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_columns} ORDER BY {timestamp_column} DESC) = 1;
```

**Deduplicate keeping first occurrence**
```sql
CREATE OR REPLACE TABLE {database}.{schema}.{table} AS
SELECT * FROM {database}.{schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_columns} ORDER BY {timestamp_column} ASC) = 1;
```

---

## Execution Pattern

1. **Discover columns**: Query `information_schema.columns` for target schema
2. **Run null_rate**: Execute per important column (PKs, required fields)
3. **Run duplicate_rate**: Execute per table
4. **Compare to threshold**: Use L1/L2/L3 based on user's workload
5. **For failures**: Generate remediation SQL from patterns above
