-- ============================================================================
-- Fix Script: Compliant Factor
-- ============================================================================
-- Remediates Compliant factor issues identified by the assessment.
-- Creates and applies masking policies, row access policies, and tags.
--
-- Prerequisites: Run snowflake_tags.sql and snowflake_fix_correlated.sql first.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Masking Policies for PII Columns
-- ----------------------------------------------------------------------------

-- Create email masking policy
-- Admins see full email, analysts see masked version, others see fully redacted
CREATE OR REPLACE MASKING POLICY email_mask AS (val STRING) 
RETURNS STRING ->
CASE 
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST', 'DATA_ENGINEER') THEN 
        REGEXP_REPLACE(val, '(.)[^@]*(@.*)', '\\1***\\2')
    ELSE '***@***.***'
END;

-- Create phone masking policy
-- Admins see full phone, others see last 4 digits only
CREATE OR REPLACE MASKING POLICY phone_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST', 'DATA_ENGINEER') THEN 
        CONCAT('***-***-', RIGHT(REGEXP_REPLACE(val, '[^0-9]', ''), 4))
    ELSE '***-***-****'
END;

-- Create name masking policy
-- Admins see full name, others see initials
CREATE OR REPLACE MASKING POLICY name_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST', 'DATA_ENGINEER') THEN 
        CONCAT(LEFT(val, 1), '*** ', LEFT(SPLIT_PART(val, ' ', -1), 1), '***')
    ELSE '*** ***'
END;

-- Apply masking policies to CUSTOMERS table
ALTER TABLE CUSTOMERS MODIFY COLUMN email 
    SET MASKING POLICY email_mask;
ALTER TABLE CUSTOMERS MODIFY COLUMN phone 
    SET MASKING POLICY phone_mask;
ALTER TABLE CUSTOMERS MODIFY COLUMN name 
    SET MASKING POLICY name_mask;

-- Verify masking policies applied
SELECT 'Masking policies applied' AS section;
SELECT 
    ref_entity_name AS table_name,
    ref_column_name AS column_name,
    policy_name
FROM information_schema.policy_references
WHERE ref_schema_name = 'ECOMMERCE'
  AND policy_kind = 'MASKING_POLICY';

-- Test masking (as current role)
SELECT 'Masking test (current role: ' || CURRENT_ROLE() || ')' AS test;
SELECT customer_id, email, phone, name FROM CUSTOMERS LIMIT 3;

-- ----------------------------------------------------------------------------
-- Fix: Row Access Policies
-- ----------------------------------------------------------------------------

-- Create a simple row access policy for CUSTOMERS
-- In production, this would integrate with actual user/role mapping
CREATE OR REPLACE ROW ACCESS POLICY customer_rap AS (cust_id VARCHAR)
RETURNS BOOLEAN ->
CASE
    -- Admins can see all rows
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN TRUE
    -- Data engineers can see all rows
    WHEN CURRENT_ROLE() = 'DATA_ENGINEER' THEN TRUE
    -- Analysts can see all rows (in demo; in prod might be filtered)
    WHEN CURRENT_ROLE() = 'ANALYST' THEN TRUE
    -- Others: no access
    ELSE FALSE
END;

-- Apply row access policy to CUSTOMERS
ALTER TABLE CUSTOMERS ADD ROW ACCESS POLICY customer_rap ON (customer_id);

-- Create and apply simpler RAP for ORDERS (region-based would be more realistic)
CREATE OR REPLACE ROW ACCESS POLICY order_rap AS (order_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN', 'DATA_ENGINEER', 'ANALYST', 'ORDERS_TEAM');

ALTER TABLE ORDERS ADD ROW ACCESS POLICY order_rap ON (order_id);

-- Verify row access policies applied
SELECT 'Row access policies applied' AS section;
SELECT 
    ref_entity_name AS table_name,
    policy_name
FROM information_schema.policy_references
WHERE ref_schema_name = 'ECOMMERCE'
  AND policy_kind = 'ROW_ACCESS_POLICY';

-- ----------------------------------------------------------------------------
-- Fix: Sensitive Column Tags (if not already done in correlated fix)
-- ----------------------------------------------------------------------------

-- Ensure PII columns have sensitivity tags
-- These may already exist from correlated fix, using IF NOT EXISTS pattern

-- Re-apply to ensure (SET TAG is idempotent)
ALTER TABLE CUSTOMERS MODIFY COLUMN email 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
ALTER TABLE CUSTOMERS MODIFY COLUMN phone 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
ALTER TABLE CUSTOMERS MODIFY COLUMN name 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';

-- Tag customer_id as internal (not public, but not PII)
ALTER TABLE CUSTOMERS MODIFY COLUMN customer_id 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== COMPLIANT FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Masking policies created and applied: email_mask, phone_mask, name_mask' AS info;
SELECT 'Row access policies created and applied: customer_rap, order_rap' AS info;
SELECT 'Sensitivity tags verified on PII columns.' AS info;
SELECT 'Re-run assessment to see improved Compliant factor scores.' AS next_step;

-- ----------------------------------------------------------------------------
-- Demo: Test the masking
-- ----------------------------------------------------------------------------

SELECT '=== MASKING DEMO ===' AS section;
SELECT 'Query CUSTOMERS as ' || CURRENT_ROLE() || ':' AS test;
SELECT customer_id, email, phone, name FROM CUSTOMERS LIMIT 5;

-- To test as different role:
-- USE ROLE ANALYST;
-- SELECT customer_id, email, phone, name FROM AIRD_DEMO.ECOMMERCE.CUSTOMERS LIMIT 5;
