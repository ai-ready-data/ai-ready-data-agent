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

**Primary user (Persona 0):** The data engineer who owns the Snowflake warehouse. See §10 for full profile.

**Implications:**
- Integrate with dbt (profiles, tests, schema.yml)
- Run in CI/CD pipelines
- Fit into existing data quality and pipeline workflows
- Output formats that data engineers can act on

---

## 3. Shared Vocabulary

**Outcome vocabulary:** "Production AI Ready: Yes / No (Threshold)"

- Simple enough for stakeholders
- Technical practitioners still get the six factors and L1/L2/L3 thresholds
- Surface the binary outcome; keep the detail available for those who need it

---

## 4. Validation Milestones

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

## 5. CLI Simplification

**Current state:** 12 commands (`assess, discover, run, report, save, history, diff, suites, init, compare, rerun, benchmark`)

**Stress test:** When would you ever *not* want discover → run → report → save together? Most users will just run `aird assess`.

**Target:** 4–5 core commands that 80% of users need.

| Command | Purpose |
|---------|---------|
| `aird init` | Setup (interactive wizard) |
| `aird assess` | The main thing (full pipeline) |
| `aird history` | What did I run before |
| `aird diff` | How did it change |
| `aird fix --dry-run` | Generate remediation scripts (new) |

**Defer or deprecate:** `discover`, `run`, `report`, `save` as separate commands — keep for power users/composability but don't surface as primary. `suites`, `compare`, `rerun`, `benchmark` — evaluate which are essential vs. secondary.

**Status:** Implemented (2026-02-13). Primary commands first in help; `fix` added with `--dry-run` and `-o <dir>`.

---

## 6. Data Products: Keep It Loose

**Decision:** Keep the data product concept flexible.

- Support pointing at a **single table** or a **whole data product**
- Don't assume organizations already organize data as products
- Framework should work whether or not they have formal data products
- Avoid pushing away users who don't have data mesh maturity

---

## 7. Build Use Case at a Time

**Decision:** Don't narrow to RAG-only, but **build requirements use case by use case**.

- Start with the use case that has the clearest ROI
- Deep integration per use case (e.g., RAG → vector DBs, embedding pipelines)
- Avoid trying to be everything at once
- Each use case gets full treatment: assessment + remediation guidance

---

## 8. Solve the Remediation Gap (Critical)

**Problem:** Read-only is safer, but creates a gap. Users see "23 tables have no primary keys" and don't know what to do.

**Bridge it with actionable outputs:**

| Instead of | Provide |
|------------|---------|
| "23 tables have no primary keys" | "23 tables have no primary keys. Run this dbt macro: `{{ generate_pk('customers', ['email', 'signup_date']) }}`" |
| Report card only | "Export to dbt test suite" → writes `schema.yml` files |
| Generic guidance | Platform-specific remediation (dbt macros, SQL scripts, DBT tests) |

**Actions:**
- [ ] Add `aird fix --dry-run` to generate remediation scripts
- [ ] Integrate "Export to dbt test suite" that writes schema.yml
- [ ] Per-requirement remediation templates (see `factors-staging/agent/remediation/`)
- [ ] Remediation is step 1 of an automated cleanup; assessment is the trigger

---

## 9. Why Teams Fail (and How We Fix It)

| Hypothesis | Their failure | Our fix |
|------------|---------------|---------|
| **1. Don't know what to check** | No checklist; miss critical factors (e.g., temporal scope) | Comprehensive test suites |
| **2. Know but don't check** | "We'll clean it up later" (they never do) | Make it fast/easy to run |
| **3. Check but can't interpret** | See 1000 nulls — acceptable or catastrophic? | L1/L2/L3 thresholds provide interpretation |
| **4. Interpret but can't fix** | Remediation seems overwhelming | Remediation guidance + scripts (our weakest link → **prioritize**) |

---

## 10. Persona 0: Data Engineer on Snowflake

**Decision:** Focus exclusively on one persona for the killer demo. No generic "data engineer" — we target **the Snowflake data engineer** who owns tables feeding RAG, analytics, or ML.

**Persona 0 profile:**
- **Role:** Data engineer (or analytics engineer) who owns a Snowflake warehouse
- **Stack:** Snowflake + dbt (or similar); tables feed BI, RAG, or ML pipelines
- **Pain:** "Is this dataset ready for AI?" — no checklist, no thresholds, no remediation path
- **Context:** May have dbt tests for data quality, but nothing scoped to AI workload levels (L1/L2/L3)
- **Success:** Runs `aird assess`, gets a report, runs `aird fix --dry-run`, gets actionable SQL/dbt suggestions

**Implication:** All demo content, docs, and validation targets this persona. Other platforms (DuckDB, SQLite) remain supported but are not the demo focus.

---

## 11. Killer Demo: 5-Minute Flow (Persona 0)

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

## 12. One Person vs. Team Use

**Decision:** Start with **one person** — single-run workflow (assess, share report). Team use (CI/CD, history sharing, multi-user) is **out of scope for now**. See [roadmap.md](roadmap.md).

---

## 13. Summary: Immediate Priorities

1. **Persona 0 focus** — All demo and validation targets the Snowflake data engineer
2. **Killer demo** — 5-minute flow: assess → interpret → fix; aha = "I didn't know X — and here's the fix"
3. **Remediation-first** — `aird fix --dry-run` + Snowflake-specific templates (primary_key, FK, temporal). Specs: [plan-remediation-snowflake-templates.md](plan-remediation-snowflake-templates.md), [plan-dbt-integration.md](plan-dbt-integration.md)
4. **CLI simplification** — Primary commands: init, assess, history, diff, fix ✓
5. **Data engineer + dbt** — Deep integration (profiles, schema.yml, CI/CD)
6. **Validation** — 5 Snowflake teams on real data in 30 days; 1 fixes something

---

*Next: Update roadmap.md to reflect these priorities and create specific implementation tasks.*
