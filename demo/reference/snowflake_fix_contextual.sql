-- ============================================================================
-- Fix Script: Contextual Factor
-- ============================================================================
-- Remediates Contextual factor issues identified by the assessment.
-- Adds primary keys, foreign keys, and temporal columns.
-- ============================================================================

USE DATABASE AIRD_DEMO;
USE SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- Fix: Primary Keys
-- ----------------------------------------------------------------------------
-- Note: Snowflake PKs are informational (not enforced) but valuable for 
-- documentation and semantic understanding.

-- First, ensure no duplicates exist (handled in clean fix)

-- Add primary keys to all tables
ALTER TABLE CUSTOMERS ADD PRIMARY KEY (customer_id);
ALTER TABLE ORDERS ADD PRIMARY KEY (order_id);
ALTER TABLE ORDER_ITEMS ADD PRIMARY KEY (item_id);
ALTER TABLE PRODUCTS ADD PRIMARY KEY (product_id);
ALTER TABLE EVENTS ADD PRIMARY KEY (event_id);

-- Verify
SELECT 'Tables with PRIMARY KEY' AS metric, 
       COUNT_IF(constraint_type = 'PRIMARY KEY') AS cnt 
FROM information_schema.table_constraints 
WHERE table_schema = 'ECOMMERCE';

-- ----------------------------------------------------------------------------
-- Fix: Foreign Keys
-- ----------------------------------------------------------------------------
-- Note: Snowflake FKs are informational (not enforced) but valuable for
-- lineage documentation and semantic understanding.

-- ORDERS -> CUSTOMERS
ALTER TABLE ORDERS 
ADD FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id);

-- ORDER_ITEMS -> ORDERS
ALTER TABLE ORDER_ITEMS 
ADD FOREIGN KEY (order_id) REFERENCES ORDERS(order_id);

-- ORDER_ITEMS -> PRODUCTS
ALTER TABLE ORDER_ITEMS 
ADD FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id);

-- EVENTS -> CUSTOMERS
ALTER TABLE EVENTS 
ADD FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id);

-- Verify
SELECT 'Tables with FOREIGN KEY' AS metric,
       COUNT_IF(constraint_type = 'FOREIGN KEY') AS cnt
FROM information_schema.table_constraints
WHERE table_schema = 'ECOMMERCE';

-- ----------------------------------------------------------------------------
-- Fix: Temporal Columns (updated_at)
-- ----------------------------------------------------------------------------

-- Add updated_at to tables missing it
ALTER TABLE CUSTOMERS ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE ORDERS ADD COLUMN IF NOT EXISTS created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE ORDERS ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE ORDER_ITEMS ADD COLUMN IF NOT EXISTS created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE ORDER_ITEMS ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE PRODUCTS ADD COLUMN IF NOT EXISTS created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE PRODUCTS ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();

-- Backfill existing rows
UPDATE CUSTOMERS SET updated_at = CURRENT_TIMESTAMP() WHERE updated_at IS NULL;
UPDATE ORDERS SET created_at = CURRENT_TIMESTAMP(), updated_at = CURRENT_TIMESTAMP() WHERE created_at IS NULL;
UPDATE ORDER_ITEMS SET created_at = CURRENT_TIMESTAMP(), updated_at = CURRENT_TIMESTAMP() WHERE created_at IS NULL;
UPDATE PRODUCTS SET created_at = CURRENT_TIMESTAMP(), updated_at = CURRENT_TIMESTAMP() WHERE created_at IS NULL;

-- Verify temporal columns
SELECT 'Temporal columns coverage' AS metric,
       table_name,
       COUNT_IF(column_name IN ('created_at', 'updated_at')) AS temporal_cols
FROM information_schema.columns
WHERE table_schema = 'ECOMMERCE'
GROUP BY table_name;

-- ----------------------------------------------------------------------------
-- Fix: Table and Column Documentation
-- ----------------------------------------------------------------------------
-- Comments make meaning explicit - a core Contextual requirement.

-- Table comments
COMMENT ON TABLE CUSTOMERS IS 
'Master customer table containing profile and contact information for all registered customers. Primary source for customer identity.';

COMMENT ON TABLE ORDERS IS 
'Order headers table with customer reference, order date, total amount, and status. Links to ORDER_ITEMS for line details.';

COMMENT ON TABLE ORDER_ITEMS IS 
'Order line items containing individual products within each order. Each row is a product-quantity-price combination.';

COMMENT ON TABLE PRODUCTS IS 
'Product catalog with pricing, categorization, and descriptions. Source of truth for product master data.';

COMMENT ON TABLE EVENTS IS 
'User activity event stream capturing page views, cart actions, purchases, and authentication events.';

-- Key column comments (abbreviated for demo)
COMMENT ON COLUMN CUSTOMERS.customer_id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN CUSTOMERS.email IS 'Primary email for communications';
COMMENT ON COLUMN CUSTOMERS.phone IS 'Phone number in E.164 format';
COMMENT ON COLUMN ORDERS.order_id IS 'Unique order identifier (UUID)';
COMMENT ON COLUMN ORDERS.customer_id IS 'Reference to CUSTOMERS.customer_id';
COMMENT ON COLUMN ORDERS.total_amount IS 'Order total in USD';
COMMENT ON COLUMN PRODUCTS.product_id IS 'Unique product identifier (UUID)';
COMMENT ON COLUMN PRODUCTS.price IS 'Current retail price in USD';
COMMENT ON COLUMN EVENTS.event_type IS 'Event category: page_view, add_to_cart, purchase, search, login, logout';

-- ----------------------------------------------------------------------------
-- Summary
-- ----------------------------------------------------------------------------

SELECT '=== CONTEXTUAL FACTOR FIXES COMPLETE ===' AS status;
SELECT 'Primary keys, foreign keys, temporal columns, and documentation added.' AS info;
SELECT 'Re-run assessment to see improved Contextual factor scores.' AS next_step;
