# Factor 4: Correlated

**Definition:** Data is traceable from source to every decision it informs.

## Why It Matters for AI

AI systems are compositional. Data flows through transformations, feature engineering, model inference, and post-processing before producing an output. When something goes wrong — a bad prediction, a hallucinated answer, a biased decision — you need to trace backward: Was it the source data? A transformation bug? A model issue? A post-processing error?

Without end-to-end traceability, a bad output is a black box.

Traditional analytics has similar needs, but the stakes are different. A wrong dashboard number gets noticed, investigated, fixed. A wrong AI decision may be invisible — or may have already triggered downstream actions before anyone notices.

Correlated data enables:
- **Root cause analysis:** Trace a bad output back to its source
- **Impact analysis:** Understand what's affected when source data changes
- **Reproducibility:** Reconstruct any past decision for audit or debugging
- **Cost attribution:** Know which data and transformations contributed to what outcomes

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for missing traceability: Moderate.** Analysts can investigate issues manually. Lineage is helpful for impact analysis but not critical for every query.

**L2 (RAG and retrieval systems)** — **Tolerance for missing traceability: Low.** When a chatbot gives a wrong answer, you need to know: which chunks were retrieved? What were their sources? What was the ranking? Without this, debugging is guesswork.

**L3 (ML model training and fine-tuning)** — **Tolerance for missing traceability: Very low.** Training data provenance is a regulatory requirement (EU AI Act). You must be able to reconstruct what data trained what model at what time. Drift detection requires baselines to compare against.

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

## Required Permissions

Querying `snowflake.account_usage.tag_references` and `access_history` requires:
- Role with `IMPORTED PRIVILEGES` on SNOWFLAKE database, OR
- `GOVERNANCE_VIEWER` role, OR
- `ACCOUNTADMIN` role

```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {role};
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)
- `lineage_queryable` is binary: 0.0 or 1.0

---

## Remediation

### Create Standard Tags
```sql
CREATE TAG IF NOT EXISTS {database}.{schema}.data_domain
    ALLOWED_VALUES 'customer', 'order', 'product', 'event', 'financial';

CREATE TAG IF NOT EXISTS {database}.{schema}.owner
    COMMENT = 'Team or individual responsible for this data';

CREATE TAG IF NOT EXISTS {database}.{schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS {database}.{schema}.freshness_sla
    ALLOWED_VALUES '1h', '6h', '24h', '7d', '30d';
```

### Apply Tags to Tables
```sql
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.data_domain = '{domain}';
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.owner = '{owner_team}';
ALTER TABLE {database}.{schema}.{table} SET TAG {database}.{schema}.sensitivity = '{level}';
```

### Create and Apply Column-Level Tags
```sql
CREATE TAG IF NOT EXISTS {database}.{schema}.pii 
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card';

ALTER TABLE {database}.{schema}.{table} MODIFY COLUMN {column} 
    SET TAG {database}.{schema}.pii = '{type}';
```

### Auto-Classification (Enterprise)
```sql
SELECT SYSTEM$CLASSIFY('{database}.{schema}.{table}', {'auto_tag': true});
```

### Query Lineage
```sql
-- Find reads for a specific table
SELECT 
    query_id, user_name, query_start_time,
    f.value:objectName::STRING AS object_name
FROM snowflake.account_usage.access_history,
    LATERAL FLATTEN(input => direct_objects_accessed) f
WHERE f.value:objectName::STRING ILIKE '%{table}%'
  AND query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP());
```

---

## Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Tagging infrastructure** | Platform supports object and column tags | Tags are queryable at runtime | Tag inheritance through transformations |
| **Lineage capture** | Automated lineage from SQL | Column-level granularity | Bi-temporal reconstruction |
| **Access history** | Query logs available | Access patterns queryable | Full audit trail |

## Requirement Keys

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Classification | Object classification | `object_tag_coverage` |
| Classification | Column classification | `column_tag_coverage` |
| Lineage | Lineage queryable | `lineage_queryable` |

## Not Yet Implemented

These requirements are not yet testable via automated SQL checks:

- **Data quality signals:** Quality metadata (completeness, freshness scores) attached to data
- **Drift baselines:** Reference distributions stored for comparison
- **Decision traces:** Linked traces from inputs to retrieval to outputs
- **Retrieval quality metadata:** Relevance scores and ranking signals logged per query
- **Faithfulness signals:** Claim support scores and source attribution on outputs

---

## Execution Pattern

1. **Run object_tag_coverage**: Query `tag_references` for TABLE domain
2. **Run column_tag_coverage**: Query `tag_references` for COLUMN domain
3. **Run lineage_queryable**: Test access to `access_history`
4. **List gaps**: Find untagged tables and columns
5. **Compare to threshold**: Use L1/L2/L3 based on user's workload
6. **Generate fixes**: Create TAG and ALTER statements
