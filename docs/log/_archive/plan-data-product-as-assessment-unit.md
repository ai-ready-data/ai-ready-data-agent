# Plan: Data Product as the Unit of Assessment

**Date:** 2026-02-12

**Status:** Implemented.

---

## Goal

Introduce the concept of "data product" as the primary unit of assessment in the AI-Ready Data Agent. This changes how the agent discovers, scopes, reports on, and tracks assessments without modifying the six factors, test suites, or threshold logic.

---

## Problem

Today the assessment agent operates on raw database objects: connections, schemas, tables, columns. Discovery enumerates everything, the user confirms scope by excluding schemas/tables, and the report groups results by factor. This works mechanically but has three problems:

- **No meaningful scope boundary.** "Assess this Snowflake account" or "assess this schema" is too broad or too arbitrary. Results are a wall of pass/fail by table with no organizational logic.
- **Results aren't actionable.** A report that says "17 of 42 tables fail null_rate at L2" doesn't tell you which business function is at risk or who owns the problem.
- **No unit for tracking over time.** History and diff operate on connection fingerprint, which is a platform concept, not a business concept. You can't ask "how has our customer 360 improved since last month?"

---

## Concept: Data Product

A **data product** is a named, bounded set of data assets maintained by a defined owner to serve a specific business function. It is the unit the agent assesses, reports on, and tracks.

A data product has:

- **Name** (user-declared, e.g. "customer_360", "event_stream")
- **Owner** (optional, e.g. team or person)
- **Assets** (tables, schemas, or patterns that belong to it)
- **Target workload** (optional per-product override of L1/L2/L3)

The six factors are unchanged. Tests are unchanged. What changes is that results are **grouped and scored per data product**, and the report tells a story about business-relevant units rather than raw database objects.

---

## Changes Made

### 1. Definitions (`docs/definitions.md`)

- Added **Data product** definition between "Data layer" and "Data asset."
- Updated **Data asset** definition to clarify that assets belong to data products and results roll up to the product level.

### 2. Context YAML (`docs/specs/cli-spec.md`)

- Extended context YAML spec (section 5) to support a `data_products` key with entries containing `name`, `owner`, `workload`, `tables`, and `schemas`.
- Added `--product` flag documentation to section 5 (Data products in context).
- Documented the data product entry shape with a table of fields and requirements.

### 3. Report spec (`docs/specs/report-spec.md`)

- Added `data_products` (optional array) to the top-level report fields table.
- Added **Data product report object** section defining per-product fields: `name`, `owner`, `target_workload`, `assets`, `summary`, `factor_summary`.
- Added section 4.2 documenting the markdown rendering for reports with data products.
- Renumbered estate report section to 4.3.

### 4. Report builder (`agent/report.py`)

- Added `_build_summary()` helper (extracted from `build_report` for reuse).
- Added `_result_belongs_to_product()` to match test results to product definitions by parsing `test_id` format (`requirement|schema|table|column`).
- Added `_build_data_product_reports()` to build per-product report objects.
- Updated `build_report()` to accept optional `data_products` parameter and include product reports when present.
- Added `_render_summary_lines()` helper for reuse in aggregate and per-product contexts.
- Added `_render_data_product_section()` to render a full product section with metadata, summary, and factor breakdown.
- Added `_result_belongs_to_product_report()` for matching results in the rendering path (supports `schema.*` wildcard assets).
- Updated `_render_factor_section()` with `heading_level` parameter for nested product sections (## vs ###).
- Updated `report_to_markdown()` to render per-product sections when `data_products` is present, falling back to flat factor-by-factor view otherwise.

### 5. Storage (`agent/storage.py`)

- Added `data_product TEXT` column to `assessments` table in schema creation.
- Added migration path for existing databases (ALTER TABLE when column is missing).
- Updated `save_report()` to accept optional `data_product` keyword argument.
- Updated `list_assessments()` to accept optional `data_product_filter` and include it in WHERE clause and output.

### 6. CLI (`agent/cli.py`, `agent/config.py`)

- Added `product` field to `Config` dataclass.
- Added `history_product_filter` field to `Config`.
- Added `--product` argument to `assess` parser.
- Added `--product` argument to `history` parser (dest: `product_filter`).
- Added `product_filter` to `_ARG_MAP` routing.
- Updated `cmd_history()` to pass `data_product_filter` to `list_assessments()` and show product in output.

### 7. Pipeline (`agent/pipeline.py`)

- Updated `run_assess()` to read `data_products` from context YAML and pass to `build_report()`.
- Added `--product` filtering: when set, validates against context products and passes only the matched product.
- Updated `save_report()` call to include `data_product=product_name` when a single product is targeted.

### 8. Skills

- **`skills/discover/SKILL.md`**: Added Step 3 (Data Products) between discovery presentation and scope confirmation. Asks user if they want to organize tables into data products.
- **`skills/interview/SKILL.md`**: Added data products question (item 3) to Phase 1 pre-assessment interview. Renumbered subsequent items.

### 9. AGENTS.md

- Added "Data products" entry to "Where to find things" section.
- Updated workflow step 3 (Discover and confirm scope) to mention data product discovery and per-product assessment.

---

## What did NOT change

- The six factors (Clean, Contextual, Consumable, Current, Correlated, Compliant)
- Factor docs, requirement keys, thresholds, test suites
- Test execution logic (`run.py`, `expand_tests()`, platform adapters)
- The CLI command set (no new commands, only new flags)
- The connections manifest format (products are in context, not in connections)
- The agentic system spec (skills model, boundaries, read-only constraint)

---

## Backward Compatibility

- When no `data_products` key exists in context YAML, all behavior is identical to before.
- Reports without products omit the `data_products` field. Consumers that ignore unknown keys are unaffected.
- Storage schema migration adds a nullable column; existing rows are untouched.
- The `--product` flag is optional; omitting it gives the previous behavior.
