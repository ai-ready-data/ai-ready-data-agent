# Factors Sub-Skills

This directory contains one skill file per AI-Ready Data factor. Each skill is **self-contained** with:

1. Factor definition and why it matters for AI
2. Requirements table with L1/L2/L3 thresholds
3. Assessment SQL queries for Snowflake
4. Interpretation guidance
5. Remediation patterns with concrete SQL

## Factor Index

| # | Factor | Key Question | Skill |
|---|--------|--------------|-------|
| 0 | **Clean** | Is the data trustworthy? | [0-clean.md](0-clean.md) |
| 1 | **Contextual** | Can AI interpret it without human context? | [1-contextual.md](1-contextual.md) |
| 2 | **Consumable** | Can AI consume it without transformation? | [2-consumable.md](2-consumable.md) |
| 3 | **Current** | Does it reflect the present state? | [3-current.md](3-current.md) |
| 4 | **Correlated** | Can we trace data to decisions? | [4-correlated.md](4-correlated.md) |
| 5 | **Compliant** | Is it safe to use for AI? | [5-compliant.md](5-compliant.md) |

## Usage

When assessing a specific factor:
1. Load the corresponding skill file
2. Execute SQL queries via `snowflake_sql_execute`
3. Compare results to thresholds based on workload level (L1/L2/L3)
4. Use remediation patterns for failures

## Threshold Quick Reference

| Requirement | Dir | L1 | L2 | L3 |
|-------------|-----|----|----|-----|
| **Clean** |
| `null_rate` | lte | 0.20 | 0.05 | 0.01 |
| `duplicate_rate` | lte | 0.10 | 0.02 | 0.01 |
| **Contextual** |
| `pk_coverage` | gte | 0.70 | 0.90 | 1.00 |
| `fk_coverage` | gte | 0.50 | 0.80 | 0.95 |
| `comment_coverage` | gte | 0.30 | 0.70 | 0.90 |
| `table_comment_coverage` | gte | 0.50 | 0.80 | 1.00 |
| **Consumable** |
| `clustering_coverage` | gte | 0.30 | 0.60 | 0.80 |
| `search_optimization_coverage` | gte | 0.20 | 0.50 | 0.70 |
| **Current** |
| `change_tracking_coverage` | gte | 0.30 | 0.70 | 0.90 |
| `stream_coverage` | gte | 0.20 | 0.50 | 0.80 |
| `dynamic_table_coverage` | gte | 0.10 | 0.30 | 0.50 |
| **Correlated** |
| `object_tag_coverage` | gte | 0.30 | 0.60 | 0.90 |
| `column_tag_coverage` | gte | 0.20 | 0.50 | 0.80 |
| `lineage_queryable` | gte | 0.00 | 1.00 | 1.00 |
| **Compliant** |
| `masking_policy_coverage` | gte | 0.50 | 0.80 | 1.00 |
| `row_access_policy_coverage` | gte | 0.30 | 0.60 | 0.90 |
| `sensitive_column_tagged` | gte | 0.50 | 0.80 | 1.00 |

**Direction:**
- `lte` = lower is better (value must be ≤ threshold)
- `gte` = higher is better (value must be ≥ threshold)
