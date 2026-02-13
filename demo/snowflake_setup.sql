-- ============================================================================
-- AI-Ready Data Demo: Snowflake Setup Script
-- ============================================================================
-- This script creates a demo database with intentional problems across all 6
-- factors. Run this to set up the "before" state for the demo.
--
-- Prerequisites:
--   - ACCOUNTADMIN role or equivalent
--   - Warehouse with sufficient credits
--
-- Usage:
--   snowsql -a <account> -u <user> -f snowflake_setup.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Create Database and Schema
-- ----------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS AIRD_DEMO;
CREATE SCHEMA IF NOT EXISTS AIRD_DEMO.ECOMMERCE;

USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- 2. Create Tables (WITHOUT proper constraints, comments, etc.)
-- ----------------------------------------------------------------------------

-- CUSTOMERS: Missing updated_at, no PK, PII unprotected
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id VARCHAR(36),
    email VARCHAR(255),          -- Will have 30% NULLs, no masking
    phone VARCHAR(20),           -- Will have 25% NULLs, no masking
    name VARCHAR(100),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    -- NOTE: No PRIMARY KEY
    -- NOTE: No updated_at column
    -- NOTE: No COMMENT
);

-- ORDERS: Mixed date formats, mixed types in total_amount, no PK/FK
CREATE OR REPLACE TABLE ORDERS (
    order_id VARCHAR(36),
    customer_id VARCHAR(36),     -- No FK to CUSTOMERS
    order_date VARCHAR(20),      -- String with mixed formats
    total_amount VARCHAR(20),    -- String with mixed types (numbers + text)
    status VARCHAR(20)
    -- NOTE: No PRIMARY KEY
    -- NOTE: No FOREIGN KEY
    -- NOTE: No timestamps
);

-- ORDER_ITEMS: Negative quantities, no PK/FK
CREATE OR REPLACE TABLE ORDER_ITEMS (
    item_id VARCHAR(36),
    order_id VARCHAR(36),        -- No FK to ORDERS
    product_id VARCHAR(36),      -- No FK to PRODUCTS
    quantity INTEGER,            -- Will have negative/zero values
    unit_price DECIMAL(10,2)
    -- NOTE: No PRIMARY KEY
    -- NOTE: No FOREIGN KEY
    -- NOTE: No timestamps
);

-- PRODUCTS: Zero/negative prices, no PK
CREATE OR REPLACE TABLE PRODUCTS (
    product_id VARCHAR(36),
    name VARCHAR(200),
    category VARCHAR(100),
    price DECIMAL(10,2),         -- Will have zero/negative values
    description TEXT
    -- NOTE: No PRIMARY KEY
    -- NOTE: No COMMENT
    -- NOTE: No search optimization
);

-- EVENTS: Stale data, no PK/FK, no change tracking
CREATE OR REPLACE TABLE EVENTS (
    event_id VARCHAR(36),
    customer_id VARCHAR(36),     -- No FK to CUSTOMERS
    event_type VARCHAR(50),
    event_data VARIANT,
    event_timestamp TIMESTAMP_NTZ
    -- NOTE: No PRIMARY KEY
    -- NOTE: No FOREIGN KEY
    -- NOTE: No clustering (will be large)
    -- NOTE: No change tracking
);

-- ----------------------------------------------------------------------------
-- 3. Insert Products First (needed for ORDER_ITEMS FK simulation)
-- ----------------------------------------------------------------------------

INSERT INTO PRODUCTS (product_id, name, category, price, description)
SELECT
    UUID_STRING() AS product_id,
    CONCAT('Product ', SEQ4()) AS name,
    CASE MOD(SEQ4(), 5)
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Clothing'
        WHEN 2 THEN 'Home & Garden'
        WHEN 3 THEN 'Sports'
        ELSE 'Books'
    END AS category,
    CASE 
        WHEN UNIFORM(0, 100, RANDOM()) < 3 THEN 0
        WHEN UNIFORM(0, 100, RANDOM()) < 5 THEN -UNIFORM(1, 50, RANDOM())
        ELSE ROUND(UNIFORM(10, 500, RANDOM())::DECIMAL(10,2), 2)
    END AS price,
    CONCAT('Description for product ', SEQ4()) AS description
FROM TABLE(GENERATOR(ROWCOUNT => 500));

-- ----------------------------------------------------------------------------
-- 4. Insert Customers
-- ----------------------------------------------------------------------------

INSERT INTO CUSTOMERS (customer_id, email, phone, name, created_at)
SELECT
    UUID_STRING() AS customer_id,
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 30 THEN NULL 
         ELSE CONCAT('user', SEQ4(), '@example.com') END AS email,
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 25 THEN NULL 
         ELSE CONCAT('+1-555-', LPAD(MOD(SEQ4(), 10000)::VARCHAR, 4, '0')) END AS phone,
    CONCAT('Customer ', SEQ4()) AS name,
    DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_TIMESTAMP()) AS created_at
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- ----------------------------------------------------------------------------
-- 5. Insert Orders (with customer_ids from CUSTOMERS)
-- ----------------------------------------------------------------------------

INSERT INTO ORDERS (order_id, customer_id, order_date, total_amount, status)
WITH customer_ids AS (SELECT customer_id FROM CUSTOMERS)
SELECT
    UUID_STRING() AS order_id,
    (SELECT customer_id FROM customer_ids SAMPLE (1 ROWS)) AS customer_id,
    CASE MOD(SEQ4(), 5)
        WHEN 0 THEN TO_VARCHAR(DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()), 'YYYY-MM-DD')
        WHEN 1 THEN TO_VARCHAR(DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()), 'MM/DD/YYYY')
        WHEN 2 THEN TO_VARCHAR(DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()), 'MON DD, YYYY')
        WHEN 3 THEN TO_VARCHAR(DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()), 'DD-MON-YYYY')
        ELSE TO_VARCHAR(DATEADD('day', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()), 'YYYY-MM-DD')
    END AS order_date,
    CASE 
        WHEN UNIFORM(0, 100, RANDOM()) < 5 THEN 'N/A'
        WHEN UNIFORM(0, 100, RANDOM()) < 8 THEN 'TBD'
        WHEN UNIFORM(0, 100, RANDOM()) < 10 THEN 'PENDING'
        ELSE TO_VARCHAR(ROUND(UNIFORM(10, 500, RANDOM())::DECIMAL(10,2), 2))
    END AS total_amount,
    CASE MOD(SEQ4(), 4)
        WHEN 0 THEN 'COMPLETED'
        WHEN 1 THEN 'SHIPPED'
        WHEN 2 THEN 'PROCESSING'
        ELSE 'PENDING'
    END AS status
FROM TABLE(GENERATOR(ROWCOUNT => 4950));

-- Add 50 duplicate orders (exact duplicates)
INSERT INTO ORDERS
SELECT * FROM ORDERS SAMPLE (50 ROWS);

-- ----------------------------------------------------------------------------
-- 6. Insert Order Items
-- ----------------------------------------------------------------------------

INSERT INTO ORDER_ITEMS (item_id, order_id, product_id, quantity, unit_price)
WITH order_ids AS (SELECT order_id FROM ORDERS),
     product_ids AS (SELECT product_id FROM PRODUCTS)
SELECT
    UUID_STRING() AS item_id,
    (SELECT order_id FROM order_ids SAMPLE (1 ROWS)) AS order_id,
    (SELECT product_id FROM product_ids SAMPLE (1 ROWS)) AS product_id,
    CASE 
        WHEN UNIFORM(0, 100, RANDOM()) < 3 THEN -1
        WHEN UNIFORM(0, 100, RANDOM()) < 6 THEN 0
        ELSE UNIFORM(1, 10, RANDOM())
    END AS quantity,
    ROUND(UNIFORM(5, 200, RANDOM())::DECIMAL(10,2), 2) AS unit_price
FROM TABLE(GENERATOR(ROWCOUNT => 15000));

-- ----------------------------------------------------------------------------
-- 7. Insert Events (ALL stale - > 30 days old)
-- ----------------------------------------------------------------------------

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
    OBJECT_CONSTRUCT('action', 'demo', 'seq', SEQ4()) AS event_data,
    -- All events are 30-365 days old (stale)
    DATEADD('day', -UNIFORM(30, 365, RANDOM()), CURRENT_TIMESTAMP()) AS event_timestamp
FROM TABLE(GENERATOR(ROWCOUNT => 50000));

-- ----------------------------------------------------------------------------
-- 8. Verify Problem State
-- ----------------------------------------------------------------------------

SELECT '=== VERIFICATION ===' AS section;

-- Check null rates
SELECT 'CUSTOMERS.email null rate' AS metric, 
       ROUND(COUNT_IF(email IS NULL) * 100.0 / COUNT(*), 1) AS pct FROM CUSTOMERS;
SELECT 'CUSTOMERS.phone null rate' AS metric,
       ROUND(COUNT_IF(phone IS NULL) * 100.0 / COUNT(*), 1) AS pct FROM CUSTOMERS;

-- Check duplicate rate
SELECT 'ORDERS duplicate rate' AS metric,
       ROUND((1.0 - COUNT(DISTINCT order_id) * 1.0 / COUNT(*)) * 100, 1) AS pct FROM ORDERS;

-- Check type inconsistency
SELECT 'ORDERS.total_amount non-numeric rate' AS metric,
       ROUND(COUNT_IF(TRY_CAST(total_amount AS DECIMAL(10,2)) IS NULL) * 100.0 / COUNT(*), 1) AS pct 
FROM ORDERS;

-- Check negative/zero values
SELECT 'ORDER_ITEMS.quantity zero_negative rate' AS metric,
       ROUND(COUNT_IF(quantity <= 0) * 100.0 / COUNT(*), 1) AS pct FROM ORDER_ITEMS;
SELECT 'PRODUCTS.price zero_negative rate' AS metric,
       ROUND(COUNT_IF(price <= 0) * 100.0 / COUNT(*), 1) AS pct FROM PRODUCTS;

-- Check data freshness
SELECT 'EVENTS freshness (days since newest)' AS metric,
       DATEDIFF('day', MAX(event_timestamp), CURRENT_TIMESTAMP()) AS days_stale FROM EVENTS;

-- Check constraint coverage
SELECT 'Tables with PRIMARY KEY' AS metric, 
       COUNT_IF(constraint_type = 'PRIMARY KEY') AS cnt 
FROM information_schema.table_constraints 
WHERE table_schema = 'ECOMMERCE';

SELECT 'Tables with FOREIGN KEY' AS metric,
       COUNT_IF(constraint_type = 'FOREIGN KEY') AS cnt
FROM information_schema.table_constraints
WHERE table_schema = 'ECOMMERCE';

-- Check documentation coverage
SELECT 'Tables with comments' AS metric,
       COUNT_IF(comment IS NOT NULL AND comment != '') AS cnt,
       COUNT(*) AS total
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE' AND table_type = 'BASE TABLE';

SELECT 'Columns with comments' AS metric,
       COUNT_IF(comment IS NOT NULL AND comment != '') AS cnt,
       COUNT(*) AS total
FROM information_schema.columns
WHERE table_schema = 'ECOMMERCE';

-- Show tables
SHOW TABLES IN SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- 9. Summary
-- ----------------------------------------------------------------------------

SELECT '=== DEMO SETUP COMPLETE ===' AS status;
SELECT 'Database: AIRD_DEMO, Schema: ECOMMERCE' AS info;
SELECT 'Tables created: CUSTOMERS, ORDERS, ORDER_ITEMS, PRODUCTS, EVENTS' AS info;
SELECT 'Next step: Run aird assess -c "snowflake://..." to see initial scores' AS next_step;
