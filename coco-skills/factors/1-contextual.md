# Factor 1: Contextual

**Definition:** The meaning of each data element is explicit, unambiguous, and colocated with the data itself.

## Why It Matters for AI

Humans bring context to data interpretation; AI does not. Column names like `amt` or `dt` carry meaning to analysts who know the domain, but embeddings and models see only tokens. Context must be explicit — in comments, constraints, and relationships — so AI can interpret data without human intuition.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `pk_coverage` | Fraction of tables with primary keys | gte | 0.70 | 0.90 | 1.00 |
| `fk_coverage` | Fraction of tables with foreign keys | gte | 0.50 | 0.80 | 0.95 |
| `comment_coverage` | Fraction of columns with comments | gte | 0.30 | 0.70 | 0.90 |
| `table_comment_coverage` | Fraction of tables with comments | gte | 0.50 | 0.80 | 1.00 |

**Direction `gte`** = higher is better. Value must be ≥ threshold to pass.

---

## Assessment SQL (Snowflake)

### pk_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt 
    FROM information_schema.tables 
    WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
),
pk_count AS (
    SELECT COUNT(DISTINCT table_name) AS cnt 
    FROM information_schema.table_constraints
    WHERE table_schema = '{schema}' AND constraint_type = 'PRIMARY KEY'
)
SELECT pk_count.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, pk_count;
```

### fk_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt 
    FROM information_schema.tables 
    WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
),
fk_count AS (
    SELECT COUNT(DISTINCT table_name) AS cnt 
    FROM information_schema.table_constraints
    WHERE table_schema = '{schema}' AND constraint_type = 'FOREIGN KEY'
)
SELECT fk_count.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, fk_count;
```

### table_comment_coverage
```sql
SELECT 
    COUNT_IF(comment IS NOT NULL AND comment != '') * 1.0 / NULLIF(COUNT(*), 0) AS value
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE';
```

### comment_coverage (columns)
```sql
SELECT 
    COUNT_IF(comment IS NOT NULL AND comment != '') * 1.0 / NULLIF(COUNT(*), 0) AS value
FROM information_schema.columns c
JOIN information_schema.tables t 
  ON c.table_name = t.table_name AND c.table_schema = t.table_schema
WHERE c.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE';
```

### Tables missing PKs
```sql
SELECT t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.table_constraints tc 
    ON t.table_name = tc.table_name 
    AND t.table_schema = tc.table_schema
    AND tc.constraint_type = 'PRIMARY KEY'
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE'
  AND tc.constraint_name IS NULL;
```

### Tables/columns missing comments
```sql
-- Tables without comments
SELECT table_name
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
  AND (comment IS NULL OR comment = '');

-- Columns without comments
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = '{schema}'
  AND (comment IS NULL OR comment = '')
ORDER BY table_name, ordinal_position;
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)

---

## Remediation

### Add Primary Keys
```sql
-- Identify likely PK column (usually *_id or id)
ALTER TABLE {database}.{schema}.{table} 
ADD CONSTRAINT {table}_pk PRIMARY KEY ({id_column});
```

### Add Foreign Keys
```sql
ALTER TABLE {database}.{schema}.{child_table}
ADD CONSTRAINT {child_table}_{parent_table}_fk 
FOREIGN KEY ({column}) REFERENCES {database}.{schema}.{parent_table}({pk_column});
```

### Add Table Comments
```sql
COMMENT ON TABLE {database}.{schema}.{table} IS 
'Description of what this table contains and its business purpose.';
```

### Add Column Comments
```sql
COMMENT ON COLUMN {database}.{schema}.{table}.{column} IS 
'Description of what this column represents.';
```

### AI-Generated Descriptions (Snowflake Cortex)
```sql
-- Generate description automatically
SELECT SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC(
    '{database}', '{schema}', '{table}'
) AS ai_description;

-- Apply generated description
COMMENT ON TABLE {database}.{schema}.{table} IS $${ai_description}$$;
```

### Batch Comment Update Pattern
```sql
-- Generate comments for all tables in schema
SELECT 
    table_name,
    SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC(
        '{database}', '{schema}', table_name
    ) AS suggested_comment
FROM information_schema.tables
WHERE table_schema = '{schema}'
  AND table_type = 'BASE TABLE'
  AND (comment IS NULL OR comment = '');
```

---

## Execution Pattern

1. **Run pk_coverage**: Check constraint metadata
2. **Run fk_coverage**: Check foreign key definitions
3. **Run comment_coverage**: Check column comments
4. **Run table_comment_coverage**: Check table comments
5. **List gaps**: Find specific tables/columns missing context
6. **Generate fixes**: Create ALTER/COMMENT statements
7. **Optional**: Use AI_GENERATE_TABLE_DESC for auto-generated descriptions
