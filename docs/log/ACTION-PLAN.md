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

**Strategic choice:** This is both a **framework people reference** (like 12-Factor App) and a **knowledge base agents execute** (like dbt). The portable skills embody the framework; the CLI (in the ai-ready-data-cli repo) automates it.

---

## 2. Primary User and Positioning

**Primary user (Persona 0):** The data engineer who owns the Snowflake warehouse. See §4 for full profile.

**Implications:**
- Factor skills must include Snowflake-specific SQL patterns
- Remediation patterns must be concrete and actionable (not generic advice)
- Skills must work with any agent runtime (Cursor, Claude Code, Cortex Code)
- Framework must integrate with existing data quality workflows

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

**Focus exclusively on one persona for the killer demo.** We target **the Snowflake data engineer** who owns tables feeding RAG, analytics, or ML.

**Persona 0 profile:**
- **Role:** Data engineer (or analytics engineer) who owns a Snowflake warehouse
- **Stack:** Snowflake + dbt (or similar); tables feed BI, RAG, or ML pipelines
- **Pain:** "Is this dataset ready for AI?" — no checklist, no thresholds, no remediation path
- **Context:** May have dbt tests for data quality, but nothing scoped to AI workload levels (L1/L2/L3)
- **Success:** Runs assessment (via any agent), gets factor scores, gets actionable remediation SQL

**Implication:** All demo content, docs, and validation targets this persona. Other platforms remain supported but are not the demo focus.

---

## 5. Why Teams Fail (and How We Fix It)

| Hypothesis | Their failure | Our fix |
|------------|---------------|---------|
| **1. Don't know what to check** | No checklist; miss critical factors (e.g., temporal scope) | Comprehensive factor skills with assessment SQL |
| **2. Know but don't check** | "We'll clean it up later" (they never do) | Make it easy — any agent can run the checks |
| **3. Check but can't interpret** | See 1000 nulls — acceptable or catastrophic? | L1/L2/L3 thresholds provide interpretation |
| **4. Interpret but can't fix** | Remediation seems overwhelming | Remediation patterns + SQL in every factor skill |

---

## 6. Repo Architecture

This repo contains the **framework and portable skills** (Layer 1 + Layer 2). The **CLI tool** (Layer 3) lives in [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli).

The skills are designed so any agent (Cursor, Claude Code, Cortex Code, or custom) can assess data without installing the CLI. The CLI automates the workflow but is not required.
