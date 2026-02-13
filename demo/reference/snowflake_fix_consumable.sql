-- ============================================================================
-- Fix Script: Consumable Factor
-- ============================================================================
-- Remediates Consumable factor issues identified by the assessment.
-- Focuses on performance: clustering and search optimization.
--
-- Note: Documentation (table/column comments) is addressed in the Contextual
-- factor fix script as it relates to making meaning explicit.
-- ============================================================================

USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Clustering (for large tables)
-- ----------------------------------------------------------------------------

-- Cluster EVENTS by timestamp for time-range queries (most common access pattern)
ALTER TABLE EVENTS CLUSTER BY (event_timestamp, event_type);

-- Cluster ORDER_ITEMS by order_id for join performance
ALTER TABLE ORDER_ITEMS CLUSTER BY (order_id);

-- Cluster ORDERS by date for time-based queries
ALTER TABLE ORDERS CLUSTER BY (TO_DATE(created_at));

-- Verify
SELECT 'Tables with clustering keys' AS metric,
       table_name,
       clustering_key
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE' 
  AND clustering_key IS NOT NULL;

-- ----------------------------------------------------------------------------
-- Fix: Search Optimization (for text-heavy tables)
-- ----------------------------------------------------------------------------

-- Enable search optimization on PRODUCTS for text search on name and description
ALTER TABLE PRODUCTS ADD SEARCH OPTIMIZATION ON SUBSTRING(name), SUBSTRING(description);

-- Enable search optimization on CUSTOMERS for email lookup
ALTER TABLE CUSTOMERS ADD SEARCH OPTIMIZATION ON EQUALITY(email);

-- Enable search optimization on EVENTS for event_type filtering
ALTER TABLE EVENTS ADD SEARCH OPTIMIZATION ON EQUALITY(event_type);

-- Verify
SELECT 'Tables with search optimization' AS metric,
       table_name,
       search_optimization
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE' 
  AND search_optimization = 'ON';

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== CONSUMABLE FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Clustering added to EVENTS, ORDER_ITEMS, ORDERS.' AS info;
SELECT 'Search optimization added to PRODUCTS, CUSTOMERS, EVENTS.' AS info;
SELECT 'Re-run assessment to see improved Consumable factor scores.' AS next_step;
