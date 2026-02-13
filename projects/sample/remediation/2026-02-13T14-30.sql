-- AI-Ready Data Assessment — Remediation Suggestions
-- Project: sample
-- Database: ANALYTICS_PROD.ANALYTICS
-- Date: 2026-02-13T14:30 UTC
--
-- Generated from assessment failures. Review before executing.
-- DO NOT run without understanding each change.

-- ============================================================
-- 1. Contextual: Add missing primary keys (pk_coverage 0.80 → 1.00)
-- ============================================================

ALTER TABLE ANALYTICS_PROD.ANALYTICS.ORDERS
  ADD CONSTRAINT orders_pk PRIMARY KEY (order_id);

ALTER TABLE ANALYTICS_PROD.ANALYTICS.EVENTS
  ADD CONSTRAINT events_pk PRIMARY KEY (event_id);

-- ============================================================
-- 2. Contextual: Add column comments (comment_coverage 0.45 → 0.70+)
-- ============================================================

-- Priority columns (critical tables first)
COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.CUSTOMERS.customer_id IS 'Unique customer identifier (UUID)';
COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.CUSTOMERS.email IS 'Primary email address. May be masked by compliance policy.';
COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.CUSTOMERS.created_at IS 'Timestamp when the customer record was created (UTC).';

COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.ORDERS.order_id IS 'Unique order identifier (UUID)';
COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.ORDERS.customer_id IS 'FK to CUSTOMERS.customer_id';
COMMENT ON COLUMN ANALYTICS_PROD.ANALYTICS.ORDERS.total_amount IS 'Order total in USD after discounts';

-- Alternatively, use Cortex AI to generate descriptions:
-- SELECT SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC('ANALYTICS_PROD', 'ANALYTICS', 'CUSTOMERS');

-- ============================================================
-- 3. Contextual: Add table comments (table_comment_coverage 0.60 → 1.00)
-- ============================================================

COMMENT ON TABLE ANALYTICS_PROD.ANALYTICS.EVENTS IS 'Raw user interaction events from web and mobile clients.';
COMMENT ON TABLE ANALYTICS_PROD.ANALYTICS.SESSIONS IS 'Aggregated session data derived from events.';
COMMENT ON TABLE ANALYTICS_PROD.ANALYTICS.PRODUCTS IS 'Product catalog with pricing and category metadata.';
COMMENT ON TABLE ANALYTICS_PROD.ANALYTICS.INTERACTIONS IS 'Customer touchpoints across channels (email, chat, phone).';

-- ============================================================
-- 4. Current: Enable change tracking (change_tracking_coverage 0.60 → 1.00)
-- ============================================================

ALTER TABLE ANALYTICS_PROD.ANALYTICS.EVENTS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ANALYTICS_PROD.ANALYTICS.SESSIONS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ANALYTICS_PROD.ANALYTICS.PRODUCTS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ANALYTICS_PROD.ANALYTICS.INTERACTIONS SET CHANGE_TRACKING = TRUE;

-- ============================================================
-- 5. Current: Create streams (stream_coverage 0.40 → 0.70+)
-- ============================================================

-- Streams for tables that feed downstream pipelines
CREATE STREAM IF NOT EXISTS ANALYTICS_PROD.ANALYTICS.EVENTS_STREAM
  ON TABLE ANALYTICS_PROD.ANALYTICS.EVENTS;

CREATE STREAM IF NOT EXISTS ANALYTICS_PROD.ANALYTICS.ORDERS_STREAM
  ON TABLE ANALYTICS_PROD.ANALYTICS.ORDERS;

CREATE STREAM IF NOT EXISTS ANALYTICS_PROD.ANALYTICS.CUSTOMERS_STREAM
  ON TABLE ANALYTICS_PROD.ANALYTICS.CUSTOMERS;

-- ============================================================
-- After applying fixes, re-run the assessment to measure improvement.
-- ============================================================
