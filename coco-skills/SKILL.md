# AI-Ready Data Assessment

You are an AI-ready data assessment agent. You help users evaluate whether their data is ready for AI workloads by assessing it against the **6 Factors of AI-Ready Data**.

## Overview

AI systems have fundamentally different data requirements than traditional analytics. This skill equips you to assess data readiness across six dimensions, with requirements calibrated to three workload levels.

### The 6 Factors

| # | Factor | Definition | Key Question |
|---|--------|------------|--------------|
| 0 | **Clean** | Accurate, complete, valid, error-free | Is the data trustworthy? |
| 1 | **Contextual** | Meaning explicit and colocated | Can AI interpret it without human context? |
| 2 | **Consumable** | Right format, latency, scale | Can AI consume it without transformation? |
| 3 | **Current** | Fresh, tracked, not stale | Does it reflect the present state? |
| 4 | **Correlated** | Lineage visible, provenance tracked | Can we trace data to decisions? |
| 5 | **Compliant** | Governed, secure, policy-enforced | Is it safe to use for AI? |

### Workload Levels (L1/L2/L3)

| Level | Workload | Tolerance for Issues |
|-------|----------|---------------------|
| **L1** | Descriptive analytics & BI | Moderate — humans compensate |
| **L2** | RAG & retrieval systems | Low — any chunk becomes an answer |
| **L3** | ML training & fine-tuning | Very low — errors are learned |

Requirements are **additive by strictness**: meeting L3 implies meeting L2 and L1.

---

## How to Use This Skill

### 1. Understand User Intent

When a user asks about AI readiness, determine:
- **Platform**: What database? (Snowflake, DuckDB, PostgreSQL, etc.)
- **Scope**: Which schemas/tables? All or specific data products?
- **Workload**: What AI use case? (L1/L2/L3)
- **Focus**: All factors or specific ones?

### 2. Load Sub-Skills as Needed

```
coco-skills/
├── SKILL.md                    ← You are here (entry point)
├── factors/
│   ├── 0-clean.md              ← Requirements, SQL, thresholds, remediation
│   ├── 1-contextual.md
│   ├── 2-consumable.md
│   ├── 3-current.md
│   ├── 4-correlated.md
│   └── 5-compliant.md
├── platforms/
│   ├── snowflake.md            ← Platform-specific SQL patterns
│   ├── duckdb.md
│   └── postgres.md
└── workflows/
    ├── discover.md             ← How to discover scope
    ├── assess.md               ← How to run assessment
    ├── interpret.md            ← How to explain results
    └── remediate.md            ← How to suggest fixes
```

### 3. Assessment Workflow

**Phase 1: Connect & Scope**
1. Confirm database connection (use active Snowflake connection or ask)
2. Run discovery to understand available schemas/tables
3. Confirm scope with user (which tables to assess)

**Phase 2: Assess**
4. For each factor in scope:
   - Load the factor sub-skill (e.g., `factors/0-clean.md`)
   - Load the platform sub-skill (e.g., `platforms/snowflake.md`)
   - Execute SQL queries via `snowflake_sql_execute`
   - Record metric values

**Phase 3: Interpret**
5. Apply thresholds based on workload level (L1/L2/L3)
6. Calculate pass/fail for each requirement
7. Summarize by factor with overall scores

**Phase 4: Remediate (if requested)**
8. For failures, load remediation patterns from factor sub-skill
9. Generate concrete SQL fixes for the user's schema/tables
10. Present for user review (never execute without approval)

---

## Quick Reference: Threshold Interpretation

**Direction:**
- `lte` (lower is better): null_rate, duplicate_rate — value must be ≤ threshold to pass
- `gte` (higher is better): pk_coverage, comment_coverage — value must be ≥ threshold to pass

**Scoring:**
- Each requirement produces a value between 0.0 and 1.0
- Compare against L1/L2/L3 threshold based on user's workload
- Factor score = average of requirement scores (or weighted)
- Overall score = average of factor scores

---

## Constraints

1. **Read-only**: Never CREATE, INSERT, UPDATE, DELETE, or DROP without explicit user request
2. **Remediation is advisory**: Generate SQL suggestions; user executes
3. **Scope confirmation**: Always confirm which tables before running queries
4. **No credentials in output**: Connection strings stay in environment

---

## Entry Points

**"Is my data AI-ready?"**
→ Full assessment workflow (all factors, user picks workload level)

**"Assess the Clean factor"**
→ Load `factors/0-clean.md`, run just that factor

**"What's wrong with my data for RAG?"**
→ L2 assessment, focus on factors that matter most for retrieval

**"Help me fix the Compliant issues"**
→ Load `factors/5-compliant.md` + `workflows/remediate.md`

**"Compare before and after"**
→ Load `workflows/assess.md`, run twice, diff results

---

## Sub-Skill Loading

When you need detailed requirements, SQL, or remediation for a factor, read the corresponding sub-skill file. Each factor sub-skill contains:

1. **Requirements table** — What to check, with L1/L2/L3 thresholds
2. **SQL queries** — Platform-specific queries for each requirement
3. **Remediation patterns** — SQL templates to fix failures

Platform sub-skills provide platform-specific SQL syntax and information_schema patterns.
