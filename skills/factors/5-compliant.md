# Factor 5: Compliant

**Definition:** Data is governed with explicit ownership, enforced access boundaries, and AI-specific safeguards.

## Why It Matters for AI

AI introduces novel governance surface area that traditional data governance doesn't cover:

- **PII leaks through embeddings:** Personal data encoded in vector representations can't be masked at query time — it's baked into the model. Once trained, the PII is permanent.
- **Bias encoded in training distributions:** A biased dataset produces a biased model. The bias becomes structural, affecting every inference the model serves.
- **Model outputs as regulated decisions:** Credit scoring, hiring, content moderation — AI outputs increasingly fall under regulatory scrutiny (EU AI Act, CCPA, GDPR).
- **Consent and purpose limitations:** Data collected for analytics may not be permissible for training. Purpose creep from "reporting" to "AI training" may violate original consent.

Traditional RBAC and audit logs are necessary but insufficient. You need:
- **Technical protection:** Masking, anonymization applied *before* AI consumption — not at query time
- **Classification:** Sensitive data identified and tagged so policies can be enforced automatically
- **Purpose boundaries:** Explicit permissions for which AI systems can access what data for what purposes

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for governance gaps: Moderate.** Humans access data through controlled interfaces. RBAC and audit logs provide reasonable protection.

**L2 (RAG and retrieval systems)** — **Tolerance for governance gaps: Low.** The model may surface sensitive information in responses. PII must be masked before indexing. Access controls must prevent retrieval of restricted content.

**L3 (ML model training and fine-tuning)** — **Tolerance for governance gaps: Very low.** Training data becomes permanent. PII in training data is PII in the model. Bias in training data is bias in every inference. EU AI Act requires documented, representative datasets with provenance.

---

## Requirements

| Key | Description | Direction | L1 | L2 | L3 |
|-----|-------------|-----------|----|----|-----|
| `masking_policy_coverage` | Fraction of PII columns with masking policies | gte | 0.50 | 0.80 | 1.00 |
| `row_access_policy_coverage` | Fraction of tables with row access policies | gte | 0.30 | 0.60 | 0.90 |
| `sensitive_column_tagged` | Fraction of sensitive columns with classification tags | gte | 0.50 | 0.80 | 1.00 |

**Direction `gte`** = higher is better. Value must be ≥ threshold to pass.

---

## Assessment SQL (Snowflake)

### masking_policy_coverage
```sql
WITH pii_columns AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.columns
    WHERE table_schema = '{schema}'
      AND (
        LOWER(column_name) LIKE '%email%'
        OR LOWER(column_name) LIKE '%phone%'
        OR LOWER(column_name) LIKE '%ssn%'
        OR LOWER(column_name) LIKE '%password%'
        OR LOWER(column_name) LIKE '%credit_card%'
        OR LOWER(column_name) LIKE '%address%'
      )
),
masked_columns AS (
    SELECT COUNT(DISTINCT ref_column_name) AS cnt
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}'
      AND policy_kind = 'MASKING_POLICY'
)
SELECT masked_columns.cnt::FLOAT / NULLIF(pii_columns.cnt::FLOAT, 0) AS value
FROM pii_columns, masked_columns;
```

### row_access_policy_coverage
```sql
WITH table_count AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE'
),
rap_tables AS (
    SELECT COUNT(DISTINCT ref_entity_name) AS cnt
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}'
      AND policy_kind = 'ROW_ACCESS_POLICY'
)
SELECT rap_tables.cnt::FLOAT / NULLIF(table_count.cnt::FLOAT, 0) AS value
FROM table_count, rap_tables;
```

### sensitive_column_tagged
```sql
WITH sensitive_columns AS (
    SELECT COUNT(*) AS cnt
    FROM information_schema.columns
    WHERE table_schema = '{schema}'
      AND (
        LOWER(column_name) LIKE '%email%'
        OR LOWER(column_name) LIKE '%phone%'
        OR LOWER(column_name) LIKE '%ssn%'
        OR LOWER(column_name) LIKE '%salary%'
        OR LOWER(column_name) LIKE '%password%'
        OR LOWER(column_name) LIKE '%credit%'
        OR LOWER(column_name) LIKE '%income%'
      )
),
tagged_sensitive AS (
    SELECT COUNT(DISTINCT column_name) AS cnt
    FROM snowflake.account_usage.tag_references
    WHERE object_schema = '{schema}'
      AND domain = 'COLUMN'
      AND (tag_name ILIKE '%pii%' OR tag_name ILIKE '%sensitiv%')
      AND deleted IS NULL
)
SELECT tagged_sensitive.cnt::FLOAT / NULLIF(sensitive_columns.cnt::FLOAT, 0) AS value
FROM sensitive_columns, tagged_sensitive;
```

### PII columns without protection
```sql
WITH pii_columns AS (
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = '{schema}'
      AND (
        LOWER(column_name) LIKE '%email%'
        OR LOWER(column_name) LIKE '%phone%'
        OR LOWER(column_name) LIKE '%ssn%'
        OR LOWER(column_name) LIKE '%password%'
        OR LOWER(column_name) LIKE '%credit_card%'
      )
),
protected AS (
    SELECT ref_entity_name AS table_name, ref_column_name AS column_name
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}'
      AND policy_kind = 'MASKING_POLICY'
)
SELECT p.table_name, p.column_name, 'NEEDS MASKING' AS status
FROM pii_columns p
LEFT JOIN protected pr ON p.table_name = pr.table_name AND p.column_name = pr.column_name
WHERE pr.column_name IS NULL;
```

---

## AI-Specific Considerations

For AI workloads, compliance is critical:
- **L2 (RAG)**: Masked data may appear in generated responses
- **L3 (Training)**: PII in training data risks memorization

Always ensure:
1. PII columns are masked before AI consumption
2. Row access policies prevent unauthorized data in training sets
3. Sensitive columns are tagged for governance visibility

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)

---

## Remediation

### Create Masking Policies
```sql
-- Email masking policy
CREATE OR REPLACE MASKING POLICY {database}.{schema}.email_mask AS (val STRING) 
RETURNS STRING ->
CASE 
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN', 'DATA_ENGINEER') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST') THEN 
        REGEXP_REPLACE(val, '(.)[^@]*(@.*)', '\\1***\\2')
    ELSE '***@***.***'
END;

-- Phone masking policy
CREATE OR REPLACE MASKING POLICY {database}.{schema}.phone_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN', 'DATA_ENGINEER') THEN val
    ELSE CONCAT('***-***-', RIGHT(REGEXP_REPLACE(val, '[^0-9]', ''), 4))
END;

-- Full redaction policy
CREATE OR REPLACE MASKING POLICY {database}.{schema}.full_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
    ELSE '***REDACTED***'
END;
```

### Apply Masking Policies
```sql
ALTER TABLE {database}.{schema}.{table} MODIFY COLUMN {column} 
    SET MASKING POLICY {database}.{schema}.email_mask;
```

### Create Row Access Policies
```sql
-- Simple role-based RAP
CREATE OR REPLACE ROW ACCESS POLICY {database}.{schema}.role_based_rap AS (binding_col VARCHAR)
RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN TRUE
    WHEN CURRENT_ROLE() = 'DATA_ENGINEER' THEN TRUE
    WHEN CURRENT_ROLE() = 'ANALYST' THEN TRUE
    ELSE FALSE
END;

-- Apply RAP
ALTER TABLE {database}.{schema}.{table} 
    ADD ROW ACCESS POLICY {database}.{schema}.role_based_rap ON ({binding_column});
```

### Tag Sensitive Columns
```sql
CREATE TAG IF NOT EXISTS {database}.{schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS {database}.{schema}.pii
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card', 'dob';

ALTER TABLE {database}.{schema}.{table} MODIFY COLUMN {column} 
    SET TAG {database}.{schema}.pii = '{type}',
    SET TAG {database}.{schema}.sensitivity = 'confidential';
```

### Auto-Classification (Enterprise)
```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFICATION_SCHEMA(
    TABLE_NAME => '{database}.{schema}.{table}'
));

CALL ASSOCIATE_SEMANTIC_CATEGORY_TAGS(
    '{database}.{schema}.{table}',
    EXTRACT_SEMANTIC_CATEGORIES('{database}.{schema}.{table}')
);
```

---

## Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Dynamic masking** | Platform supports column-level masking policies | Role-based conditional masking | — |
| **Row access policies** | Platform supports row-level security | Context-aware policies (role, time, purpose) | — |
| **Sensitivity tags** | Platform supports data classification tags | Tags drive automated policy application | — |

## Requirement Keys

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| PII Protection | Masking policies | `masking_policy_coverage` |
| PII Protection | Row-level security | `row_access_policy_coverage` |
| Classification | Sensitivity classification | `sensitive_column_tagged` |

## Not Yet Implemented

These requirements address AI-specific compliance challenges but are not yet testable:

- **Pre-training anonymization:** PII removed or anonymized before embedding generation
- **Bias assessment metadata:** Fairness metrics and demographic error rates on models
- **Legal basis metadata:** Documented consent, legitimate interest, or contractual basis
- **Training data provenance:** Source documentation for training datasets
- **Erasure-ready identifiers:** Ability to locate and delete personal data across all stores
- **Decision reconstruction:** Link decisions to inputs, model version, and context
- **Purpose boundaries:** Declared scope for which AI systems can access what data

---

## Execution Pattern

1. **Run masking_policy_coverage**: Query `policy_references` for MASKING_POLICY
2. **Run row_access_policy_coverage**: Query `policy_references` for ROW_ACCESS_POLICY
3. **Run sensitive_column_tagged**: Cross-reference sensitive columns with tag_references
4. **List gaps**: Find PII columns without protection
5. **Compare to threshold**: Use L1/L2/L3 based on user's workload
6. **Generate fixes**: Create policies and apply to columns/tables
