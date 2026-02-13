-- ============================================================================
-- Fix Script: Correlated Factor
-- ============================================================================
-- Remediates Correlated factor issues identified by the assessment.
-- Applies object and column tags for classification and lineage.
--
-- Prerequisites: Run snowflake_tags.sql first to create the tag definitions.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Object (Table) Tags
-- ----------------------------------------------------------------------------

-- Apply data_domain tags to all tables
ALTER TABLE CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'customer';
ALTER TABLE ORDERS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'order';
ALTER TABLE ORDER_ITEMS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'order';
ALTER TABLE PRODUCTS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'product';
ALTER TABLE EVENTS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'event';

-- Apply owner tags (assuming teams)
ALTER TABLE CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'customer-data-team';
ALTER TABLE ORDERS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'orders-team';
ALTER TABLE ORDER_ITEMS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'orders-team';
ALTER TABLE PRODUCTS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'product-team';
ALTER TABLE EVENTS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'analytics-team';

-- Apply sensitivity tags at table level
ALTER TABLE CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
ALTER TABLE ORDERS SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';
ALTER TABLE ORDER_ITEMS SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';
ALTER TABLE PRODUCTS SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'public';
ALTER TABLE EVENTS SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';

-- Apply freshness SLA tags
ALTER TABLE CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.freshness_sla = '24h';
ALTER TABLE ORDERS SET TAG AIRD_DEMO.ECOMMERCE.freshness_sla = '1h';
ALTER TABLE ORDER_ITEMS SET TAG AIRD_DEMO.ECOMMERCE.freshness_sla = '1h';
ALTER TABLE PRODUCTS SET TAG AIRD_DEMO.ECOMMERCE.freshness_sla = '7d';
ALTER TABLE EVENTS SET TAG AIRD_DEMO.ECOMMERCE.freshness_sla = '1h';

-- Verify table tags
-- Note: tag_references may have up to 3-hour latency
SELECT 'Object tags applied (check may have latency)' AS note;

-- ----------------------------------------------------------------------------
-- Fix: Column Tags (PII and sensitivity)
-- ----------------------------------------------------------------------------

-- Tag PII columns in CUSTOMERS
ALTER TABLE CUSTOMERS MODIFY COLUMN email 
    SET TAG AIRD_DEMO.ECOMMERCE.pii = 'email';
ALTER TABLE CUSTOMERS MODIFY COLUMN phone 
    SET TAG AIRD_DEMO.ECOMMERCE.pii = 'phone';
ALTER TABLE CUSTOMERS MODIFY COLUMN name 
    SET TAG AIRD_DEMO.ECOMMERCE.pii = 'name';

-- Tag sensitivity on PII columns
ALTER TABLE CUSTOMERS MODIFY COLUMN email 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
ALTER TABLE CUSTOMERS MODIFY COLUMN phone 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
ALTER TABLE CUSTOMERS MODIFY COLUMN name 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';

-- Tag financial columns in ORDERS
ALTER TABLE ORDERS MODIFY COLUMN total_amount 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';

-- Tag financial columns in PRODUCTS
ALTER TABLE PRODUCTS MODIFY COLUMN price 
    SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'internal';

-- Verify column tags (using system function, works immediately)
SELECT 
    'CUSTOMERS.email' AS column_ref,
    SYSTEM$GET_TAG('AIRD_DEMO.ECOMMERCE.pii', 'AIRD_DEMO.ECOMMERCE.CUSTOMERS.email', 'COLUMN') AS pii_tag,
    SYSTEM$GET_TAG('AIRD_DEMO.ECOMMERCE.sensitivity', 'AIRD_DEMO.ECOMMERCE.CUSTOMERS.email', 'COLUMN') AS sensitivity_tag;

-- ----------------------------------------------------------------------------
-- Verify Lineage Queryability
-- ----------------------------------------------------------------------------

-- Lineage is automatic via ACCESS_HISTORY - just verify we can query it
-- This requires ACCOUNTADMIN or GOVERNANCE_VIEWER role

SELECT 'Lineage verification' AS section;

-- Sample lineage query (last 24 hours)
SELECT 
    query_id,
    user_name,
    query_start_time,
    ARRAY_SIZE(direct_objects_accessed) AS objects_accessed_count
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE query_start_time > DATEADD('day', -1, CURRENT_TIMESTAMP())
LIMIT 5;

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== CORRELATED FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Data domain tags applied to all 5 tables.' AS info;
SELECT 'Owner tags applied to all 5 tables.' AS info;
SELECT 'PII tags applied to email, phone, name columns.' AS info;
SELECT 'Sensitivity tags applied to sensitive columns.' AS info;
SELECT 'Note: tag_references view may have up to 3-hour latency.' AS note;
SELECT 'Re-run assessment to see improved Correlated factor scores.' AS next_step;
