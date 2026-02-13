# Clean Factor Remediation

**Factor 0: Clean** — Is the data accurate, complete, valid, and error-free?

Reference: `/factors.md` § Clean

---

## null_rate

**Problem:** Column has null values above threshold.

**Diagnosis:**
```sql
SELECT 
    '{column}' AS column_name,
    COUNT(*) AS total_rows,
    COUNT_IF({column} IS NULL) AS null_count,
    ROUND(COUNT_IF({column} IS NULL) * 100.0 / COUNT(*), 2) AS null_pct
FROM {schema}.{table};
```

**Fix Patterns:**

```sql
-- Option 1: Fill with default value
UPDATE {schema}.{table} 
SET {column} = '{default_value}' 
WHERE {column} IS NULL;

-- Option 2: Fill with computed value (e.g., for emails)
UPDATE {schema}.{table}
SET {column} = CONCAT('unknown_', {id_column}, '@placeholder.com')
WHERE {column} IS NULL;

-- Option 3: Add NOT NULL constraint after filling
ALTER TABLE {schema}.{table} 
ALTER COLUMN {column} SET NOT NULL;

-- Option 4: Add default for future inserts
ALTER TABLE {schema}.{table} 
ALTER COLUMN {column} SET DEFAULT '{default_value}';
```

**Snowflake-specific:**
```sql
-- Use COALESCE in views if source data can't be modified
CREATE OR REPLACE VIEW {schema}.{table}_clean AS
SELECT 
    *,
    COALESCE({column}, '{default}') AS {column}_clean
FROM {schema}.{table};
```

---

## duplicate_rate

**Problem:** Table has duplicate rows.

**Diagnosis:**
```sql
SELECT 
    'Duplicate analysis' AS analysis,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT *) AS unique_rows,
    COUNT(*) - COUNT(DISTINCT *) AS duplicate_rows,
    ROUND((1.0 - COUNT(DISTINCT *) * 1.0 / COUNT(*)) * 100, 2) AS duplicate_pct
FROM {schema}.{table};

-- Find the duplicates
SELECT *, COUNT(*) AS dup_count
FROM {schema}.{table}
GROUP BY ALL
HAVING COUNT(*) > 1
ORDER BY dup_count DESC
LIMIT 20;
```

**Fix Patterns:**

```sql
-- Option 1: Deduplicate by keeping all distinct rows
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT DISTINCT * FROM {schema}.{table};

-- Option 2: Deduplicate with explicit key (keep first)
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT * FROM {schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_columns} ORDER BY {order_column}) = 1;

-- Option 3: Deduplicate keeping most recent
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT * FROM {schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_columns} ORDER BY updated_at DESC) = 1;
```

**Prevention:**
```sql
-- Add unique constraint (informational in Snowflake)
ALTER TABLE {schema}.{table} ADD UNIQUE ({key_columns});
```

---

## format_inconsistency_rate

**Problem:** Date/time column has inconsistent formats.

**Diagnosis:**
```sql
-- Check what formats exist
SELECT 
    {column},
    TRY_TO_DATE({column}) AS parsed_default,
    TRY_TO_DATE({column}, 'MM/DD/YYYY') AS parsed_us,
    TRY_TO_DATE({column}, 'DD-MON-YYYY') AS parsed_oracle,
    CASE 
        WHEN TRY_TO_DATE({column}) IS NOT NULL THEN 'ISO'
        WHEN TRY_TO_DATE({column}, 'MM/DD/YYYY') IS NOT NULL THEN 'US'
        WHEN TRY_TO_DATE({column}, 'DD-MON-YYYY') IS NOT NULL THEN 'Oracle'
        ELSE 'Unknown'
    END AS detected_format
FROM {schema}.{table}
WHERE TRY_TO_DATE({column}) IS NULL
LIMIT 20;
```

**Fix Patterns:**

```sql
-- Option 1: Add normalized column
ALTER TABLE {schema}.{table} ADD COLUMN {column}_normalized DATE;

-- Parse with multiple format attempts
UPDATE {schema}.{table} SET {column}_normalized = TRY_TO_DATE({column});

UPDATE {schema}.{table} 
SET {column}_normalized = TRY_TO_DATE({column}, 'MM/DD/YYYY')
WHERE {column}_normalized IS NULL;

UPDATE {schema}.{table} 
SET {column}_normalized = TRY_TO_DATE({column}, 'DD-MON-YYYY')
WHERE {column}_normalized IS NULL;

UPDATE {schema}.{table} 
SET {column}_normalized = TRY_TO_DATE({column}, 'MON DD, YYYY')
WHERE {column}_normalized IS NULL;

-- Option 2: Replace column entirely
ALTER TABLE {schema}.{table} DROP COLUMN {column};
ALTER TABLE {schema}.{table} RENAME COLUMN {column}_normalized TO {column};
```

---

## type_inconsistency_rate

**Problem:** Column has mixed types (e.g., numbers and text).

**Diagnosis:**
```sql
-- Find non-numeric values in numeric column
SELECT {column}, COUNT(*) AS cnt
FROM {schema}.{table}
WHERE TRY_CAST({column} AS DECIMAL(10,2)) IS NULL
GROUP BY {column}
ORDER BY cnt DESC;
```

**Fix Patterns:**

```sql
-- Option 1: Clean invalid values to NULL
UPDATE {schema}.{table}
SET {column} = NULL
WHERE TRY_CAST({column} AS DECIMAL(10,2)) IS NULL;

-- Option 2: Convert to proper type with new column
ALTER TABLE {schema}.{table} ADD COLUMN {column}_clean DECIMAL(10,2);
UPDATE {schema}.{table} SET {column}_clean = TRY_CAST({column} AS DECIMAL(10,2));
ALTER TABLE {schema}.{table} DROP COLUMN {column};
ALTER TABLE {schema}.{table} RENAME COLUMN {column}_clean TO {column};

-- Option 3: Map known bad values
UPDATE {schema}.{table}
SET {column} = CASE 
    WHEN {column} IN ('N/A', 'TBD', 'PENDING', '-') THEN NULL
    ELSE {column}
END;
```

---

## zero_negative_rate

**Problem:** Numeric column has invalid zero or negative values.

**Diagnosis:**
```sql
SELECT 
    'Zero/negative analysis' AS analysis,
    COUNT(*) AS total_rows,
    COUNT_IF({column} = 0) AS zero_count,
    COUNT_IF({column} < 0) AS negative_count,
    COUNT_IF({column} <= 0) AS invalid_count,
    ROUND(COUNT_IF({column} <= 0) * 100.0 / COUNT(*), 2) AS invalid_pct
FROM {schema}.{table};

-- See the invalid values
SELECT * FROM {schema}.{table} WHERE {column} <= 0 LIMIT 20;
```

**Fix Patterns:**

```sql
-- Option 1: Nullify invalid values
UPDATE {schema}.{table}
SET {column} = NULL
WHERE {column} <= 0;

-- Option 2: Set to minimum valid value
UPDATE {schema}.{table}
SET {column} = 1  -- or appropriate minimum
WHERE {column} <= 0;

-- Option 3: Add CHECK constraint to prevent future issues
ALTER TABLE {schema}.{table} 
ADD CONSTRAINT {column}_positive CHECK ({column} > 0);
```

**Snowflake-specific:**
```sql
-- Note: CHECK constraints are informational in Snowflake (not enforced)
-- Use a masking policy or secure view for enforcement:
CREATE OR REPLACE SECURE VIEW {schema}.{table}_valid AS
SELECT * FROM {schema}.{table} WHERE {column} > 0;
```
