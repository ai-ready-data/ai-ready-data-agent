---
name: interview
description: "Structured questions in three phases: pre-connect, post-discover, post-results. Gather context and triage decisions."
parent_skill: assess-data
---

# Interview (Context and Triage)

Three phases of structured questions so the agent can tailor the assessment and interpretation. Use progressive disclosure: ask 1–2 questions at a time and expand based on answers so the user isn't overwhelmed.

## Forbidden Actions

- NEVER store or log credentials
- NEVER skip a STOP when the playbook says wait for user response
- NEVER invent user answers; use only what the user explicitly provided

## When to Load

- **Phase 1:** Before connecting; user is starting a first-time or new assessment. Load for "Gather Context" (Step 1).
- **Phase 2:** After discovery; before running tests. Load for "Confirm Scope" (Step 3).
- **Phase 3:** After results; before generating fixes. Load for "Failure Triage" (Step 5 / interpret).

## Phase 1: Pre-Assessment (before connecting)

Ask in order of priority. Use progressive disclosure.

1. **Platform (first):** "What database platform are you using? (e.g. DuckDB, SQLite, Snowflake.)" This determines which driver to install and which test suite to use. For first-time setup, `aird init` can guide you through this interactively.

2. **Target workload:** "What are you building toward: analytics dashboards (L1), RAG/search (L2), or model training (L3)?" Drives which threshold level to emphasize and how to prioritize failures. Maps to the `--workload` flag: `--workload analytics` (L1), `--workload rag` (L2), `--workload training` (L3).

3. **Scope:** "Are there schemas we should skip? (e.g. staging, scratch, test.)" Informs scope; can be passed as `--schema` or exclusions when supported.

4. **Infrastructure:** "Do you use dbt, a data catalog, OpenTelemetry, or Iceberg?" Helps explain what can or can't be assessed.

5. **Governance:** "Do you have PII classification? Which columns are sensitive?" Relevant for Compliant factor when implemented.

6. **Pain points:** "What prompted this assessment? Any known issues?" Helps validate that the assessment catches what matters.

**Tip:** `aird assess -i` (interactive mode) provides a guided flow that handles scope selection and workload choice interactively, so some of these questions may be answered during the assessment itself.

**STOP:** Wait for user responses before proceeding to connect.

## Phase 2: Post-Discovery (after connecting, before testing)

After running `aird discover`, present the summary (schemas, table counts) and ask:

1. **Scope:** "I found N tables across M schemas. Assess all, or exclude any?"
2. **Criticality:** "Which tables are most critical for your AI workload?" (Optional; helps prioritize in interpretation.)
3. **Nullable by design:** "Are there columns where nulls are expected?" (Optional; can inform threshold overrides when supported.)

**Note:** In interactive mode (`aird assess -i`), scope selection is handled with checkbox prompts — the user can browse discovered tables and select which to include.

**STOP:** Confirm scope before running the assessment.

## Phase 3: Post-Results (after testing, before suggesting fixes)

After presenting the report and walking through failures:

1. For each failure (or group): "Is this expected? Do you want a fix suggestion?"
2. "Should any of these be excluded from future runs?" (When context supports it.)
3. "Which failures should I generate remediation for?"

**STOP:** Get decisions before generating remediation in [remediate/SKILL.md](../remediate/SKILL.md).

## Output

- Phase 1: Goals, scope hints, context for interpretation
- Phase 2: Confirmed scope and exclusions
- Phase 3: List of failures to fix vs accept; ready for remediate skill
