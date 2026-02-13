# Factor 0: Clean

**Definition:** Clean data is consistently accurate, complete, valid, and free of errors that would compromise downstream consumption.

## Why It Matters for AI

The importance of data quality is nothing new, but the consequences of poor data quality are dramatically increased when used by AI systems.

Clean data is not perfect data. Perfection is neither achievable nor necessary. What matters is that data is clean *enough* for the workload it feeds. Different workloads have materially different tolerance thresholds for data quality. The demands escalate as the system's autonomy increases and as the cost of errors shifts from recoverable to permanent.

Clean data is Factor 0 because nothing else in the framework matters without it. Context, consumability, freshness, lineage, and compliance all assume that the underlying data is trustworthy. If it isn't, you are building on a foundation that will fail — not loudly or immediately, but quietly and pervasively.

Models optimize on whatever signal is present — including noise. Dirty data doesn't just degrade output quality; it gets encoded into weights and embeddings as learned patterns, making errors systematic and hard to detect downstream.

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for dirty data: Moderate.** Humans are in the loop. They interpret results, notice anomalies, and ask clarifying questions before acting.

**L2 (RAG and retrieval systems)** — **Tolerance for dirty data: Low.** The model selects chunks from your corpus and presents them — often verbatim — as answers. Any individual chunk can become the basis of a response.

**L3 (ML model training and fine-tuning)** — **Tolerance for dirty data: Very low.** Errors in training data are not retrieved — they are *learned*. The model encodes patterns from the training distribution into its weights. A bias, a labeling error, or a systematic data quality issue produces a model that is structurally inclined toward wrong answers across every inference it serves. Remediation means retraining.

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

## Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Validation & quality checks** | Schema validation at ingestion (type checks, range constraints, mandatory fields) | — | Automated quality gates that block training runs when data quality thresholds are not met |
| **Profiling & baselines** | Data profiling to establish and track quality baselines over time | — | Distribution drift monitoring against the distribution the model was trained on |
| **Deduplication** | Deduplication logic applied during ingestion or transformation | Corpus-level deduplication with similarity detection for near-duplicates | — |
| **Alerting** | Alerting on validation rule failures so issues are surfaced | — | — |

## Requirement Keys

Stable identifiers for use in test definitions, threshold config, and remediation templates.

| Requirement (name) | Key |
|--------------------|-----|
| Null handling | `null_rate` |
| Deduplication | `duplicate_rate` |
| Format consistency | `format_inconsistency_rate` |
| Type consistency | `type_inconsistency_rate` |
| Numeric validity | `zero_negative_rate` |

---

## Execution Pattern

1. **Discover columns**: Query `information_schema.columns` for target schema
2. **Run null_rate**: Execute per important column (PKs, required fields)
3. **Run duplicate_rate**: Execute per table
4. **Compare to threshold**: Use L1/L2/L3 based on user's workload
5. **For failures**: Generate remediation SQL from patterns above
