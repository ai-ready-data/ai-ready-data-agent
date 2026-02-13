-- ============================================================================
-- Fix Script: Clean Factor
-- ============================================================================
-- Remediates Clean factor issues identified by the assessment.
-- Run after initial assessment to fix data quality problems.
-- ============================================================================

USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Null Rate in CUSTOMERS
-- ----------------------------------------------------------------------------

-- Fill null emails with placeholder
UPDATE CUSTOMERS 
SET email = CONCAT('unknown_', customer_id, '@placeholder.com') 
WHERE email IS NULL;

-- Fill null phones with placeholder
UPDATE CUSTOMERS 
SET phone = '+1-000-000-0000' 
WHERE phone IS NULL;

-- Verify
SELECT 'CUSTOMERS.email null rate (after fix)' AS metric, 
       COUNT_IF(email IS NULL) * 100.0 / COUNT(*) AS pct FROM CUSTOMERS;
SELECT 'CUSTOMERS.phone null rate (after fix)' AS metric,
       COUNT_IF(phone IS NULL) * 100.0 / COUNT(*) AS pct FROM CUSTOMERS;

-- ----------------------------------------------------------------------------
-- Fix: Duplicate Rate in ORDERS
-- ----------------------------------------------------------------------------

-- Deduplicate orders (keep first by order_id)
CREATE OR REPLACE TABLE ORDERS AS
SELECT * FROM ORDERS
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1;

-- Verify
SELECT 'ORDERS duplicate rate (after fix)' AS metric,
       ROUND((1.0 - COUNT(DISTINCT order_id) * 1.0 / COUNT(*)) * 100, 1) AS pct FROM ORDERS;

-- ----------------------------------------------------------------------------
-- Fix: Format Inconsistency in ORDERS.order_date
-- ----------------------------------------------------------------------------

-- Add normalized date column
ALTER TABLE ORDERS ADD COLUMN IF NOT EXISTS order_date_normalized DATE;

-- Parse various formats into normalized date
UPDATE ORDERS SET order_date_normalized = TRY_TO_DATE(order_date);

-- For rows that didn't parse, try alternate formats
UPDATE ORDERS 
SET order_date_normalized = TRY_TO_DATE(order_date, 'MM/DD/YYYY')
WHERE order_date_normalized IS NULL;

UPDATE ORDERS 
SET order_date_normalized = TRY_TO_DATE(order_date, 'MON DD, YYYY')
WHERE order_date_normalized IS NULL;

UPDATE ORDERS 
SET order_date_normalized = TRY_TO_DATE(order_date, 'DD-MON-YYYY')
WHERE order_date_normalized IS NULL;

-- Verify
SELECT 'ORDERS format fix success rate' AS metric,
       ROUND(COUNT_IF(order_date_normalized IS NOT NULL) * 100.0 / COUNT(*), 1) AS pct FROM ORDERS;

-- ----------------------------------------------------------------------------
-- Fix: Type Inconsistency in ORDERS.total_amount
-- ----------------------------------------------------------------------------

-- Add properly typed column
ALTER TABLE ORDERS ADD COLUMN IF NOT EXISTS total_amount_clean DECIMAL(10,2);

-- Convert valid values
UPDATE ORDERS 
SET total_amount_clean = TRY_CAST(total_amount AS DECIMAL(10,2));

-- For non-numeric values (N/A, TBD, PENDING), set to NULL or default
-- NULL is appropriate here as these orders have unknown amounts
-- Verify
SELECT 'ORDERS.total_amount type fix success rate' AS metric,
       ROUND(COUNT_IF(total_amount_clean IS NOT NULL) * 100.0 / COUNT(*), 1) AS pct FROM ORDERS;

-- ----------------------------------------------------------------------------
-- Fix: Zero/Negative Rate in ORDER_ITEMS.quantity
-- ----------------------------------------------------------------------------

-- Option 1: Set invalid quantities to NULL
UPDATE ORDER_ITEMS 
SET quantity = NULL 
WHERE quantity <= 0;

-- Option 2: Or set to minimum valid value (1)
-- UPDATE ORDER_ITEMS SET quantity = 1 WHERE quantity <= 0;

-- Verify
SELECT 'ORDER_ITEMS.quantity zero_negative rate (after fix)' AS metric,
       ROUND(COUNT_IF(quantity <= 0 OR quantity IS NULL) * 100.0 / COUNT(*), 1) AS pct FROM ORDER_ITEMS;

-- ----------------------------------------------------------------------------
-- Fix: Zero/Negative Rate in PRODUCTS.price
-- ----------------------------------------------------------------------------

-- Set invalid prices to NULL (to be reviewed by business)
UPDATE PRODUCTS 
SET price = NULL 
WHERE price <= 0;

-- Verify
SELECT 'PRODUCTS.price zero_negative rate (after fix)' AS metric,
       ROUND(COUNT_IF(price <= 0 OR price IS NULL) * 100.0 / COUNT(*), 1) AS pct FROM PRODUCTS;

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== CLEAN FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Re-run assessment to see improved Clean factor scores.' AS next_step;
