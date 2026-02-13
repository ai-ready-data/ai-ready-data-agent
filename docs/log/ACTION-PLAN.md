# Action Plan: AI-Ready Data Framework

**Created:** 2026-02-12  
**Status:** Active  

---

## 1. North Star: What This Needs to Become a Standard

For this to become a standard, it must:

1. **Solve an urgent problem** teams face *right now* (not aspirational)
2. **Take less time to run than it saves** (ROI must be immediate)
3. **Produce actionable outputs** (not just a report card)
4. **Integrate into existing workflows** (CI/CD, dbt, orchestration)
5. **Have a killer demo** (5 minutes to "wow, I need this")

**Strategic choice:** This is a **tool people run** (like dbt), not just a framework people reference (like 12-Factor App). The tool embodies and enforces the framework.

---

## 2. Primary User and Positioning

**Primary user (Persona 0):** The data engineer who owns the Snowflake warehouse. See §4 for full profile.

**Implications:**
- Integrate with dbt (profiles, tests, schema.yml)
- Run in CI/CD pipelines
- Fit into existing data quality and pipeline workflows
- Output formats that data engineers can act on

---

## 3. Validation Milestones

### Minimal Viable Signal (30 days)
- [ ] 5 teams run this on real data (not samples)
- [ ] 3 teams learn something they didn't know (discovery)
- [ ] 1 team fixes something as a result (action)

### Stronger Signal (90 days)
- [ ] 1 team prevents a failure ("We were about to launch, ran this, found issues, fixed them")
- [ ] 1 team uses it in their workflow (runs it regularly, not just once)

### Proof of Concept (6 months)
- [ ] 1 team shows before/after metrics ("RAG precision improved from 60% to 78% after fixing Contextual issues")
- [ ] Someone else builds on the framework (extends, integrates, references in their tool)

---

## 4. Persona 0: Data Engineer on Snowflake

**Decision:** Focus exclusively on one persona for the killer demo. No generic "data engineer" — we target **the Snowflake data engineer** who owns tables feeding RAG, analytics, or ML.

**Persona 0 profile:**
- **Role:** Data engineer (or analytics engineer) who owns a Snowflake warehouse
- **Stack:** Snowflake + dbt (or similar); tables feed BI, RAG, or ML pipelines
- **Pain:** "Is this dataset ready for AI?" — no checklist, no thresholds, no remediation path
- **Context:** May have dbt tests for data quality, but nothing scoped to AI workload levels (L1/L2/L3)
- **Success:** Runs `aird assess`, gets a report, runs `aird fix --dry-run`, gets actionable SQL/dbt suggestions

**Implication:** All demo content, docs, and validation targets this persona. Other platforms (DuckDB, SQLite) remain supported but are not the demo focus.

---

## 5. Why Teams Fail (and How We Fix It)

| Hypothesis | Their failure | Our fix |
|------------|---------------|---------|
| **1. Don't know what to check** | No checklist; miss critical factors (e.g., temporal scope) | Comprehensive test suites |
| **2. Know but don't check** | "We'll clean it up later" (they never do) | Make it fast/easy to run |
| **3. Check but can't interpret** | See 1000 nulls — acceptable or catastrophic? | L1/L2/L3 thresholds provide interpretation |
| **4. Interpret but can't fix** | Remediation seems overwhelming | Remediation guidance + scripts (our weakest link → **prioritize**) |

---

## 6. Killer Demo: 5-Minute Flow (Persona 0)

**Goal:** A Data Engineer on Snowflake sees the full loop in 5 minutes: assess → interpret → fix.

| Step | Time | Action | Aha moment |
|------|------|--------|------------|
| 1 | 0:00 | "You have tables feeding a RAG app. Is it ready?" | Sets stakes |
| 2 | 0:30 | `aird init` (or `-c snowflake://...`) → connect | Zero config friction |
| 3 | 1:00 | `aird assess -c snowflake://... -s analytics -o markdown` | Report in seconds: L1/L2/L3 scores, factor breakdown |
| 4 | 2:30 | Walk report: "Clean 72%, Contextual 45% — primary keys missing on 12 tables" | **Interpretation:** They see *what* failed and *why* it matters for RAG |
| 5 | 3:30 | `aird fix --dry-run` | **Actionable output:** SQL and dbt-ready suggestions, not just "fix it" |
| 6 | 4:30 | "Run these, re-assess with `--compare`" | **Closure:** Clear path from problem → fix → verify |

**Aha moment:** "I didn't know 12 tables had no primary keys — and here's the SQL to fix it." The tool answers *what to check*, *how to interpret*, and *how to fix* in one flow.

**Deliverables:**
- [ ] Demo script (runbook) for Persona 0: [demo-snowflake.md](demo-snowflake.md)
- [ ] Snowflake-first: Clean + Contextual suites polished; fix templates for Snowflake (primary_key, FK, temporal)
- [ ] 5-min video or live demo path documented

---

*Next: Update roadmap.md to reflect these priorities and create specific implementation tasks.*
