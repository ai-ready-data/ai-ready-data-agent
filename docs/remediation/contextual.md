# Contextual Factor Remediation

**Factor 1: Contextual** — Is the meaning of the data explicit and colocated with the data?

Reference: `/factors.md` § Curated (Contextual)

---

## primary_key_defined

**Problem:** Table lacks a primary key constraint.

**Diagnosis:**
```sql
-- Check existing constraints
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_schema = '{schema}' AND table_name = '{table}';

-- Find candidate key columns (unique, non-null)
SELECT 
    column_name,
    COUNT(DISTINCT {column}) AS distinct_count,
    COUNT(*) AS total_count,
    COUNT_IF({column} IS NULL) AS null_count
FROM {schema}.{table}
GROUP BY ALL;
```

**Fix Patterns:**

```sql
-- Add primary key (column must have unique, non-null values)
ALTER TABLE {schema}.{table} 
ADD PRIMARY KEY ({column});

-- For composite keys
ALTER TABLE {schema}.{table}
ADD PRIMARY KEY ({column1}, {column2});
```

**If data has duplicates:**
```sql
-- First deduplicate (see clean.md > duplicate_rate)
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT * FROM {schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_column} ORDER BY {key_column}) = 1;

-- Then add PK
ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({key_column});
```

**Snowflake-specific:**
```sql
-- Note: Snowflake PKs are informational (not enforced at DML time)
-- They are valuable for:
-- 1. Documentation and semantic understanding
-- 2. Query optimization hints
-- 3. BI tool relationship discovery
-- 4. dbt relationship tests
```

---

## foreign_key_coverage

**Problem:** Table lacks foreign key relationships.

**Diagnosis:**
```sql
-- Check for potential FK columns (naming patterns)
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{table}'
  AND (column_name LIKE '%_id' OR column_name LIKE '%_key' OR column_name LIKE '%_fk');

-- Verify referential integrity before adding FK
SELECT 
    '{child_column}' AS fk_column,
    COUNT(DISTINCT c.{child_column}) AS distinct_values,
    COUNT(DISTINCT p.{parent_column}) AS matching_in_parent,
    COUNT_IF(p.{parent_column} IS NULL) AS orphan_count
FROM {schema}.{child_table} c
LEFT JOIN {schema}.{parent_table} p ON c.{child_column} = p.{parent_column};
```

**Fix Patterns:**

```sql
-- Add foreign key constraint
ALTER TABLE {schema}.{child_table}
ADD FOREIGN KEY ({column}) REFERENCES {schema}.{parent_table}({parent_column});

-- Example: Orders -> Customers
ALTER TABLE {schema}.ORDERS
ADD FOREIGN KEY (customer_id) REFERENCES {schema}.CUSTOMERS(customer_id);
```

**If orphan records exist:**
```sql
-- Option 1: Delete orphans
DELETE FROM {schema}.{child_table}
WHERE {column} NOT IN (SELECT {parent_column} FROM {schema}.{parent_table});

-- Option 2: Create placeholder parent record
INSERT INTO {schema}.{parent_table} ({parent_column}, name)
VALUES ('UNKNOWN', 'Unknown/Placeholder');

UPDATE {schema}.{child_table}
SET {column} = 'UNKNOWN'
WHERE {column} NOT IN (SELECT {parent_column} FROM {schema}.{parent_table});
```

**Snowflake-specific:**
```sql
-- Note: Snowflake FKs are informational (not enforced)
-- They are valuable for:
-- 1. Lineage documentation
-- 2. BI tool auto-join discovery
-- 3. Semantic layer relationship definition
-- 4. Query optimization hints
```

---

## semantic_model_coverage

**Problem:** Tables lack semantic model definitions.

**Diagnosis:**
```sql
-- Check for existing semantic views
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND (table_name LIKE '%_semantic' OR table_type = 'VIEW');

-- Check for column comments (basic semantic metadata)
SELECT table_name, column_name, comment
FROM information_schema.columns
WHERE table_schema = '{schema}'
  AND comment IS NOT NULL AND comment != '';
```

**Fix Patterns:**

```sql
-- Option 1: Create semantic view with business definitions
CREATE OR REPLACE VIEW {schema}.{table}_semantic AS
SELECT
    {column1} AS "Customer ID",
    {column2} AS "Email Address",
    {column3} AS "Order Total (USD)"
FROM {schema}.{table};

-- Option 2: Add comprehensive column comments
COMMENT ON COLUMN {schema}.{table}.{column} IS 
    'Business definition: {description}. Format: {format}. Example: {example}';

-- Option 3: Create a data dictionary view
CREATE OR REPLACE VIEW {schema}.DATA_DICTIONARY AS
SELECT 
    table_name,
    column_name,
    data_type,
    comment AS business_definition
FROM information_schema.columns
WHERE table_schema = '{schema}'
ORDER BY table_name, ordinal_position;
```

**Snowflake-specific:**
```sql
-- Use Snowflake's Semantic Views (if available in your account)
CREATE OR REPLACE SEMANTIC VIEW {schema}.{table}_semantic
AS SELECT * FROM {schema}.{table}
WITH COLUMN ANNOTATIONS (
    {column1} = 'Customer identifier',
    {column2} = 'Email for communications'
);

-- Or integrate with external semantic layers:
-- - dbt semantic layer
-- - Looker LookML
-- - Cube.js
-- - AtScale
```

---

## temporal_scope_present

**Problem:** Table lacks temporal columns (created_at, updated_at).

**Diagnosis:**
```sql
-- Check for existing temporal columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{table}'
  AND (
    column_name IN ('created_at', 'updated_at', 'created_date', 'modified_date', 
                    'insert_ts', 'update_ts', 'timestamp', 'datetime')
    OR data_type IN ('TIMESTAMP_NTZ', 'TIMESTAMP_LTZ', 'TIMESTAMP_TZ', 'DATE')
  );
```

**Fix Patterns:**

```sql
-- Add temporal columns
ALTER TABLE {schema}.{table} 
ADD COLUMN created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();

ALTER TABLE {schema}.{table} 
ADD COLUMN updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();

-- Backfill existing rows
UPDATE {schema}.{table} 
SET created_at = CURRENT_TIMESTAMP() 
WHERE created_at IS NULL;

UPDATE {schema}.{table} 
SET updated_at = CURRENT_TIMESTAMP() 
WHERE updated_at IS NULL;
```

**Maintaining updated_at:**
```sql
-- Option 1: Use streams + tasks for automatic updates
CREATE OR REPLACE STREAM {schema}.{table}_stream ON TABLE {schema}.{table};

CREATE OR REPLACE TASK {schema}.update_{table}_timestamp
WAREHOUSE = {warehouse}
SCHEDULE = '1 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('{schema}.{table}_stream')
AS
UPDATE {schema}.{table} t
SET updated_at = CURRENT_TIMESTAMP()
FROM {schema}.{table}_stream s
WHERE t.{pk_column} = s.{pk_column}
  AND s.METADATA$ACTION = 'INSERT';

ALTER TASK {schema}.update_{table}_timestamp RESUME;

-- Option 2: Handle in application layer (preferred for most cases)
```

**Snowflake-specific:**
```sql
-- Use Time Travel for point-in-time queries (even without explicit timestamps)
SELECT * FROM {schema}.{table} AT(TIMESTAMP => '2024-01-15 10:00:00'::TIMESTAMP);

-- Or use CHANGES clause with change tracking
SELECT * FROM {schema}.{table}
CHANGES(INFORMATION => DEFAULT)
AT(TIMESTAMP => DATEADD('hour', -24, CURRENT_TIMESTAMP()));
```

---

## Documentation (Table & Column Comments)

**Problem:** Tables and columns lack documentation, making meaning implicit.

**Note:** While not currently tested as a separate requirement, documentation is fundamental to making meaning explicit — a core Contextual principle.

**Diagnosis:**
```sql
-- Check table comment coverage
SELECT 
    table_name,
    CASE WHEN comment IS NOT NULL AND comment != '' THEN 'Yes' ELSE 'No' END AS has_comment
FROM information_schema.tables
WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE';

-- Check column comment coverage
SELECT 
    table_name,
    COUNT(*) AS total_columns,
    COUNT_IF(comment IS NOT NULL AND comment != '') AS documented
FROM information_schema.columns
WHERE table_schema = '{schema}'
GROUP BY table_name;
```

**Fix Patterns:**

```sql
-- Add table comments
COMMENT ON TABLE {schema}.{table} IS '{description}';

-- Add column comments
COMMENT ON COLUMN {schema}.{table}.{column} IS '{description}';

-- Example: Include what, format, valid values, business context
COMMENT ON COLUMN ORDERS.total_amount IS 
    'Total order value in USD. Decimal(10,2). Includes tax and shipping.';

COMMENT ON COLUMN CUSTOMERS.status IS
    'Account status: ACTIVE, SUSPENDED, CLOSED. Updated by customer service.';
```

**Best Practices:**
- Document all columns, not just "important" ones
- Include data type expectations and valid values
- Note relationships to other tables
- Describe business meaning, not just technical format
