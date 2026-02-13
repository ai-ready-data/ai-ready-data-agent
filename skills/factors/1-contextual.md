# Factor 1: Contextual

**Definition:** Meaning is explicit and colocated with the data. No external lookup, tribal knowledge, or human context is required to take action on the data.

## Why It Matters for AI

If the data's meaning lives outside the system or is not accessible at inference-time, the data is not interpretable. Traditional analytics tolerates implicit meaning — analysts learn the schema, read a wiki, ask colleagues. AI systems have none of that context. A model consuming data with ambiguous column names, missing relationship declarations, or undocumented business logic is operating blind.

Contextual data ensures consistent interpretation across contexts and models at inference-time. Meaning must be explicit, machine-readable, and colocated with the data it describes.

Meaning can be broken into four dimensions:

- **Structural Semantics (What the data is):** Typed schemas, constraint declarations, and evolution contracts encode the data's formal identity.
- **Business Semantics (What the data means):** Versioned definitions, calculation logic, and controlled vocabularies encode authoritative meaning.
- **Entity Semantics (How the data connects):** Typed, scoped, and/or probabilistic relationships encode referential integrity of meaning.
- **Contextual Semantics (When/where it applies):** Temporal scope, jurisdictional applicability, provenance, and confidence encode the boundaries of validity.

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for missing context: Moderate.** Humans are in the loop. They can look up column definitions in a wiki, ask a colleague what a table represents, or infer meaning from experience. Structural constraints and descriptions are helpful but not essential — the analyst compensates.

**L2 (RAG and retrieval systems)** — **Tolerance for missing context: Low.** The model has no tribal knowledge. If meaning is not colocated with the data, the model generates answers without understanding what the data represents. Business definitions, semantic models, and declared relationships become critical because they are the only context the model has at inference-time.

**L3 (ML model training and fine-tuning)** — **Tolerance for missing context: Very low.** Ambiguous semantics propagate into learned representations. If the model does not know what a column means, what relationships exist, or when data is valid, it cannot learn the right signal. Full semantic coverage is essential — meaning that is implicit or external to the data at training time is meaning the model will never have.

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

## Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Constraint declarations** | Platform supports PRIMARY KEY and FOREIGN KEY constraints (enforced or declared) | — | Constraints are enforced, not just declared |
| **Semantic model layer** | Platform supports or integrates with a semantic model (e.g. semantic views, dbt semantic layer, catalog with business definitions) | Semantic model is queryable at inference-time (not just documentation) | Semantic model is versioned and covers all assessed tables |
| **Metadata queryability** | Table and column metadata (types, constraints, descriptions) are queryable via SQL or API | — | — |

## Requirement Keys

Stable identifiers for use in test definitions, threshold config, and remediation templates.

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Structural | Primary key defined | `primary_key_defined` |
| Business | Semantic model coverage | `semantic_model_coverage` |
| Entity | Foreign key coverage | `foreign_key_coverage` |
| Contextual | Temporal scope present | `temporal_scope_present` |

---

## Execution Pattern

1. **Run pk_coverage**: Check constraint metadata
2. **Run fk_coverage**: Check foreign key definitions
3. **Run comment_coverage**: Check column comments
4. **Run table_comment_coverage**: Check table comments
5. **List gaps**: Find specific tables/columns missing context
6. **Generate fixes**: Create ALTER/COMMENT statements
7. **Optional**: Use AI_GENERATE_TABLE_DESC for auto-generated descriptions
