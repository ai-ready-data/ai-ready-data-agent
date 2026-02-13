# Report specification

This document defines the canonical shape of assessment reports produced by the AI-Ready Data Agent. It covers both the **JSON schema** (the source of truth for storage, diffing, and programmatic access) and the **markdown rendering** (the human-readable presentation). It applies to single-connection and estate (multi-connection) reports.

The CLI spec ([cli-spec.md](cli-spec.md)) references this document as the schema authority for the Report artifact.

---

## 1. Design principles

- **Self-contained:** A report includes everything needed to understand the assessment — thresholds, directions, factor summaries, and measured values. No external lookup is required to interpret pass/fail.
- **Factor-first:** Results are grouped by factor for both JSON (`factor_summary`) and markdown rendering. The flat `results` list is preserved for machine consumption and diffing.
- **Workload-aware:** Reports surface scores at all three workload levels (L1/L2/L3). When a `target_workload` is set, rendering emphasizes that level.
- **Backward-compatible:** New fields are additive. Consumers that ignore unknown keys continue to work.

---

## 2. Single-connection report (JSON)

A single-connection report is produced by `aird assess` (one connection) or `aird report`.

### Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `created_at` | string (ISO-8601) | yes | Timestamp of report creation (UTC). |
| `assessment_id` | string (UUID) | no | Set after `save`; absent if `--no-save`. |
| `connection_fingerprint` | string | yes | Redacted connection identifier (no credentials). |
| `target_workload` | string or null | yes | `"l1"`, `"l2"`, `"l3"`, or `null`. From user context (`target_level`) or null when not specified. |
| `summary` | object | yes | Aggregate pass counts and percentages. See **Summary object**. |
| `factor_summary` | array | yes | Per-factor roll-up. See **Factor summary object**. |
| `results` | array | yes | Flat list of test results. See **Result object**. |
| `question_results` | array | no | Survey / question-based results. Present when `--survey` is used. |
| `not_assessed` | array | yes | Requirements or factors that could not be assessed. See **Not-assessed object**. |
| `inventory` | object or null | yes | Discovery metadata (schemas, tables, columns). Null when not available. |
| `user_context` | object | yes | Context from user YAML (schemas, tables, target_level, etc.). Empty object `{}` when not provided. |
| `environment` | object | yes | Reserved for platform version, driver version, etc. Empty object `{}` for now. |
| `data_products` | array | no | Per-data-product report objects. Present when context defines `data_products`. See **Data product report object**. |

When `data_products` is present, the top-level `summary` and `factor_summary` represent the aggregate across all products. The flat `results` list remains unchanged (each result's `test_id` encodes schema.table, which maps back to a product). When `data_products` is absent, behavior is identical to a report without products.

### Data product report object

Each entry in the `data_products` array represents one named data product and its scoped assessment results.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Data product name (e.g. `"customer_360"`). |
| `owner` | string or null | Owner team or person. Null when not specified. |
| `target_workload` | string or null | Per-product workload override (`"l1"`, `"l2"`, `"l3"`, or `null`). |
| `assets` | array | List of table identifiers (e.g. `["public.customers", "public.orders"]`) belonging to this product. |
| `summary` | object | Same shape as **Summary object**, scoped to this product's assets. |
| `factor_summary` | array | Same shape as **Factor summary object**, scoped to this product's assets. |

### Summary object

| Field | Type | Description |
|-------|------|-------------|
| `total_tests` | integer | Number of test results. |
| `l1_pass` | integer | Tests passing at L1. |
| `l2_pass` | integer | Tests passing at L2. |
| `l3_pass` | integer | Tests passing at L3. |
| `l1_pct` | float | Percentage passing at L1 (0.0–100.0). |
| `l2_pct` | float | Percentage passing at L2. |
| `l3_pct` | float | Percentage passing at L3. |

### Factor summary object

Each entry in the `factor_summary` array represents one factor that has at least one test result.

| Field | Type | Description |
|-------|------|-------------|
| `factor` | string | Factor name (e.g. `"clean"`, `"contextual"`). |
| `total_tests` | integer | Number of tests for this factor. |
| `l1_pass` | integer | Tests passing at L1 for this factor. |
| `l2_pass` | integer | Tests passing at L2 for this factor. |
| `l3_pass` | integer | Tests passing at L3 for this factor. |
| `l1_pct` | float | Percentage passing at L1 for this factor. |
| `l2_pct` | float | Percentage passing at L2 for this factor. |
| `l3_pct` | float | Percentage passing at L3 for this factor. |

### Result object

Each entry in the `results` array is one executed test.

| Field | Type | Description |
|-------|------|-------------|
| `test_id` | string | Unique test identifier (e.g. `"null_rate\|main\|products\|name"`). |
| `factor` | string | Factor name. |
| `requirement` | string | Requirement key (e.g. `"null_rate"`, `"primary_key_defined"`). |
| `target_type` | string | `"column"`, `"table"`, or `"platform"`. |
| `measured_value` | number or null | The value returned by the test query. Null on error. |
| `threshold` | object | The L1/L2/L3 threshold values used for this test. Shape: `{ "l1": float, "l2": float, "l3": float }`. |
| `direction` | string | `"lte"` (pass when measured <= threshold) or `"gte"` (pass when measured >= threshold). |
| `l1_pass` | boolean | Whether the test passes at L1. |
| `l2_pass` | boolean | Whether the test passes at L2. |
| `l3_pass` | boolean | Whether the test passes at L3. |
| `error` | string | Present only when the test query failed. |

### Not-assessed object

Each entry describes a requirement or factor that was skipped or could not be evaluated.

| Field | Type | Description |
|-------|------|-------------|
| `factor` | string | Factor name. |
| `requirement` | string | Requirement key. |
| `reason` | string | Why it was not assessed (e.g. `"Platform does not support semantic views"`, `"No test defined for this requirement"`). |

### Question results (survey)

Each entry in the optional `question_results` array:

| Field | Type | Description |
|-------|------|-------------|
| `factor` | string | Factor name. |
| `requirement` | string | Requirement key. |
| `question_text` | string | The question that was asked. |
| `answer` | string | The user's answer (or default). |
| `l1_pass` | boolean | Whether the answer passes at L1. |
| `l2_pass` | boolean | Whether the answer passes at L2. |
| `l3_pass` | boolean | Whether the answer passes at L3. |

---

## 3. Estate report (JSON)

An estate report is produced by `aird assess` with multiple connections. It wraps per-connection sub-reports.

### Top-level fields (additions to single-connection)

| Field | Type | Description |
|-------|------|-------------|
| `platforms` | array | List of per-connection sub-reports. Each has `connection_fingerprint`, `summary`, `factor_summary`, `results`, `inventory`, and optional `error`. |
| `aggregate_summary` | object | Roll-up summary across all connections. Same shape as **Summary object** plus `platforms_count`. |

The top-level `summary` and `aggregate_summary` are the same object in estate mode. `factor_summary` at the top level aggregates across all connections. `results` at the top level is an empty array (per-connection results live in `platforms[].results`). `connection_fingerprint` at the top level is an empty string.

---

## 4. Markdown rendering

The markdown output (`report_to_markdown`) follows this section order. The format is designed for both human reading and agent presentation.

### 4.1 Single-connection report (no data products)

```
# AI-Ready Data Assessment Report

**Created:** <created_at>
**Connection:** <connection_fingerprint>
**Target workload:** <target_workload or "Not specified">

## Summary

- Total tests: N
- L1 pass: X/N (P%)
- L2 pass: X/N (P%)
- L3 pass: X/N (P%)

## Factor: Clean

L1: X/N (P%) | L2: X/N (P%) | L3: X/N (P%)

| Test | Requirement | Measured | Threshold (L1/L2/L3) | Direction | L1 | L2 | L3 |
|------|-------------|----------|----------------------|-----------|----|----|-----|
| test_id | requirement_key | 0.15 | 0.20 / 0.05 / 0.01 | lte | PASS | FAIL | FAIL |

## Factor: Contextual

(same structure)

## Survey Results

(if question_results present)

- **factor / requirement**: PASS/FAIL
  - Question text
  - Answer: ...

## Not Assessed

(if not_assessed is non-empty)

- **factor / requirement**: reason

## Appendix: Inventory

- Schemas: N
- Tables: N
- Columns: N
```

### 4.2 Single-connection report (with data products)

When the context defines `data_products`, the report renders per-product sections with an aggregate summary at the top.

```
# AI-Ready Data Assessment Report

**Created:** <created_at>
**Connection:** <connection_fingerprint>
**Target workload:** <target_workload or "Not specified">
**Data products:** N

## Summary (Aggregate)

- Total tests: N
- L1 pass: X/N (P%)
- L2 pass: X/N (P%)
- L3 pass: X/N (P%)

## Data Product: customer_360

**Owner:** data-platform-team | **Workload:** RAG (L2)
**Assets:** public.customers, public.addresses, public.orders

L1: X/N (P%) | L2: X/N (P%) | L3: X/N (P%)

### Factor: Clean

| Test | Requirement | Measured | Threshold (L1/L2/L3) | Direction | L1 | L2 | L3 |
|------|-------------|----------|----------------------|-----------|----|----|-----|
| test_id | requirement_key | 0.15 | 0.20 / 0.05 / 0.01 | lte | PASS | FAIL | FAIL |

### Factor: Contextual

(same structure)

## Data Product: event_stream

**Owner:** analytics-eng | **Workload:** Analytics (L1)
**Assets:** events.*

(same factor structure)

## Survey Results

(if question_results present)

## Not Assessed

(if not_assessed is non-empty)

## Appendix: Inventory

- Schemas: N
- Tables: N
- Columns: N
```

### 4.3 Estate report

```
# AI-Ready Data Assessment Report (Estate)

**Created:** <created_at>
**Platforms:** N
**Target workload:** <target_workload or "Not specified">

## Aggregate Summary

- Total tests: N
- L1 pass: X/N (P%)
- L2 pass: X/N (P%)
- L3 pass: X/N (P%)

## 1. <connection_fingerprint>

### Factor: Clean

(same table structure as single-connection)

## 2. <connection_fingerprint>

(repeat per connection)
```

---

## 5. Diff rendering

When comparing two reports (`aird diff`), the output highlights:

- **Tests added / removed** between runs.
- **Pass/fail changes** per test (e.g. `null_rate|main|products|name: L2 FAIL → PASS`).
- **Score deltas** per factor and overall (e.g. `Clean L2: 60% → 80%`).

The diff format is implementation-defined but should be human-readable markdown and optionally machine-readable JSON.

---

## 6. Versioning

Reports do not carry an explicit schema version field today. If the schema changes in a backward-incompatible way, a `schema_version` field will be added. For now, new fields are additive and consumers should ignore unknown keys.

---

## 7. Relationship to other specs

- **CLI spec** ([cli-spec.md](cli-spec.md)): Defines the commands that produce and consume reports. Section 3 references this spec.
- **Factor spec** ([factor-spec.md](factor-spec.md)): Defines requirement keys used in `results[].requirement` and `factor_summary[].factor`.
- **Thresholds** (`agent/thresholds.py`): Source of default threshold values and directions embedded in results.
