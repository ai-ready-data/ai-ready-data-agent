-- ============================================================================
-- Create Tags for Governance Demo
-- ============================================================================
-- Run this BEFORE the demo if you want tag-based tests to have a baseline.
-- The tags exist but are NOT applied to any objects initially.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- Create PII tag with allowed values
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.pii 
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name', 'credit_card';

-- Create sensitivity classification tag
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

-- Create data domain tag for lineage/ownership
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.data_domain
    ALLOWED_VALUES 'customer', 'order', 'product', 'event', 'financial';

-- Create owner tag
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.owner
    COMMENT = 'Data owner team or individual';

-- Create freshness SLA tag
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.freshness_sla
    ALLOWED_VALUES '1h', '6h', '24h', '7d', '30d'
    COMMENT = 'Expected data freshness SLA';

-- Verify tags created
SHOW TAGS IN SCHEMA ECOMMERCE;

SELECT '=== Tags created ===' AS status;
SELECT 'Tags are NOT applied to any objects yet (intentional for demo).' AS note;
SELECT 'After assessment, use snowflake_fix_correlated.sql to apply tags.' AS next_step;
