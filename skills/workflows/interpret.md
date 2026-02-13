# Workflow: Interpret

Guide for interpreting assessment results, presenting findings, and triaging failures.

## Purpose

Transform raw metric values into actionable insights:
1. Apply thresholds based on workload level
2. Determine pass/fail status
3. Calculate factor and overall scores
4. Prioritize findings
5. Triage failures with the user

## Threshold Application

### Direction Rules
- **`lte`** (lower is better): Value ≤ threshold = PASS
- **`gte`** (higher is better): Value ≥ threshold = PASS

See [../factors/README.md](../factors/README.md) for the full threshold reference table.

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

## Presentation

### Step 1: Lead with Target Workload

If the user stated a target workload (L1, L2, or L3), start there:

> "Your data scores **X%** for L2 (RAG) readiness across N tests."

If no target workload was specified, show all three levels:

> "Across N tests: L1 (Analytics) X%, L2 (RAG) Y%, L3 (Training) Z%."

### Step 2: Factor-by-Factor Walkthrough

For each factor with results:

1. **Name and summary** — e.g. "Clean: 8/10 pass at L2 (80%)"
2. **Highlight failures** at the target level. For each failing test, show:
   - Requirement key (e.g. `null_rate`)
   - Measured value vs threshold (e.g. "measured 0.15, threshold 0.05 for L2")
   - Direction (lte = "should be at most", gte = "should be at least")
3. **Passing tests** — mention briefly or skip if all pass

### Step 3: Summary Table

```
## AI-Ready Data Assessment Results

**Schema:** {database}.{schema}
**Workload Level:** L{level}
**Overall Score:** {score}% ({pass_count}/{total_count} requirements passed)

| Factor | Score | Status |
|--------|-------|--------|
| Clean | 85% | Pass |
| Contextual | 60% | Fail |
| Consumable | 90% | Pass |
| Current | 40% | Fail |
| Correlated | 30% | Fail |
| Compliant | 70% | Pass |
```

---

## Failure Triage (Post-Results)

After presenting the report, triage failures with the user:

1. For each failure (or group): "Is this expected? Do you want a fix suggestion?"
2. "Should any of these be excluded from future runs?"
3. "Which failures should I generate remediation for?"

**STOP:** Get decisions before generating remediation in [remediate.md](remediate.md).

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

## Output

- User understands scores and failures at their target level
- User has decided which failures to fix vs accept
- Ready to proceed to [remediate.md](remediate.md) for fix suggestions
