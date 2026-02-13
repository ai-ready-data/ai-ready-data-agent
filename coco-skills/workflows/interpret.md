# Workflow: Interpret

Guide for interpreting assessment results and presenting findings.

## Purpose

Transform raw metric values into actionable insights:
1. Apply thresholds based on workload level
2. Determine pass/fail status
3. Calculate factor and overall scores
4. Prioritize findings

## Threshold Application

### Direction Rules
- **`lte`** (lower is better): Value ≤ threshold = PASS
- **`gte`** (higher is better): Value ≥ threshold = PASS

### Workload Levels
| Level | Use Case | Strictness |
|-------|----------|------------|
| L1 | BI/Analytics | Lenient |
| L2 | RAG/Retrieval | Moderate |
| L3 | ML Training | Strict |

### Threshold Reference

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

## Scoring

### Requirement Score
```
For 'gte' requirements:
  score = min(value / threshold, 1.0)

For 'lte' requirements:
  score = max(1.0 - (value / threshold), 0.0) if value > threshold
  score = 1.0 if value <= threshold
```

### Factor Score
```
factor_score = average(requirement_scores)
```

### Overall Score
```
overall_score = average(factor_scores)
```

## Output Format

### Summary Table
```
## AI-Ready Data Assessment Results

**Schema:** {database}.{schema}
**Workload Level:** L{level}
**Overall Score:** {score}% ({pass_count}/{total_count} requirements passed)

| Factor | Score | Status |
|--------|-------|--------|
| Clean | 85% | ✓ Pass |
| Contextual | 60% | ✗ Fail |
| Consumable | 90% | ✓ Pass |
| Current | 40% | ✗ Fail |
| Correlated | 30% | ✗ Fail |
| Compliant | 70% | ✓ Pass |
```

### Detailed Factor View
```
### Factor 1: Contextual (60% - FAIL)

| Requirement | Value | Threshold | Status |
|-------------|-------|-----------|--------|
| pk_coverage | 0.80 | ≥0.90 | ✗ FAIL |
| fk_coverage | 0.75 | ≥0.80 | ✗ FAIL |
| comment_coverage | 0.45 | ≥0.70 | ✗ FAIL |
| table_comment_coverage | 0.90 | ≥0.80 | ✓ PASS |

**Priority Issues:**
1. 2 tables missing primary keys
2. 25% of columns lack comments
```

## Prioritization

Rank failures by:
1. **Impact**: How much does this affect AI workloads?
2. **Gap**: How far from threshold?
3. **Effort**: How hard to fix?

### High Priority (Fix First)
- `null_rate` > 0.20 (data quality)
- `pk_coverage` < 0.90 (integrity)
- `masking_policy_coverage` < 0.80 (compliance risk)

### Medium Priority
- `comment_coverage` < 0.70 (interpretability)
- `change_tracking_coverage` < 0.70 (CDC capability)
- `clustering_coverage` < 0.60 (performance)

### Lower Priority
- `search_optimization_coverage` (optional optimization)
- `dynamic_table_coverage` (nice-to-have)

## Presentation Tips

1. **Lead with overall score** — gives immediate context
2. **Highlight failures** — use ✗ or color to draw attention
3. **Show specific gaps** — "2 tables missing PKs" not just "pk_coverage: 0.80"
4. **Suggest next steps** — link to remediation
