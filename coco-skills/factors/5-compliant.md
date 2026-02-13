# Factor 5: Compliant

**Definition:** Data is governed with explicit ownership, enforced access boundaries, and AI-specific safeguards.

## Why It Matters for AI

AI amplifies compliance risks. A RAG system can surface PII in responses. Training data can encode protected information into model weights. Compliant data has explicit policies — masking, row-level security, classification — that prevent AI from inadvertently exposing or learning from data it shouldn't access.

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

### Detailed masking policy inventory
```sql
SELECT 
    ref_entity_name AS table_name,
    ref_column_name AS column_name,
    policy_name,
    policy_kind
FROM information_schema.policy_references
WHERE ref_schema_name = '{schema}'
  AND policy_kind = 'MASKING_POLICY'
ORDER BY ref_entity_name, ref_column_name;
```

### Detailed row access policy inventory
```sql
SELECT 
    ref_entity_name AS table_name,
    policy_name,
    policy_kind
FROM information_schema.policy_references
WHERE ref_schema_name = '{schema}'
  AND policy_kind = 'ROW_ACCESS_POLICY'
ORDER BY ref_entity_name;
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

### Sensitive Data Classification (Enterprise)
```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFICATION_SCHEMA(
    TABLE_NAME => '{database}.{schema}.{table}'
));
```

---

## Interpretation

- `gte` direction = higher is better (1.0 is perfect)
- Value ≥ threshold = PASS
- Value < threshold = FAIL (suggest remediation)

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

-- SSN masking policy
CREATE OR REPLACE MASKING POLICY {database}.{schema}.ssn_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val
    ELSE CONCAT('***-**-', RIGHT(val, 4))
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

### Test Masking
```sql
-- Test as different roles
USE ROLE ACCOUNTADMIN;
SELECT email, phone FROM {database}.{schema}.CUSTOMERS LIMIT 3;

USE ROLE ANALYST;
SELECT email, phone FROM {database}.{schema}.CUSTOMERS LIMIT 3;
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

-- User-based RAP (users see only their own data)
CREATE OR REPLACE ROW ACCESS POLICY {database}.{schema}.user_data_rap AS (owner_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
    OR owner_id = CURRENT_USER();

-- Region-based RAP
CREATE OR REPLACE ROW ACCESS POLICY {database}.{schema}.region_rap AS (region VARCHAR)
RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
    WHEN CURRENT_ROLE() = 'NA_ANALYST' AND region = 'NA' THEN TRUE
    WHEN CURRENT_ROLE() = 'EMEA_ANALYST' AND region = 'EMEA' THEN TRUE
    WHEN CURRENT_ROLE() = 'APAC_ANALYST' AND region = 'APAC' THEN TRUE
    ELSE FALSE
END;
```

### Apply Row Access Policies
```sql
ALTER TABLE {database}.{schema}.{table} 
    ADD ROW ACCESS POLICY {database}.{schema}.role_based_rap ON ({binding_column});
```

### Mapping Table Pattern
```sql
-- Create mapping table for flexible access control
CREATE TABLE {database}.{schema}.USER_ACCESS_MAPPING (
    user_name VARCHAR,
    allowed_tenant_id VARCHAR,
    access_level VARCHAR
);

-- RAP using mapping table
CREATE OR REPLACE ROW ACCESS POLICY {database}.{schema}.mapping_rap AS (tenant_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN') 
    OR EXISTS (
        SELECT 1 FROM {database}.{schema}.USER_ACCESS_MAPPING
        WHERE user_name = CURRENT_USER()
          AND allowed_tenant_id = tenant_id
    );
```

### Tag Sensitive Columns
```sql
-- Create sensitivity tags
CREATE TAG IF NOT EXISTS {database}.{schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS {database}.{schema}.pii
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card', 'dob';

CREATE TAG IF NOT EXISTS {database}.{schema}.data_classification
    ALLOWED_VALUES 'public', 'pii', 'phi', 'pci', 'confidential';

-- Apply tags to sensitive columns
ALTER TABLE {database}.{schema}.CUSTOMERS MODIFY COLUMN email 
    SET TAG {database}.{schema}.pii = 'email',
    SET TAG {database}.{schema}.sensitivity = 'confidential';

ALTER TABLE {database}.{schema}.CUSTOMERS MODIFY COLUMN phone
    SET TAG {database}.{schema}.pii = 'phone',
    SET TAG {database}.{schema}.sensitivity = 'confidential';
```

### Auto-Classification (Enterprise)
```sql
-- Analyze table for sensitive data
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFICATION_SCHEMA(
    TABLE_NAME => '{database}.{schema}.{table}'
));

-- Apply automatic classification tags
CALL ASSOCIATE_SEMANTIC_CATEGORY_TAGS(
    '{database}.{schema}.{table}',
    EXTRACT_SEMANTIC_CATEGORIES('{database}.{schema}.{table}')
);
```

---

## Execution Pattern

1. **Run masking_policy_coverage**: Query `policy_references` for MASKING_POLICY
2. **Run row_access_policy_coverage**: Query `policy_references` for ROW_ACCESS_POLICY
3. **Run sensitive_column_tagged**: Cross-reference sensitive columns with tag_references
4. **List gaps**: Find PII columns without protection
5. **Compare to threshold**: Use L1/L2/L3 based on user's workload
6. **Generate fixes**: Create policies and apply to columns/tables
