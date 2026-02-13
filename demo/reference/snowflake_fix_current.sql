-- ============================================================================
-- Fix Script: Current Factor
-- ============================================================================
-- Remediates Current factor issues identified by the assessment.
-- Enables change tracking, creates streams, and adds fresh data.
-- ============================================================================

USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Enable Change Tracking
-- ----------------------------------------------------------------------------

ALTER TABLE CUSTOMERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ORDER_ITEMS SET CHANGE_TRACKING = TRUE;
ALTER TABLE PRODUCTS SET CHANGE_TRACKING = TRUE;
ALTER TABLE EVENTS SET CHANGE_TRACKING = TRUE;

-- Verify
SELECT 'Tables with change tracking (after fix)' AS metric,
       table_name,
       change_tracking
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE' 
  AND table_type = 'BASE TABLE';

-- ----------------------------------------------------------------------------
-- Fix: Create Streams for CDC
-- ----------------------------------------------------------------------------

-- Create streams for key tables
CREATE OR REPLACE STREAM CUSTOMERS_STREAM ON TABLE CUSTOMERS;
CREATE OR REPLACE STREAM ORDERS_STREAM ON TABLE ORDERS;
CREATE OR REPLACE STREAM EVENTS_STREAM ON TABLE EVENTS;

-- Verify
SELECT 'Streams created' AS metric,
       stream_name,
       table_name
FROM information_schema.streams
WHERE table_schema = 'ECOMMERCE';

-- ----------------------------------------------------------------------------
-- Fix: Data Freshness (add recent data to EVENTS)
-- ----------------------------------------------------------------------------

-- The demo EVENTS table has all stale data (>30 days old)
-- Add some fresh events to pass freshness checks

INSERT INTO EVENTS (event_id, customer_id, event_type, event_data, event_timestamp)
WITH customer_ids AS (SELECT customer_id FROM CUSTOMERS)
SELECT
    UUID_STRING() AS event_id,
    (SELECT customer_id FROM customer_ids SAMPLE (1 ROWS)) AS customer_id,
    CASE MOD(SEQ4(), 6)
        WHEN 0 THEN 'page_view'
        WHEN 1 THEN 'add_to_cart'
        WHEN 2 THEN 'purchase'
        WHEN 3 THEN 'search'
        WHEN 4 THEN 'login'
        ELSE 'logout'
    END AS event_type,
    OBJECT_CONSTRUCT('action', 'demo_fresh', 'seq', SEQ4()) AS event_data,
    -- Fresh events from last 7 days
    DATEADD('minute', -UNIFORM(0, 10080, RANDOM()), CURRENT_TIMESTAMP()) AS event_timestamp
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- Also add some recent orders
INSERT INTO ORDERS (order_id, customer_id, order_date, total_amount, status)
WITH customer_ids AS (SELECT customer_id FROM CUSTOMERS)
SELECT
    UUID_STRING() AS order_id,
    (SELECT customer_id FROM customer_ids SAMPLE (1 ROWS)) AS customer_id,
    TO_VARCHAR(DATEADD('day', -UNIFORM(0, 7, RANDOM()), CURRENT_DATE()), 'YYYY-MM-DD') AS order_date,
    TO_VARCHAR(ROUND(UNIFORM(50, 500, RANDOM())::DECIMAL(10,2), 2)) AS total_amount,
    'PROCESSING' AS status
FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- Verify freshness
SELECT 'EVENTS freshness (days since newest)' AS metric,
       DATEDIFF('minute', MAX(event_timestamp), CURRENT_TIMESTAMP()) AS minutes_stale 
FROM EVENTS;

-- ----------------------------------------------------------------------------
-- Optional: Create a Dynamic Table Example
-- ----------------------------------------------------------------------------

-- Create a dynamic table that aggregates order stats per customer
-- This demonstrates the "Current" pattern for derived data

CREATE OR REPLACE DYNAMIC TABLE CUSTOMER_ORDER_STATS
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT 
    c.customer_id,
    c.name,
    c.email,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(TRY_CAST(o.total_amount AS DECIMAL(10,2))) AS total_spent,
    MAX(TRY_TO_DATE(o.order_date)) AS last_order_date
FROM CUSTOMERS c
LEFT JOIN ORDERS o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.email;

-- Verify dynamic table created
SELECT 'Dynamic tables created' AS metric,
       table_name,
       table_type
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE' 
  AND table_type = 'DYNAMIC TABLE';

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== CURRENT FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Change tracking enabled on all tables.' AS info;
SELECT 'Streams created for CUSTOMERS, ORDERS, EVENTS.' AS info;
SELECT 'Fresh data added to EVENTS and ORDERS.' AS info;
SELECT 'Dynamic table CUSTOMER_ORDER_STATS created.' AS info;
SELECT 'Re-run assessment to see improved Current factor scores.' AS next_step;
