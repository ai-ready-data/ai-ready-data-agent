# Plan: Snowflake Demo — All 6 Factors End-to-End

**Created:** 2026-02-12  
**Status:** Planning  
**Goal:** Create a compelling demo that showcases AI-ready data assessment across all 6 factors in Snowflake, with fixable problems and measurable improvement.

---

## Table of Contents

1. [Overview](#1-overview)
   - 1.1 Demo Narrative
   - 1.2 Success Criteria
   - 1.3 The 6 Factors
   - **1.4 Canonical Source: `factors.md`** ← Start here for factor definitions
2. [Prerequisites](#2-prerequisites)
3. [Demo Schema Design](#3-demo-schema-design)
4. [Factor-by-Factor Test Implementation](#4-factor-by-factor-test-implementation)
5. [Demo Setup SQL Script](#5-demo-setup-sql-script)
6. [Requirements Registry Updates](#6-requirements-registry-updates)
7. [Remediation Templates](#7-remediation-templates)
8. [Demo Runbook](#8-demo-runbook)
9. [Implementation Checklist](#9-implementation-checklist)
10. [File Manifest](#10-file-manifest)

---

## 1. Overview

### 1.1 Demo Narrative

A data engineer has a Snowflake database powering an e-commerce platform. They want to use this data for AI workloads (RAG for customer support, ML for recommendations). The AI-Ready Data Agent assesses their data, identifies problems across all 6 factors, and an AI assistant (Coco) fixes each issue. Re-assessment shows dramatic improvement.

### 1.2 Success Criteria

- [ ] Initial assessment shows failures across all 6 factors
- [ ] Each factor has at least 2-3 testable requirements
- [ ] Coco can generate SQL fixes for each failure
- [ ] Re-assessment shows measurable improvement (before/after comparison)
- [ ] Demo completes in under 15 minutes

### 1.3 The 6 Factors

| Factor | Name | Definition | Status |
|--------|------|------------|--------|
| 0 | **Clean** | Accurate, complete, valid, error-free | ✅ Implemented |
| 1 | **Contextual** | Meaning explicit and colocated | ✅ Implemented |
| 2 | **Consumable** | Accessible, performant, documented | 🔴 Not implemented |
| 3 | **Current** | Fresh, tracked, not stale | 🔴 Not implemented |
| 4 | **Correlated** | Lineage visible, provenance tracked | 🔴 Not implemented |
| 5 | **Compliant** | Governed, secure, policy-enforced | 🔴 Not implemented |

### 1.4 Canonical Source: `factors.md`

**IMPORTANT:** The canonical reference for all factor definitions, requirements, and Snowflake capabilities is:

```
/factors.md  (root directory)
```

This file contains:
**When implementing new tests:**

1. **Reference `factors.md` first** for the authoritative requirement definitions
2. **Use the exact terminology** from the requirements table (e.g., "Declared freshness contracts" not "freshness SLA")
3. **Map to Snowflake capabilities** listed in the Platform Capabilities tables
4. **Note the maturity level** (Foundation, Intermediate, Advanced) to prioritize implementation

**Example mapping from `factors.md` to test implementation:**

```
factors.md requirement:
  "Declared freshness contracts — Data carries its freshness requirements as metadata"
  Maturity: Foundation
  Snowflake: Data Quality Monitoring (preview), Tags

→ Test implementation:
  requirement_key: freshness_contract_defined
  query: Check for freshness tags or DMF rules on tables
  threshold: L1=0.3, L2=0.6, L3=0.9 (Foundation = high coverage expected)
```

---

## 2. Prerequisites

### 2.1 Snowflake Account Requirements

- Snowflake account with ACCOUNTADMIN or equivalent privileges
- Access to `SNOWFLAKE.ACCOUNT_USAGE` schema (for lineage/audit queries)
- Ability to create: databases, schemas, tables, views, streams, tasks, masking policies, row access policies, tags

### 2.2 Agent Environment

```bash
# Install with Snowflake support
pip install -e ".[snowflake]"

# Verify Snowflake connection
aird discover -c "snowflake://user:pass@account/database/schema"
```

### 2.3 Connection String Format

```
snowflake://<user>:<password>@<account>/<database>/<schema>?warehouse=<warehouse>&role=<role>
```

Or use Snowflake connection config:
```
snowflake://connection:my_connection_name
```

---

## 3. Demo Schema Design

### 3.1 Database and Schema

```
Database: AIRD_DEMO
Schema:   ECOMMERCE
```

### 3.2 Table Definitions

Create 5 tables representing a realistic e-commerce data model:

#### 3.2.1 CUSTOMERS

| Column | Type | Problems to Create |
|--------|------|-------------------|
| customer_id | VARCHAR(36) | No PRIMARY KEY |
| email | VARCHAR(255) | 30% NULL, no masking policy |
| phone | VARCHAR(20) | 25% NULL, no masking policy |
| name | VARCHAR(100) | — |
| created_at | TIMESTAMP | — |
| updated_at | — | **Missing column** |

#### 3.2.2 ORDERS

| Column | Type | Problems to Create |
|--------|------|-------------------|
| order_id | VARCHAR(36) | No PRIMARY KEY |
| customer_id | VARCHAR(36) | No FOREIGN KEY |
| order_date | VARCHAR(20) | **Mixed formats**: '2024-01-15', '01/15/2024', 'Jan 15, 2024' |
| total_amount | VARCHAR(20) | **Mixed types**: numbers + 'N/A', 'TBD', 'PENDING' |
| status | VARCHAR(20) | — |

#### 3.2.3 ORDER_ITEMS

| Column | Type | Problems to Create |
|--------|------|-------------------|
| item_id | VARCHAR(36) | No PRIMARY KEY |
| order_id | VARCHAR(36) | No FOREIGN KEY |
| product_id | VARCHAR(36) | No FOREIGN KEY |
| quantity | INTEGER | **Negative/zero values**: -1, 0 |
| unit_price | DECIMAL(10,2) | — |

#### 3.2.4 PRODUCTS

| Column | Type | Problems to Create |
|--------|------|-------------------|
| product_id | VARCHAR(36) | No PRIMARY KEY |
| name | VARCHAR(200) | — |
| category | VARCHAR(100) | — |
| price | DECIMAL(10,2) | **Zero/negative**: $0, -$5 |
| description | TEXT | No COMMENT |

#### 3.2.5 EVENTS

| Column | Type | Problems to Create |
|--------|------|-------------------|
| event_id | VARCHAR(36) | No PRIMARY KEY |
| customer_id | VARCHAR(36) | No FOREIGN KEY |
| event_type | VARCHAR(50) | — |
| event_data | VARIANT | — |
| event_timestamp | TIMESTAMP | **Stale**: all records > 30 days old |

### 3.3 Intentional Problems Summary

| Factor | Problem | Tables Affected |
|--------|---------|-----------------|
| Clean | High null rate | CUSTOMERS (email, phone) |
| Clean | Duplicate rows | ORDERS (insert duplicates) |
| Clean | Format inconsistency | ORDERS (order_date) |
| Clean | Type inconsistency | ORDERS (total_amount) |
| Clean | Zero/negative values | ORDER_ITEMS (quantity), PRODUCTS (price) |
| Contextual | No primary keys | All 5 tables |
| Contextual | No foreign keys | ORDERS, ORDER_ITEMS, EVENTS |
| Contextual | No semantic model | No semantic views |
| Contextual | Missing temporal cols | ORDERS, ORDER_ITEMS, PRODUCTS (no updated_at) |
| Consumable | No clustering | EVENTS (large table) |
| Consumable | No search optimization | PRODUCTS (text search) |
| Consumable | No column comments | All columns |
| Consumable | No table comments | All tables |
| Current | Stale data | EVENTS (>30 days old) |
| Current | No streams | No CDC tracking |
| Current | No change tracking | All tables |
| Correlated | No object tags | All tables |
| Correlated | No documented lineage | No tag-based provenance |
| Compliant | PII exposed | CUSTOMERS (email, phone) |
| Compliant | No row access policy | All tables |
| Compliant | No sensitivity tags | PII columns untagged |

---

## 4. Factor-by-Factor Test Implementation

> **📖 Reference:** Before implementing any factor, consult **`/factors.md`** in the root directory.
> This is the canonical source for:
> - Factor definitions and reasoning
> - Detailed requirements with maturity levels
> - Snowflake platform capabilities to leverage
> - Topic areas and use cases
>
> The test implementations below are derived from `factors.md`. When in doubt, defer to that document.

### 4.1 Factor 0: Clean (Existing)

**File:** `agent/suites/definitions/clean_snowflake.yaml`  
**Status:** ✅ Already implemented

Existing tests:
- `null_rate` — fraction of nulls per column
- `duplicate_rate` — fraction of duplicate rows per table
- `format_inconsistency_rate` — date parsing failures
- `type_inconsistency_rate` — type casting failures
- `zero_negative_rate` — invalid numeric values

**No changes needed.**

---

### 4.2 Factor 1: Contextual (Existing)

**File:** `agent/suites/definitions/contextual_snowflake.yaml`  
**Status:** ✅ Already implemented

Existing tests:
- `primary_key_defined` — PK constraint coverage
- `foreign_key_coverage` — FK constraint coverage
- `semantic_model_coverage` — semantic view coverage
- `temporal_scope_present` — temporal column presence

**No changes needed.**

---

### 4.3 Factor 2: Consumable (NEW)

**File to create:** `agent/suites/definitions/consumable_snowflake.yaml`

#### 4.3.1 Requirements

| Requirement | Key | Description | Direction | L1 | L2 | L3 |
|-------------|-----|-------------|-----------|----|----|-----|
| Column Documentation | `column_comment_coverage` | Fraction of columns with comments | gte | 0.3 | 0.6 | 0.9 |
| Table Documentation | `table_comment_coverage` | Fraction of tables with comments | gte | 0.5 | 0.8 | 0.95 |
| Clustering Defined | `clustering_coverage` | Fraction of large tables with clustering keys | gte | 0.2 | 0.5 | 0.8 |
| Search Optimization | `search_optimization_coverage` | Fraction of text-heavy tables with search optimization | gte | 0.1 | 0.3 | 0.5 |

#### 4.3.2 Test Definitions

```yaml
# consumable_snowflake.yaml
suite_name: consumable_snowflake
platform: snowflake

tests:
  - id: column_comment_coverage
    factor: consumable
    requirement: column_comment_coverage
    query: >-
      SELECT COUNT_IF(comment IS NOT NULL AND comment != '') * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.columns
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
    target_type: platform

  - id: table_comment_coverage
    factor: consumable
    requirement: table_comment_coverage
    query: >-
      SELECT COUNT_IF(comment IS NOT NULL AND comment != '') * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
        AND table_type = 'BASE TABLE'
    target_type: platform

  - id: clustering_coverage
    factor: consumable
    requirement: clustering_coverage
    query: >-
      SELECT COUNT_IF(clustering_key IS NOT NULL AND clustering_key != '') * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
        AND table_type = 'BASE TABLE'
        AND row_count > 10000
    target_type: platform

  - id: search_optimization_coverage
    factor: consumable
    requirement: search_optimization_coverage
    query: >-
      SELECT COUNT_IF(search_optimization = 'ON') * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
        AND table_type = 'BASE TABLE'
    target_type: platform
```

#### 4.3.3 Notes

- `clustering_key` is available in `information_schema.tables`
- `search_optimization` column exists in `information_schema.tables`
- Thresholds are intentionally lower than other factors (documentation is often lacking)

---

### 4.4 Factor 3: Current (NEW)

**File to create:** `agent/suites/definitions/current_snowflake.yaml`

#### 4.4.1 Requirements

| Requirement | Key | Description | Direction | L1 | L2 | L3 |
|-------------|-----|-------------|-----------|----|----|-----|
| Change Tracking | `change_tracking_coverage` | Fraction of tables with change tracking enabled | gte | 0.2 | 0.5 | 0.8 |
| Stream Coverage | `stream_coverage` | Fraction of tables with associated streams | gte | 0.1 | 0.3 | 0.6 |
| Data Freshness | `data_freshness_pass_rate` | Fraction of tables updated within SLA (7 days default) | gte | 0.5 | 0.8 | 0.95 |
| Dynamic Table Usage | `dynamic_table_coverage` | Fraction of derived tables that are dynamic tables | gte | 0.0 | 0.2 | 0.5 |

#### 4.4.2 Test Definitions

```yaml
# current_snowflake.yaml
suite_name: current_snowflake
platform: snowflake

tests:
  - id: change_tracking_coverage
    factor: current
    requirement: change_tracking_coverage
    query: >-
      SELECT COUNT_IF(change_tracking = 'ON') * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
        AND table_type = 'BASE TABLE'
    target_type: platform

  - id: stream_coverage
    factor: current
    requirement: stream_coverage
    query: >-
      WITH base_tables AS (
        SELECT table_name
        FROM information_schema.tables
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
          AND table_type = 'BASE TABLE'
      ),
      tables_with_streams AS (
        SELECT DISTINCT base_tables
        FROM information_schema.streams
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
      )
      SELECT COUNT(s.base_tables) * 1.0 / NULLIF(COUNT(t.table_name), 0) AS v
      FROM base_tables t
      LEFT JOIN tables_with_streams s ON t.table_name = s.base_tables
    target_type: platform

  - id: data_freshness_pass_rate
    factor: current
    requirement: data_freshness_pass_rate
    query: >-
      SELECT COUNT_IF(last_altered > DATEADD('day', -7, CURRENT_TIMESTAMP())) * 1.0 / NULLIF(COUNT(*), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
        AND table_type = 'BASE TABLE'
    target_type: platform

  - id: dynamic_table_coverage
    factor: current
    requirement: dynamic_table_coverage
    query: >-
      SELECT COUNT_IF(table_type = 'DYNAMIC TABLE') * 1.0 / 
             NULLIF(COUNT_IF(table_type IN ('VIEW', 'DYNAMIC TABLE')), 0) AS v
      FROM information_schema.tables
      WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
    target_type: platform
```

#### 4.4.3 Notes

- `change_tracking` column is in `information_schema.tables`
- `information_schema.streams` contains stream metadata
- `last_altered` is the last DDL modification time (not data modification)
- For actual data freshness, would need to query max(timestamp_col) per table — more complex
- Dynamic tables are identified by `table_type = 'DYNAMIC TABLE'`

---

### 4.5 Factor 4: Correlated (NEW)

**File to create:** `agent/suites/definitions/correlated_snowflake.yaml`

#### 4.5.1 Requirements

| Requirement | Key | Description | Direction | L1 | L2 | L3 |
|-------------|-----|-------------|-----------|----|----|-----|
| Object Tag Coverage | `object_tag_coverage` | Fraction of tables with at least one tag | gte | 0.2 | 0.5 | 0.8 |
| Column Tag Coverage | `column_tag_coverage` | Fraction of columns with at least one tag | gte | 0.1 | 0.3 | 0.6 |
| Lineage Queryable | `lineage_queryable` | Whether lineage data is available in ACCESS_HISTORY | gte | 0.5 | 0.8 | 1.0 |

#### 4.5.2 Test Definitions

```yaml
# correlated_snowflake.yaml
suite_name: correlated_snowflake
platform: snowflake

tests:
  - id: object_tag_coverage
    factor: correlated
    requirement: object_tag_coverage
    query: >-
      WITH base_tables AS (
        SELECT table_catalog, table_schema, table_name
        FROM information_schema.tables
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
          AND table_type = 'BASE TABLE'
      ),
      tagged_tables AS (
        SELECT DISTINCT object_database, object_schema, object_name
        FROM snowflake.account_usage.tag_references
        WHERE domain = 'TABLE'
          AND deleted IS NULL
      )
      SELECT COUNT(tt.object_name) * 1.0 / NULLIF(COUNT(bt.table_name), 0) AS v
      FROM base_tables bt
      LEFT JOIN tagged_tables tt
        ON bt.table_catalog = tt.object_database
        AND bt.table_schema = tt.object_schema
        AND bt.table_name = tt.object_name
    target_type: platform

  - id: column_tag_coverage
    factor: correlated
    requirement: column_tag_coverage
    query: >-
      WITH all_columns AS (
        SELECT table_catalog, table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
      ),
      tagged_columns AS (
        SELECT DISTINCT object_database, object_schema, object_name, column_name
        FROM snowflake.account_usage.tag_references
        WHERE domain = 'COLUMN'
          AND deleted IS NULL
      )
      SELECT COUNT(tc.column_name) * 1.0 / NULLIF(COUNT(ac.column_name), 0) AS v
      FROM all_columns ac
      LEFT JOIN tagged_columns tc
        ON ac.table_catalog = tc.object_database
        AND ac.table_schema = tc.object_schema
        AND ac.table_name = tc.object_name
        AND ac.column_name = tc.column_name
    target_type: platform

  - id: lineage_queryable
    factor: correlated
    requirement: lineage_queryable
    query: >-
      SELECT CASE 
        WHEN (SELECT COUNT(*) FROM snowflake.account_usage.access_history 
              WHERE query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP()) LIMIT 1) > 0 
        THEN 1.0 
        ELSE 0.0 
      END AS v
    target_type: platform
```

#### 4.5.3 Notes

- `snowflake.account_usage.tag_references` requires ACCOUNTADMIN or GOVERNANCE_VIEWER role
- `snowflake.account_usage.access_history` contains query-level lineage
- Tag queries may have latency (account_usage views are not real-time)
- Alternative: use `SHOW TAGS IN ACCOUNT` if account_usage is not accessible

---

### 4.6 Factor 5: Compliant (NEW)

**File to create:** `agent/suites/definitions/compliant_snowflake.yaml`

#### 4.6.1 Requirements

| Requirement | Key | Description | Direction | L1 | L2 | L3 |
|-------------|-----|-------------|-----------|----|----|-----|
| Masking Policy Coverage | `masking_policy_coverage` | Fraction of PII columns with masking policies | gte | 0.3 | 0.7 | 0.95 |
| Row Access Policy Coverage | `row_access_policy_coverage` | Fraction of tables with row access policies | gte | 0.1 | 0.3 | 0.6 |
| Sensitive Column Tagged | `sensitive_column_tagged` | Fraction of likely-sensitive columns with sensitivity tags | gte | 0.2 | 0.5 | 0.9 |
| Network Policy Exists | `network_policy_exists` | Whether a network policy is configured | gte | 0.5 | 1.0 | 1.0 |

#### 4.6.2 Test Definitions

```yaml
# compliant_snowflake.yaml
suite_name: compliant_snowflake
platform: snowflake

tests:
  - id: masking_policy_coverage
    factor: compliant
    requirement: masking_policy_coverage
    query: >-
      WITH pii_columns AS (
        SELECT table_catalog, table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
          AND (
            LOWER(column_name) LIKE '%email%'
            OR LOWER(column_name) LIKE '%phone%'
            OR LOWER(column_name) LIKE '%ssn%'
            OR LOWER(column_name) LIKE '%social_security%'
            OR LOWER(column_name) LIKE '%credit_card%'
            OR LOWER(column_name) LIKE '%card_number%'
            OR LOWER(column_name) LIKE '%password%'
            OR LOWER(column_name) LIKE '%secret%'
          )
      ),
      masked_columns AS (
        SELECT DISTINCT ref_database_name, ref_schema_name, ref_entity_name, ref_column_name
        FROM information_schema.policy_references
        WHERE policy_kind = 'MASKING_POLICY'
      )
      SELECT COUNT(mc.ref_column_name) * 1.0 / NULLIF(COUNT(pc.column_name), 0) AS v
      FROM pii_columns pc
      LEFT JOIN masked_columns mc
        ON pc.table_catalog = mc.ref_database_name
        AND pc.table_schema = mc.ref_schema_name
        AND pc.table_name = mc.ref_entity_name
        AND pc.column_name = mc.ref_column_name
    target_type: platform

  - id: row_access_policy_coverage
    factor: compliant
    requirement: row_access_policy_coverage
    query: >-
      WITH base_tables AS (
        SELECT table_catalog, table_schema, table_name
        FROM information_schema.tables
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
          AND table_type = 'BASE TABLE'
      ),
      tables_with_rap AS (
        SELECT DISTINCT ref_database_name, ref_schema_name, ref_entity_name
        FROM information_schema.policy_references
        WHERE policy_kind = 'ROW_ACCESS_POLICY'
      )
      SELECT COUNT(rap.ref_entity_name) * 1.0 / NULLIF(COUNT(bt.table_name), 0) AS v
      FROM base_tables bt
      LEFT JOIN tables_with_rap rap
        ON bt.table_catalog = rap.ref_database_name
        AND bt.table_schema = rap.ref_schema_name
        AND bt.table_name = rap.ref_entity_name
    target_type: platform

  - id: sensitive_column_tagged
    factor: compliant
    requirement: sensitive_column_tagged
    query: >-
      WITH sensitive_columns AS (
        SELECT table_catalog, table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')
          AND (
            LOWER(column_name) LIKE '%email%'
            OR LOWER(column_name) LIKE '%phone%'
            OR LOWER(column_name) LIKE '%ssn%'
            OR LOWER(column_name) LIKE '%address%'
            OR LOWER(column_name) LIKE '%birth%'
            OR LOWER(column_name) LIKE '%salary%'
            OR LOWER(column_name) LIKE '%income%'
          )
      ),
      tagged_columns AS (
        SELECT DISTINCT object_database, object_schema, object_name, column_name
        FROM snowflake.account_usage.tag_references
        WHERE domain = 'COLUMN'
          AND LOWER(tag_name) IN ('pii', 'sensitive', 'confidential', 'phi', 'pci')
          AND deleted IS NULL
      )
      SELECT COUNT(tc.column_name) * 1.0 / NULLIF(COUNT(sc.column_name), 0) AS v
      FROM sensitive_columns sc
      LEFT JOIN tagged_columns tc
        ON sc.table_catalog = tc.object_database
        AND sc.table_schema = tc.object_schema
        AND sc.table_name = tc.object_name
        AND sc.column_name = tc.column_name
    target_type: platform

  - id: network_policy_exists
    factor: compliant
    requirement: network_policy_exists
    query: >-
      SELECT CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.network_policies LIMIT 1) > 0 
        THEN 1.0 
        ELSE 0.0 
      END AS v
    target_type: platform
```

#### 4.6.3 Notes

- `information_schema.policy_references` shows masking and row access policy assignments
- PII detection is heuristic (column name matching) — could be enhanced with classification
- `snowflake.account_usage.tag_references` for sensitivity tags
- Network policies are in `information_schema.network_policies` (may require ACCOUNTADMIN)

---

## 5. Demo Setup SQL Script

**File to create:** `scripts/demo/snowflake_setup.sql`

### 5.1 Full Setup Script

```sql
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
-- 3. Insert Problematic Data
-- ----------------------------------------------------------------------------

-- CUSTOMERS: 1000 rows, 30% null emails, 25% null phones
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

-- ORDERS: 5000 rows with mixed date formats and type inconsistency
-- Plus intentional duplicates (50 duplicate rows)
INSERT INTO ORDERS (order_id, customer_id, order_date, total_amount, status)
SELECT
    UUID_STRING() AS order_id,
    (SELECT customer_id FROM CUSTOMERS ORDER BY RANDOM() LIMIT 1) AS customer_id,
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
SELECT * FROM ORDERS ORDER BY RANDOM() LIMIT 50;

-- ORDER_ITEMS: 15000 rows with negative/zero quantities
INSERT INTO ORDER_ITEMS (item_id, order_id, product_id, quantity, unit_price)
SELECT
    UUID_STRING() AS item_id,
    (SELECT order_id FROM ORDERS ORDER BY RANDOM() LIMIT 1) AS order_id,
    (SELECT product_id FROM PRODUCTS ORDER BY RANDOM() LIMIT 1) AS product_id,
    CASE 
        WHEN UNIFORM(0, 100, RANDOM()) < 3 THEN -1
        WHEN UNIFORM(0, 100, RANDOM()) < 6 THEN 0
        ELSE UNIFORM(1, 10, RANDOM())
    END AS quantity,
    ROUND(UNIFORM(5, 200, RANDOM())::DECIMAL(10,2), 2) AS unit_price
FROM TABLE(GENERATOR(ROWCOUNT => 15000));

-- PRODUCTS: 500 rows with zero/negative prices
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

-- EVENTS: 50000 rows, ALL stale (> 30 days old)
INSERT INTO EVENTS (event_id, customer_id, event_type, event_data, event_timestamp)
SELECT
    UUID_STRING() AS event_id,
    (SELECT customer_id FROM CUSTOMERS ORDER BY RANDOM() LIMIT 1) AS customer_id,
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
-- 4. Verify Problem State
-- ----------------------------------------------------------------------------

-- Check null rates
SELECT 'CUSTOMERS.email null rate' AS metric, 
       COUNT_IF(email IS NULL) * 100.0 / COUNT(*) AS pct FROM CUSTOMERS;
SELECT 'CUSTOMERS.phone null rate' AS metric,
       COUNT_IF(phone IS NULL) * 100.0 / COUNT(*) AS pct FROM CUSTOMERS;

-- Check duplicate rate
SELECT 'ORDERS duplicate rate' AS metric,
       (1.0 - COUNT(DISTINCT *) / COUNT(*)) * 100 AS pct FROM ORDERS;

-- Check type inconsistency
SELECT 'ORDERS.total_amount non-numeric rate' AS metric,
       COUNT_IF(TRY_CAST(total_amount AS DECIMAL(10,2)) IS NULL) * 100.0 / COUNT(*) AS pct 
FROM ORDERS;

-- Check negative/zero values
SELECT 'ORDER_ITEMS.quantity zero_negative rate' AS metric,
       COUNT_IF(quantity <= 0) * 100.0 / COUNT(*) AS pct FROM ORDER_ITEMS;
SELECT 'PRODUCTS.price zero_negative rate' AS metric,
       COUNT_IF(price <= 0) * 100.0 / COUNT(*) AS pct FROM PRODUCTS;

-- Check data freshness
SELECT 'EVENTS freshness (days since newest)' AS metric,
       DATEDIFF('day', MAX(event_timestamp), CURRENT_TIMESTAMP()) AS days_stale FROM EVENTS;

-- Check constraint coverage
SELECT 'Tables with PRIMARY KEY' AS metric, 
       COUNT_IF(constraint_type = 'PRIMARY KEY') AS cnt 
FROM information_schema.table_constraints 
WHERE UPPER(constraint_schema) NOT IN ('INFORMATION_SCHEMA');

SELECT 'Tables with FOREIGN KEY' AS metric,
       COUNT_IF(constraint_type = 'FOREIGN KEY') AS cnt
FROM information_schema.table_constraints
WHERE UPPER(constraint_schema) NOT IN ('INFORMATION_SCHEMA');

-- Check documentation coverage
SELECT 'Tables with comments' AS metric,
       COUNT_IF(comment IS NOT NULL AND comment != '') AS cnt,
       COUNT(*) AS total
FROM information_schema.tables
WHERE table_schema = 'ECOMMERCE';

SELECT 'Columns with comments' AS metric,
       COUNT_IF(comment IS NOT NULL AND comment != '') AS cnt,
       COUNT(*) AS total
FROM information_schema.columns
WHERE table_schema = 'ECOMMERCE';

SHOW TABLES IN SCHEMA ECOMMERCE;

-- ----------------------------------------------------------------------------
-- 5. Summary
-- ----------------------------------------------------------------------------

SELECT '=== DEMO SETUP COMPLETE ===' AS status;
SELECT 'Database: AIRD_DEMO, Schema: ECOMMERCE' AS info;
SELECT 'Tables created: CUSTOMERS, ORDERS, ORDER_ITEMS, PRODUCTS, EVENTS' AS info;
SELECT 'Run: aird assess -c "snowflake://..." --schema ECOMMERCE' AS next_step;
```

### 5.2 Create Tags Script (for Correlated/Compliant tests)

```sql
-- ============================================================================
-- Create Tags for Governance Demo
-- ============================================================================
-- Run this BEFORE the demo if you want tag-based tests to have a baseline.
-- The tags exist but are NOT applied to any objects initially.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE AIRD_DEMO;

-- Create tag database/schema if not using AIRD_DEMO
CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.pii 
    ALLOWED_VALUES 'email', 'phone', 'ssn', 'address', 'name';

CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.sensitivity
    ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.data_domain
    ALLOWED_VALUES 'customer', 'order', 'product', 'event', 'financial';

CREATE TAG IF NOT EXISTS AIRD_DEMO.ECOMMERCE.owner
    COMMENT = 'Data owner team or individual';

-- Tags created but NOT applied — this is intentional for the demo
SELECT 'Tags created. Not applied to any objects (intentional for demo).' AS status;
```

---

## 6. Requirements Registry Updates

**File to update:** `agent/requirements_registry.yaml`

Add the following requirement definitions:

```yaml
# ── Factor 2: Consumable ──────────────────────────────────────────────────────
column_comment_coverage:
  name: Column Comment Coverage
  description: Fraction of columns with documentation comments. Higher is better.
  factor: consumable
  direction: gte
  default_thresholds: {l1: 0.3, l2: 0.6, l3: 0.9}

table_comment_coverage:
  name: Table Comment Coverage
  description: Fraction of tables with documentation comments. Higher is better.
  factor: consumable
  direction: gte
  default_thresholds: {l1: 0.5, l2: 0.8, l3: 0.95}

clustering_coverage:
  name: Clustering Coverage
  description: Fraction of large tables with clustering keys defined. Higher is better.
  factor: consumable
  direction: gte
  default_thresholds: {l1: 0.2, l2: 0.5, l3: 0.8}

search_optimization_coverage:
  name: Search Optimization Coverage
  description: Fraction of tables with search optimization enabled. Higher is better.
  factor: consumable
  direction: gte
  default_thresholds: {l1: 0.1, l2: 0.3, l3: 0.5}

# ── Factor 3: Current ─────────────────────────────────────────────────────────
change_tracking_coverage:
  name: Change Tracking Coverage
  description: Fraction of tables with change tracking enabled. Higher is better.
  factor: current
  direction: gte
  default_thresholds: {l1: 0.2, l2: 0.5, l3: 0.8}

stream_coverage:
  name: Stream Coverage
  description: Fraction of tables with associated streams for CDC. Higher is better.
  factor: current
  direction: gte
  default_thresholds: {l1: 0.1, l2: 0.3, l3: 0.6}

data_freshness_pass_rate:
  name: Data Freshness Pass Rate
  description: Fraction of tables updated within freshness SLA. Higher is better.
  factor: current
  direction: gte
  default_thresholds: {l1: 0.5, l2: 0.8, l3: 0.95}

dynamic_table_coverage:
  name: Dynamic Table Coverage
  description: Fraction of derived tables that are dynamic tables. Higher is better.
  factor: current
  direction: gte
  default_thresholds: {l1: 0.0, l2: 0.2, l3: 0.5}

# ── Factor 4: Correlated ──────────────────────────────────────────────────────
object_tag_coverage:
  name: Object Tag Coverage
  description: Fraction of tables with at least one tag applied. Higher is better.
  factor: correlated
  direction: gte
  default_thresholds: {l1: 0.2, l2: 0.5, l3: 0.8}

column_tag_coverage:
  name: Column Tag Coverage
  description: Fraction of columns with at least one tag applied. Higher is better.
  factor: correlated
  direction: gte
  default_thresholds: {l1: 0.1, l2: 0.3, l3: 0.6}

lineage_queryable:
  name: Lineage Queryable
  description: Whether lineage data is available via ACCESS_HISTORY. Higher is better.
  factor: correlated
  direction: gte
  default_thresholds: {l1: 0.5, l2: 0.8, l3: 1.0}

# ── Factor 5: Compliant ───────────────────────────────────────────────────────
masking_policy_coverage:
  name: Masking Policy Coverage
  description: Fraction of PII columns with masking policies applied. Higher is better.
  factor: compliant
  direction: gte
  default_thresholds: {l1: 0.3, l2: 0.7, l3: 0.95}

row_access_policy_coverage:
  name: Row Access Policy Coverage
  description: Fraction of tables with row access policies. Higher is better.
  factor: compliant
  direction: gte
  default_thresholds: {l1: 0.1, l2: 0.3, l3: 0.6}

sensitive_column_tagged:
  name: Sensitive Column Tagged
  description: Fraction of likely-sensitive columns with sensitivity tags. Higher is better.
  factor: compliant
  direction: gte
  default_thresholds: {l1: 0.2, l2: 0.5, l3: 0.9}

network_policy_exists:
  name: Network Policy Exists
  description: Whether a network policy is configured for the account. Higher is better.
  factor: compliant
  direction: gte
  default_thresholds: {l1: 0.5, l2: 1.0, l3: 1.0}
```

---

## 7. Remediation Templates

**Directory to create:** `docs/remediation/`

Create one file per factor with SQL templates for fixes.

### 7.1 Clean Remediation

**File:** `docs/remediation/clean.md`

```markdown
# Clean Factor Remediation

## null_rate

**Problem:** Column has null values above threshold.

**Fix Pattern:**
\`\`\`sql
-- Option 1: Fill with default value
UPDATE {schema}.{table} 
SET {column} = '{default_value}' 
WHERE {column} IS NULL;

-- Option 2: Add NOT NULL constraint after filling
ALTER TABLE {schema}.{table} 
ALTER COLUMN {column} SET NOT NULL;

-- Option 3: Add default for future inserts
ALTER TABLE {schema}.{table} 
ALTER COLUMN {column} SET DEFAULT '{default_value}';
\`\`\`

## duplicate_rate

**Problem:** Table has duplicate rows.

**Fix Pattern:**
\`\`\`sql
-- Deduplicate by keeping first occurrence
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT DISTINCT * FROM {schema}.{table};

-- Or with explicit dedup key
CREATE OR REPLACE TABLE {schema}.{table} AS
SELECT * FROM {schema}.{table}
QUALIFY ROW_NUMBER() OVER (PARTITION BY {key_columns} ORDER BY {order_column}) = 1;
\`\`\`

## format_inconsistency_rate

**Problem:** Date column has inconsistent formats.

**Fix Pattern:**
\`\`\`sql
-- Normalize to standard format
UPDATE {schema}.{table}
SET {column} = TRY_TO_DATE({column})::VARCHAR
WHERE TRY_TO_DATE({column}) IS NOT NULL;

-- Better: Convert to proper DATE type
ALTER TABLE {schema}.{table} ADD COLUMN {column}_normalized DATE;
UPDATE {schema}.{table} SET {column}_normalized = TRY_TO_DATE({column});
ALTER TABLE {schema}.{table} DROP COLUMN {column};
ALTER TABLE {schema}.{table} RENAME COLUMN {column}_normalized TO {column};
\`\`\`

## type_inconsistency_rate

**Problem:** Column has mixed types (e.g., numbers and text).

**Fix Pattern:**
\`\`\`sql
-- Clean invalid values
UPDATE {schema}.{table}
SET {column} = NULL
WHERE TRY_CAST({column} AS DECIMAL(10,2)) IS NULL;

-- Convert to proper type
ALTER TABLE {schema}.{table} ADD COLUMN {column}_clean DECIMAL(10,2);
UPDATE {schema}.{table} SET {column}_clean = TRY_CAST({column} AS DECIMAL(10,2));
ALTER TABLE {schema}.{table} DROP COLUMN {column};
ALTER TABLE {schema}.{table} RENAME COLUMN {column}_clean TO {column};
\`\`\`

## zero_negative_rate

**Problem:** Numeric column has invalid zero or negative values.

**Fix Pattern:**
\`\`\`sql
-- Option 1: Nullify invalid values
UPDATE {schema}.{table}
SET {column} = NULL
WHERE {column} <= 0;

-- Option 2: Add CHECK constraint to prevent future issues
ALTER TABLE {schema}.{table} 
ADD CONSTRAINT {column}_positive CHECK ({column} > 0);
\`\`\`
```

### 7.2 Contextual Remediation

**File:** `docs/remediation/contextual.md`

```markdown
# Contextual Factor Remediation

## primary_key_defined

**Problem:** Table lacks a primary key constraint.

**Fix Pattern:**
\`\`\`sql
-- Add primary key (column must have unique, non-null values)
ALTER TABLE {schema}.{table} 
ADD PRIMARY KEY ({column});

-- If data has duplicates, deduplicate first
-- See: clean.md > duplicate_rate
\`\`\`

## foreign_key_coverage

**Problem:** Table lacks foreign key relationships.

**Fix Pattern:**
\`\`\`sql
-- Add foreign key constraint
ALTER TABLE {schema}.{child_table}
ADD FOREIGN KEY ({column}) REFERENCES {schema}.{parent_table}({parent_column});

-- Note: Snowflake FKs are informational (not enforced) but valuable for documentation
\`\`\`

## semantic_model_coverage

**Problem:** Tables lack semantic model definitions.

**Fix Pattern:**
\`\`\`sql
-- Create semantic view with business definitions
CREATE OR REPLACE SEMANTIC VIEW {schema}.{table}_semantic AS
SELECT
    {column1} AS "Customer ID" COMMENT 'Unique identifier for customer',
    {column2} AS "Email Address" COMMENT 'Primary email for customer communications'
FROM {schema}.{table};

-- Or add to existing semantic layer (dbt, Looker, etc.)
\`\`\`

## temporal_scope_present

**Problem:** Table lacks temporal columns (created_at, updated_at).

**Fix Pattern:**
\`\`\`sql
-- Add temporal columns
ALTER TABLE {schema}.{table} ADD COLUMN created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();
ALTER TABLE {schema}.{table} ADD COLUMN updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP();

-- Backfill existing rows
UPDATE {schema}.{table} SET created_at = CURRENT_TIMESTAMP() WHERE created_at IS NULL;
UPDATE {schema}.{table} SET updated_at = CURRENT_TIMESTAMP() WHERE updated_at IS NULL;
\`\`\`
```

### 7.3 Consumable Remediation

**File:** `docs/remediation/consumable.md`

```markdown
# Consumable Factor Remediation

## column_comment_coverage

**Problem:** Columns lack documentation comments.

**Fix Pattern:**
\`\`\`sql
-- Add column comments
COMMENT ON COLUMN {schema}.{table}.{column} IS '{description}';

-- Batch example
COMMENT ON COLUMN ECOMMERCE.CUSTOMERS.customer_id IS 'Unique identifier for each customer (UUID)';
COMMENT ON COLUMN ECOMMERCE.CUSTOMERS.email IS 'Primary email address for customer communications';
COMMENT ON COLUMN ECOMMERCE.CUSTOMERS.phone IS 'Primary phone number in E.164 format';
\`\`\`

## table_comment_coverage

**Problem:** Tables lack documentation comments.

**Fix Pattern:**
\`\`\`sql
-- Add table comment
COMMENT ON TABLE {schema}.{table} IS '{description}';

-- Example
COMMENT ON TABLE ECOMMERCE.CUSTOMERS IS 'Master customer table containing profile and contact information for all registered customers';
\`\`\`

## clustering_coverage

**Problem:** Large tables lack clustering keys for query performance.

**Fix Pattern:**
\`\`\`sql
-- Add clustering key on frequently filtered/joined columns
ALTER TABLE {schema}.{table} CLUSTER BY ({column1}, {column2});

-- Example: Cluster events by timestamp for time-range queries
ALTER TABLE ECOMMERCE.EVENTS CLUSTER BY (event_timestamp, event_type);

-- Monitor clustering
SELECT * FROM TABLE(INFORMATION_SCHEMA.AUTOMATIC_CLUSTERING_HISTORY(
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_DATE()),
    TABLE_NAME => '{schema}.{table}'
));
\`\`\`

## search_optimization_coverage

**Problem:** Tables lack search optimization for text queries.

**Fix Pattern:**
\`\`\`sql
-- Enable search optimization on table
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION;

-- Enable for specific columns (more targeted)
ALTER TABLE {schema}.{table} ADD SEARCH OPTIMIZATION 
ON SUBSTRING({text_column});

-- Example
ALTER TABLE ECOMMERCE.PRODUCTS ADD SEARCH OPTIMIZATION ON SUBSTRING(name), SUBSTRING(description);
\`\`\`
```

### 7.4 Current Remediation

**File:** `docs/remediation/current.md`

```markdown
# Current Factor Remediation

## change_tracking_coverage

**Problem:** Tables lack change tracking for CDC use cases.

**Fix Pattern:**
\`\`\`sql
-- Enable change tracking
ALTER TABLE {schema}.{table} SET CHANGE_TRACKING = TRUE;

-- Query changes
SELECT * FROM {schema}.{table}
CHANGES (INFORMATION => DEFAULT)
AT (TIMESTAMP => DATEADD('hour', -1, CURRENT_TIMESTAMP()));
\`\`\`

## stream_coverage

**Problem:** Tables lack streams for change data capture.

**Fix Pattern:**
\`\`\`sql
-- Create stream on table
CREATE OR REPLACE STREAM {schema}.{table}_stream ON TABLE {schema}.{table};

-- Query stream for changes
SELECT * FROM {schema}.{table}_stream;

-- Process and advance stream (typically in a task)
INSERT INTO {target_table} SELECT * FROM {schema}.{table}_stream WHERE METADATA$ACTION = 'INSERT';
\`\`\`

## data_freshness_pass_rate

**Problem:** Data is stale (not updated recently).

**Fix Pattern:**
\`\`\`sql
-- Option 1: Create task for regular refresh
CREATE OR REPLACE TASK {schema}.refresh_{table}_task
WAREHOUSE = {warehouse}
SCHEDULE = 'USING CRON 0 */6 * * * UTC'  -- Every 6 hours
AS
INSERT INTO {schema}.{table}
SELECT * FROM {source_table}
WHERE updated_at > (SELECT MAX(updated_at) FROM {schema}.{table});

ALTER TASK {schema}.refresh_{table}_task RESUME;

-- Option 2: Convert to dynamic table
CREATE OR REPLACE DYNAMIC TABLE {schema}.{table}_dynamic
TARGET_LAG = '1 hour'
WAREHOUSE = {warehouse}
AS
SELECT * FROM {source_table};
\`\`\`

## dynamic_table_coverage

**Problem:** Derived tables are static views instead of dynamic tables.

**Fix Pattern:**
\`\`\`sql
-- Convert view to dynamic table
CREATE OR REPLACE DYNAMIC TABLE {schema}.{table}
TARGET_LAG = '1 hour'  -- Or 'DOWNSTREAM' for real-time
WAREHOUSE = {warehouse}
AS
{view_definition_sql};

-- Drop old view if replacing
DROP VIEW IF EXISTS {schema}.{old_view_name};
\`\`\`
```

### 7.5 Correlated Remediation

**File:** `docs/remediation/correlated.md`

```markdown
# Correlated Factor Remediation

## object_tag_coverage

**Problem:** Tables lack tags for classification and lineage.

**Fix Pattern:**
\`\`\`sql
-- Apply domain tag to table
ALTER TABLE {schema}.{table} SET TAG {tag_db}.{tag_schema}.data_domain = '{domain}';

-- Apply owner tag
ALTER TABLE {schema}.{table} SET TAG {tag_db}.{tag_schema}.owner = '{owner_team}';

-- Example
ALTER TABLE ECOMMERCE.CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'customer';
ALTER TABLE ECOMMERCE.CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.owner = 'customer-data-team';
\`\`\`

## column_tag_coverage

**Problem:** Columns lack tags for classification.

**Fix Pattern:**
\`\`\`sql
-- Apply PII tag to column
ALTER TABLE {schema}.{table} MODIFY COLUMN {column} 
SET TAG {tag_db}.{tag_schema}.pii = '{pii_type}';

-- Apply sensitivity tag
ALTER TABLE {schema}.{table} MODIFY COLUMN {column}
SET TAG {tag_db}.{tag_schema}.sensitivity = '{level}';

-- Example
ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN email SET TAG AIRD_DEMO.ECOMMERCE.pii = 'email';
ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN email SET TAG AIRD_DEMO.ECOMMERCE.sensitivity = 'confidential';
\`\`\`

## lineage_queryable

**Problem:** Lineage data not being captured or queryable.

**Fix Pattern:**
\`\`\`sql
-- Lineage is automatic in Snowflake via ACCESS_HISTORY
-- Ensure you have appropriate role to query it

-- Grant access to lineage data
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {role};

-- Query lineage (which tables read from which)
SELECT 
    query_id,
    user_name,
    direct_objects_accessed,
    base_objects_accessed,
    objects_modified
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
LIMIT 100;
\`\`\`
```

### 7.6 Compliant Remediation

**File:** `docs/remediation/compliant.md`

```markdown
# Compliant Factor Remediation

## masking_policy_coverage

**Problem:** PII columns lack masking policies.

**Fix Pattern:**
\`\`\`sql
-- Create masking policy for emails
CREATE OR REPLACE MASKING POLICY {schema}.email_mask AS (val STRING) 
RETURNS STRING ->
CASE 
    WHEN CURRENT_ROLE() IN ('ADMIN', 'DATA_ENGINEER') THEN val
    WHEN CURRENT_ROLE() IN ('ANALYST') THEN REGEXP_REPLACE(val, '(.)[^@]*(@.*)', '\\1***\\2')
    ELSE '***@***.***'
END;

-- Apply to column
ALTER TABLE {schema}.{table} MODIFY COLUMN {column} 
SET MASKING POLICY {schema}.email_mask;

-- Create masking policy for phone numbers
CREATE OR REPLACE MASKING POLICY {schema}.phone_mask AS (val STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'DATA_ENGINEER') THEN val
    ELSE REGEXP_REPLACE(val, '(\\+?\\d{1,3})?[-.\\s]?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?(\\d{4})', '***-***-\\2')
END;

ALTER TABLE {schema}.{table} MODIFY COLUMN {column}
SET MASKING POLICY {schema}.phone_mask;
\`\`\`

## row_access_policy_coverage

**Problem:** Tables lack row-level security.

**Fix Pattern:**
\`\`\`sql
-- Create row access policy
CREATE OR REPLACE ROW ACCESS POLICY {schema}.{table}_rap AS ({binding_column} VARCHAR)
RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() = 'ADMIN' THEN TRUE
    WHEN CURRENT_ROLE() = 'ANALYST' AND {binding_column} = CURRENT_USER() THEN TRUE
    ELSE FALSE
END;

-- Apply to table
ALTER TABLE {schema}.{table} ADD ROW ACCESS POLICY {schema}.{table}_rap ON ({column});

-- Example: Users can only see their own customer data
CREATE OR REPLACE ROW ACCESS POLICY ECOMMERCE.customer_rap AS (owner_id VARCHAR)
RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ADMIN', 'DATA_ENGINEER') OR owner_id = CURRENT_USER();

ALTER TABLE ECOMMERCE.CUSTOMERS ADD ROW ACCESS POLICY ECOMMERCE.customer_rap ON (customer_id);
\`\`\`

## sensitive_column_tagged

**Problem:** Sensitive columns lack classification tags.

**Fix Pattern:**
\`\`\`sql
-- Tag PII columns
ALTER TABLE {schema}.{table} MODIFY COLUMN email 
SET TAG {tag_db}.{tag_schema}.pii = 'email';

ALTER TABLE {schema}.{table} MODIFY COLUMN phone
SET TAG {tag_db}.{tag_schema}.pii = 'phone';

ALTER TABLE {schema}.{table} MODIFY COLUMN email
SET TAG {tag_db}.{tag_schema}.sensitivity = 'confidential';

-- Use Snowflake's built-in classification (if available)
-- This auto-detects PII
SELECT SYSTEM$CLASSIFY('{schema}.{table}', {'auto_tag': true});
\`\`\`

## network_policy_exists

**Problem:** No network policy configured for account security.

**Fix Pattern:**
\`\`\`sql
-- Create network policy (ACCOUNTADMIN required)
CREATE OR REPLACE NETWORK POLICY {policy_name}
ALLOWED_IP_LIST = ('{ip1}', '{ip2}', '{cidr_range}')
BLOCKED_IP_LIST = ()
COMMENT = 'Restrict access to corporate IPs';

-- Apply to account
ALTER ACCOUNT SET NETWORK_POLICY = {policy_name};

-- Or apply to specific user
ALTER USER {user_name} SET NETWORK_POLICY = {policy_name};
\`\`\`
```

---

## 8. Demo Runbook

**File to create:** `docs/demo/snowflake-demo-runbook.md`

### 8.1 Pre-Demo Setup (15 minutes)

```bash
# 1. Ensure Snowflake connection works
export AIRD_CONNECTION_STRING="snowflake://user:pass@account/AIRD_DEMO/ECOMMERCE?warehouse=COMPUTE_WH"
aird discover -c "$AIRD_CONNECTION_STRING"

# 2. Run setup script in Snowflake
# Copy scripts/demo/snowflake_setup.sql to Snowflake worksheet and execute
# Or use snowsql:
snowsql -a <account> -u <user> -f scripts/demo/snowflake_setup.sql

# 3. Verify problematic data exists
aird assess -c "$AIRD_CONNECTION_STRING" --dry-run
```

### 8.2 Demo Script (15 minutes)

#### Part 1: Initial Assessment (3 minutes)

```bash
# Run full assessment
aird assess -c "$AIRD_CONNECTION_STRING" -o markdown

# Expected output: Low scores across all factors
# Factor: Clean      - L1: ~40% | L2: ~20% | L3: ~10%
# Factor: Contextual - L1: ~25% | L2: ~10% | L3: ~5%
# Factor: Consumable - L1: ~0%  | L2: ~0%  | L3: ~0%
# Factor: Current    - L1: ~20% | L2: ~10% | L3: ~0%
# Factor: Correlated - L1: ~0%  | L2: ~0%  | L3: ~0%
# Factor: Compliant  - L1: ~0%  | L2: ~0%  | L3: ~0%
```

**Talking points:**
- "This is a typical state for production data that wasn't built with AI in mind"
- "Let's see what specific issues we have"
- "Notice how L3 (training) is much stricter than L1 (analytics)"

#### Part 2: Factor-by-Factor Fix (10 minutes)

For each factor, show the problem, have Coco generate the fix, execute it, explain the improvement.

**Factor 0: Clean**
```sql
-- Fix null rate
UPDATE ECOMMERCE.CUSTOMERS SET email = CONCAT('unknown_', customer_id, '@placeholder.com') WHERE email IS NULL;
UPDATE ECOMMERCE.CUSTOMERS SET phone = '+1-000-000-0000' WHERE phone IS NULL;

-- Fix duplicates
CREATE OR REPLACE TABLE ECOMMERCE.ORDERS AS
SELECT DISTINCT * FROM ECOMMERCE.ORDERS;

-- Fix format inconsistency
ALTER TABLE ECOMMERCE.ORDERS ADD COLUMN order_date_clean DATE;
UPDATE ECOMMERCE.ORDERS SET order_date_clean = TRY_TO_DATE(order_date);
```

**Factor 1: Contextual**
```sql
-- Add primary keys
ALTER TABLE ECOMMERCE.CUSTOMERS ADD PRIMARY KEY (customer_id);
ALTER TABLE ECOMMERCE.ORDERS ADD PRIMARY KEY (order_id);
ALTER TABLE ECOMMERCE.ORDER_ITEMS ADD PRIMARY KEY (item_id);
ALTER TABLE ECOMMERCE.PRODUCTS ADD PRIMARY KEY (product_id);
ALTER TABLE ECOMMERCE.EVENTS ADD PRIMARY KEY (event_id);

-- Add foreign keys
ALTER TABLE ECOMMERCE.ORDERS ADD FOREIGN KEY (customer_id) REFERENCES ECOMMERCE.CUSTOMERS(customer_id);
ALTER TABLE ECOMMERCE.ORDER_ITEMS ADD FOREIGN KEY (order_id) REFERENCES ECOMMERCE.ORDERS(order_id);
ALTER TABLE ECOMMERCE.ORDER_ITEMS ADD FOREIGN KEY (product_id) REFERENCES ECOMMERCE.PRODUCTS(product_id);
```

**Factor 2: Consumable**
```sql
-- Add table comments
COMMENT ON TABLE ECOMMERCE.CUSTOMERS IS 'Master customer table with profile and contact information';
COMMENT ON TABLE ECOMMERCE.ORDERS IS 'Order headers with customer reference and totals';
COMMENT ON TABLE ECOMMERCE.ORDER_ITEMS IS 'Order line items with product and quantity';
COMMENT ON TABLE ECOMMERCE.PRODUCTS IS 'Product catalog with pricing and categories';
COMMENT ON TABLE ECOMMERCE.EVENTS IS 'User activity event stream for analytics';

-- Add column comments (abbreviated)
COMMENT ON COLUMN ECOMMERCE.CUSTOMERS.customer_id IS 'Unique customer identifier (UUID)';
COMMENT ON COLUMN ECOMMERCE.CUSTOMERS.email IS 'Primary email for communications';

-- Add clustering to large table
ALTER TABLE ECOMMERCE.EVENTS CLUSTER BY (event_timestamp, event_type);
```

**Factor 3: Current**
```sql
-- Enable change tracking
ALTER TABLE ECOMMERCE.CUSTOMERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ECOMMERCE.ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE ECOMMERCE.EVENTS SET CHANGE_TRACKING = TRUE;

-- Create stream for CDC
CREATE OR REPLACE STREAM ECOMMERCE.EVENTS_STREAM ON TABLE ECOMMERCE.EVENTS;

-- Add fresh data to events
INSERT INTO ECOMMERCE.EVENTS (event_id, customer_id, event_type, event_data, event_timestamp)
SELECT UUID_STRING(), customer_id, 'page_view', OBJECT_CONSTRUCT('fresh', true), CURRENT_TIMESTAMP()
FROM ECOMMERCE.CUSTOMERS LIMIT 100;
```

**Factor 4: Correlated**
```sql
-- Apply tags
ALTER TABLE ECOMMERCE.CUSTOMERS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'customer';
ALTER TABLE ECOMMERCE.ORDERS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'order';
ALTER TABLE ECOMMERCE.PRODUCTS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'product';
ALTER TABLE ECOMMERCE.EVENTS SET TAG AIRD_DEMO.ECOMMERCE.data_domain = 'event';

ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN email SET TAG AIRD_DEMO.ECOMMERCE.pii = 'email';
ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN phone SET TAG AIRD_DEMO.ECOMMERCE.pii = 'phone';
```

**Factor 5: Compliant**
```sql
-- Create and apply masking policies
CREATE OR REPLACE MASKING POLICY ECOMMERCE.email_mask AS (val STRING) RETURNS STRING ->
CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val ELSE REGEXP_REPLACE(val, '(.)[^@]*(@.*)', '\\1***\\2') END;

ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN email SET MASKING POLICY ECOMMERCE.email_mask;

CREATE OR REPLACE MASKING POLICY ECOMMERCE.phone_mask AS (val STRING) RETURNS STRING ->
CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val ELSE '***-***-****' END;

ALTER TABLE ECOMMERCE.CUSTOMERS MODIFY COLUMN phone SET MASKING POLICY ECOMMERCE.phone_mask;
```

#### Part 3: Re-Assessment with Comparison (2 minutes)

```bash
# Re-run assessment with comparison
aird assess -c "$AIRD_CONNECTION_STRING" -o markdown --compare

# Expected: Dramatic improvement across all factors
# Factor: Clean      - L1: 100% (+60) | L2: 95% (+75) | L3: 90% (+80)
# Factor: Contextual - L1: 100% (+75) | L2: 100% (+90) | L3: 95% (+90)
# ...
```

**Talking points:**
- "We went from ~20% overall to ~90%+ in 10 minutes"
- "This data is now ready for RAG and approaching training-ready"
- "The agent identified specific issues; Coco generated SQL fixes"

---

## 9. Implementation Checklist

> **📖 Before starting:** Read **`/factors.md`** (root directory) for canonical factor definitions, requirements, and Snowflake capabilities. All implementations should align with that document.

### 9.1 Files to Create

- [ ] `agent/suites/definitions/consumable_snowflake.yaml`
- [ ] `agent/suites/definitions/current_snowflake.yaml`
- [ ] `agent/suites/definitions/correlated_snowflake.yaml`
- [ ] `agent/suites/definitions/compliant_snowflake.yaml`
- [ ] `agent/suites/definitions/snowflake_all.yaml` (composed suite)
- [ ] `scripts/demo/snowflake_setup.sql`
- [ ] `scripts/demo/snowflake_tags.sql`
- [ ] `scripts/demo/snowflake_fix_clean.sql`
- [ ] `scripts/demo/snowflake_fix_contextual.sql`
- [ ] `scripts/demo/snowflake_fix_consumable.sql`
- [ ] `scripts/demo/snowflake_fix_current.sql`
- [ ] `scripts/demo/snowflake_fix_correlated.sql`
- [ ] `scripts/demo/snowflake_fix_compliant.sql`
- [ ] `docs/remediation/clean.md`
- [ ] `docs/remediation/contextual.md`
- [ ] `docs/remediation/consumable.md`
- [ ] `docs/remediation/current.md`
- [ ] `docs/remediation/correlated.md`
- [ ] `docs/remediation/compliant.md`
- [ ] `docs/demo/snowflake-demo-runbook.md`

### 9.2 Files to Update

- [ ] `agent/requirements_registry.yaml` — add 14 new requirements
- [ ] `agent/suites/definitions/snowflake_common.yaml` — update extends list
- [ ] `docs/definitions.md` — update factor status
- [ ] `README.md` — update suite table

### 9.3 Validation Steps

After implementation:

1. [ ] Run `aird suites` — verify all new suites are discovered
2. [ ] Run `aird requirements` — verify all new requirements are registered
3. [ ] Run `python scripts/verify_setup.py` — verify no import errors
4. [ ] Test each new suite individually:
   - [ ] `aird assess -c "..." --suite consumable_snowflake --dry-run`
   - [ ] `aird assess -c "..." --suite current_snowflake --dry-run`
   - [ ] `aird assess -c "..." --suite correlated_snowflake --dry-run`
   - [ ] `aird assess -c "..." --suite compliant_snowflake --dry-run`
5. [ ] Run full demo end-to-end in test Snowflake account
6. [ ] Time the demo (target: <15 minutes)

---

## 10. File Manifest

### 10.1 New Files Summary

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `agent/suites/definitions/consumable_snowflake.yaml` | Consumable factor tests | ~50 |
| `agent/suites/definitions/current_snowflake.yaml` | Current factor tests | ~60 |
| `agent/suites/definitions/correlated_snowflake.yaml` | Correlated factor tests | ~50 |
| `agent/suites/definitions/compliant_snowflake.yaml` | Compliant factor tests | ~70 |
| `agent/suites/definitions/snowflake_all.yaml` | Composed suite (all 6 factors) | ~15 |
| `scripts/demo/snowflake_setup.sql` | Demo data with problems | ~200 |
| `scripts/demo/snowflake_tags.sql` | Tag creation script | ~30 |
| `scripts/demo/snowflake_fix_*.sql` (6 files) | Fix scripts per factor | ~50 each |
| `docs/remediation/*.md` (6 files) | Remediation templates | ~100 each |
| `docs/demo/snowflake-demo-runbook.md` | Demo script | ~200 |

### 10.2 Directory Structure After Implementation

```
agent/
├── suites/
│   └── definitions/
│       ├── clean_common.yaml          (existing)
│       ├── clean_snowflake.yaml       (existing)
│       ├── clean_sqlite.yaml          (existing)
│       ├── contextual_snowflake.yaml  (existing)
│       ├── snowflake_common.yaml      (existing)
│       ├── consumable_snowflake.yaml  (NEW)
│       ├── current_snowflake.yaml     (NEW)
│       ├── correlated_snowflake.yaml  (NEW)
│       ├── compliant_snowflake.yaml   (NEW)
│       └── snowflake_all.yaml         (NEW)
├── requirements_registry.yaml         (UPDATED)

scripts/
└── demo/
    ├── snowflake_setup.sql            (NEW)
    ├── snowflake_tags.sql             (NEW)
    ├── snowflake_fix_clean.sql        (NEW)
    ├── snowflake_fix_contextual.sql   (NEW)
    ├── snowflake_fix_consumable.sql   (NEW)
    ├── snowflake_fix_current.sql      (NEW)
    ├── snowflake_fix_correlated.sql   (NEW)
    └── snowflake_fix_compliant.sql    (NEW)

docs/
├── remediation/
│   ├── clean.md                       (NEW)
│   ├── contextual.md                  (NEW)
│   ├── consumable.md                  (NEW)
│   ├── current.md                     (NEW)
│   ├── correlated.md                  (NEW)
│   └── compliant.md                   (NEW)
└── demo/
    └── snowflake-demo-runbook.md      (NEW)
```

---

## Appendix A: SQL Query Validation Notes

### A.1 Snowflake System Tables Used

| Table/View | Factor | Permission Required |
|------------|--------|---------------------|
| `information_schema.tables` | All | SELECT on schema |
| `information_schema.columns` | Clean, Consumable, Compliant | SELECT on schema |
| `information_schema.table_constraints` | Contextual | SELECT on schema |
| `information_schema.streams` | Current | SELECT on schema |
| `information_schema.policy_references` | Compliant | SELECT on schema |
| `snowflake.account_usage.tag_references` | Correlated, Compliant | GOVERNANCE_VIEWER or ACCOUNTADMIN |
| `snowflake.account_usage.access_history` | Correlated | GOVERNANCE_VIEWER or ACCOUNTADMIN |
| `information_schema.network_policies` | Compliant | ACCOUNTADMIN |

### A.2 Potential Query Issues

1. **Account Usage latency**: `snowflake.account_usage` views have up to 3-hour latency. Demo should account for this.

2. **Role requirements**: Some queries require ACCOUNTADMIN. Document fallback queries for lower privilege roles.

3. **Empty result handling**: All queries use `NULLIF(..., 0)` to avoid division by zero.

4. **Case sensitivity**: Snowflake identifiers are uppercase by default. Queries use `UPPER()` for comparisons.

### A.3 Testing Queries Independently

Before integrating, test each query in Snowflake worksheet:

```sql
-- Test consumable: column_comment_coverage
SELECT COUNT_IF(comment IS NOT NULL AND comment != '') * 1.0 / NULLIF(COUNT(*), 0) AS v
FROM information_schema.columns
WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG');
-- Expected: 0.0 (no comments initially)
```

---

## Appendix B: Threshold Rationale

### B.1 Why These Thresholds?

| Factor | Requirement | L1 | L2 | L3 | Rationale |
|--------|-------------|----|----|-----|-----------|
| Consumable | column_comment_coverage | 0.3 | 0.6 | 0.9 | Documentation is often lacking; progressive improvement |
| Current | change_tracking_coverage | 0.2 | 0.5 | 0.8 | CDC not universal; critical for RAG/training freshness |
| Correlated | object_tag_coverage | 0.2 | 0.5 | 0.8 | Tags require governance maturity; progressive |
| Compliant | masking_policy_coverage | 0.3 | 0.7 | 0.95 | PII protection critical for AI; near-complete for training |

### B.2 Adjusting for Demo

For a more dramatic demo, consider starting with stricter thresholds (more failures) and showing improvement. Or use `--thresholds` flag with custom values.

---

**End of Plan**
