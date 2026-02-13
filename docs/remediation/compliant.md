# Compliant Factor Remediation

**Factor 5: Compliant** — Is the data governed with explicit ownership, enforced access boundaries, and AI-specific safeguards?

Reference: `/factors.md` § Compliant

---

## masking_policy_coverage

**Problem:** PII columns lack masking policies.

**Diagnosis:**
```sql
-- Find PII columns without masking policies
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
masked_columns AS (
    SELECT ref_entity_name AS table_name, ref_column_name AS column_name
    FROM information_schema.policy_references
    WHERE ref_schema_name = '{schema}'
      AND policy_kind = 'MASKING_POLICY'
)
SELECT p.table_name, p.column_name, 
       CASE WHEN m.column_name IS NULL THEN 'NEEDS MASKING' ELSE 'OK' END AS status
FROM pii_columns p
LEFT JOIN masked_columns m 
    ON p.table_name = m.table_name AND p.column_name = m.column_name;
```

**Fix Patterns:**

```sql
-- Create email masking policy
CREATE OR REPLACE MASKING POLICY {schema}.email_mask AS (val STRING) 
RETURNS STRING ->
CASE 
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN', 'DATA_ENGINEER') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST') THEN 
        REGEXP_REPLACE(val, '(.)[^@]*(@.*)', '\\1***\\2')
    ELSE '***@***.***'
END;

-- Create phone masking policy
CREATE OR REPLACE MASKING POLICY {schema}.phone_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN', 'DATA_ENGINEER') THEN val
    ELSE CONCAT('***-***-', RIGHT(REGEXP_REPLACE(val, '[^0-9]', ''), 4))
END;

-- Create SSN masking policy
CREATE OR REPLACE MASKING POLICY {schema}.ssn_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val
    ELSE CONCAT('***-**-', RIGHT(val, 4))
END;

-- Create generic string masking (full redaction)
CREATE OR REPLACE MASKING POLICY {schema}.full_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
    ELSE '***REDACTED***'
END;

-- Apply masking policies
ALTER TABLE {schema}.{table} MODIFY COLUMN {column} 
    SET MASKING POLICY {schema}.email_mask;
```

**Dynamic Masking (Using Tags):**
```sql
-- Create tag-based masking policy
CREATE OR REPLACE MASKING POLICY {schema}.pii_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('pii') IS NOT NULL THEN '***PII***'
    ELSE val
END;
```

**Test Masking:**
```sql
-- Test as different roles
USE ROLE ACCOUNTADMIN;
SELECT email, phone FROM {schema}.CUSTOMERS LIMIT 3;

USE ROLE ANALYST;
SELECT email, phone FROM {schema}.CUSTOMERS LIMIT 3;

USE ROLE PUBLIC;
SELECT email, phone FROM {schema}.CUSTOMERS LIMIT 3;
```

---

## row_access_policy_coverage

**Problem:** Tables lack row-level security.

**Diagnosis:**
```sql
-- Check tables with row access policies
SELECT 
    t.table_name,
    CASE WHEN pr.policy_name IS NULL THEN 'NO RAP' ELSE 'HAS RAP' END AS rap_status
FROM information_schema.tables t
LEFT JOIN information_schema.policy_references pr
    ON t.table_name = pr.ref_entity_name
    AND t.table_schema = pr.ref_schema_name
    AND pr.policy_kind = 'ROW_ACCESS_POLICY'
WHERE t.table_schema = '{schema}'
  AND t.table_type = 'BASE TABLE';
```

**Fix Patterns:**

```sql
-- Simple role-based RAP
CREATE OR REPLACE ROW ACCESS POLICY {schema}.role_based_rap AS (binding_col VARCHAR)
RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN TRUE
    WHEN CURRENT_ROLE() = 'DATA_ENGINEER' THEN TRUE
    WHEN CURRENT_ROLE() = 'ANALYST' THEN TRUE
    ELSE FALSE
END;

-- User-based RAP (users see only their own data)
CREATE OR REPLACE ROW ACCESS POLICY {schema}.user_data_rap AS (owner_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
    OR owner_id = CURRENT_USER();

-- Region-based RAP
CREATE OR REPLACE ROW ACCESS POLICY {schema}.region_rap AS (region VARCHAR)
RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
    WHEN CURRENT_ROLE() = 'NA_ANALYST' AND region = 'NA' THEN TRUE
    WHEN CURRENT_ROLE() = 'EMEA_ANALYST' AND region = 'EMEA' THEN TRUE
    WHEN CURRENT_ROLE() = 'APAC_ANALYST' AND region = 'APAC' THEN TRUE
    ELSE FALSE
END;

-- Apply RAP to table
ALTER TABLE {schema}.{table} ADD ROW ACCESS POLICY {schema}.role_based_rap ON ({binding_column});
```

**Mapping Table Pattern:**
```sql
-- Create mapping table for flexible access control
CREATE TABLE {schema}.USER_ACCESS_MAPPING (
    user_name VARCHAR,
    allowed_tenant_id VARCHAR,
    access_level VARCHAR
);

-- RAP using mapping table
CREATE OR REPLACE ROW ACCESS POLICY {schema}.mapping_rap AS (tenant_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN') 
    OR EXISTS (
        SELECT 1 FROM {schema}.USER_ACCESS_MAPPING
        WHERE user_name = CURRENT_USER()
          AND allowed_tenant_id = tenant_id
    );
```

---

## sensitive_column_tagged

**Problem:** Sensitive columns lack classification tags.

**Diagnosis:**
```sql
-- Find sensitive columns by naming pattern
SELECT 
    table_name, 
    column_name,
    SYSTEM$GET_TAG('{schema}.sensitivity', 
        CONCAT('{database}.{schema}.', table_name, '.', column_name), 'COLUMN') AS sensitivity_tag,
    SYSTEM$GET_TAG('{schema}.pii', 
        CONCAT('{database}.{schema}.', table_name, '.', column_name), 'COLUMN') AS pii_tag
FROM information_schema.columns
WHERE table_schema = '{schema}'
  AND (
    LOWER(column_name) LIKE '%email%'
    OR LOWER(column_name) LIKE '%phone%'
    OR LOWER(column_name) LIKE '%ssn%'
    OR LOWER(column_name) LIKE '%salary%'
    OR LOWER(column_name) LIKE '%income%'
    OR LOWER(column_name) LIKE '%address%'
  );
```

**Fix Patterns:**

```sql
-- Create sensitivity tags
CREATE TAG IF NOT EXISTS {schema}.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS {schema}.pii
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card', 'dob';

CREATE TAG IF NOT EXISTS {schema}.data_classification
    ALLOWED_VALUES 'public', 'pii', 'phi', 'pci', 'confidential';

-- Apply tags to sensitive columns
ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN email 
    SET TAG {schema}.pii = 'email',
    SET TAG {schema}.sensitivity = 'confidential';

ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN phone
    SET TAG {schema}.pii = 'phone',
    SET TAG {schema}.sensitivity = 'confidential';

ALTER TABLE {schema}.CUSTOMERS MODIFY COLUMN name
    SET TAG {schema}.pii = 'name',
    SET TAG {schema}.sensitivity = 'confidential';
```

**Auto-Classification:**
```sql
-- Use Snowflake's classification feature (Enterprise)
-- Analyze table for sensitive data
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFICATION_SCHEMA(
    TABLE_NAME => '{schema}.{table}'
));

-- Apply automatic classification tags
CALL ASSOCIATE_SEMANTIC_CATEGORY_TAGS(
    '{schema}.{table}',
    EXTRACT_SEMANTIC_CATEGORIES('{schema}.{table}')
);
```
