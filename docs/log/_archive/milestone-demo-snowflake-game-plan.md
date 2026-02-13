# Milestone: Working demo against Snowflake (all factors, all test types)

**Goal:** A working demo against Snowflake with tests across **each of the six factors** and **all types of tests** (measured, question-based, file-based evidence), ready for tomorrow. Each factor must be **represented**; we do not have to complete every requirement per factor.

**Constraint:** You have a Snowflake account and Cortex Code CLI for testing. Demo runs as `aird assess -c "snowflake://..."` (or equivalent) and produces one report showing measured results + question-based results (and optionally file-based evidence).

---

## Test types to demonstrate

| Type | What it is | Demo deliverable |
|------|------------|------------------|
| **Measured** | SQL (or API) runs; result compared to threshold; pass/fail. | Clean suite (6 tests) on Snowflake + at least one measured test per factor 1–5 so report has a "result" row for each factor. |
| **Question-based** | Agent asks user a question; answer recorded; optional rubric → pass/fail. | Questions registry + survey step; at least one question per factor (6 total); report has `question_results` section. |
| **File-based** | User points to or uploads a file; agent reads and evaluates; answer/pass derived. | At least one question that `accepts_file`; file path handling + simple evaluator; evidence_source/evidence_ref in report. |

---

## Submilestones

### SM1: Snowflake platform — adapter, discovery, Clean suite

**Outcome:** Can run `aird assess -c "snowflake://..."` and get **Clean** factor measured results against a real Snowflake database.

**Tasks:**
1. **Adapter:** Add `agent/platform/snowflake_adapter.py`. Use `snowflake-connector-python` (already in optional deps). Parse connection string (e.g. `snowflake://user:pass@account/db/schema?warehouse=wh` or env); create connection; register with scheme `snowflake`, default_suite `common_snowflake`.
2. **Discovery:** Snowflake has `information_schema.tables` and `information_schema.columns` with standard column names. Reuse existing discovery path in `discovery.py` (no SQLite-style branch needed). If connection string encodes database/schema, ensure discovery scopes to them (or use current session defaults).
3. **Clean suite:** Add `agent/suites/clean_snowflake.py`. Same six requirement keys as DuckDB/SQLite. Snowflake SQL: double-quoted identifiers; use `TRY_CAST` (Snowflake supports it) or `TRY_TO_DOUBLE`/`TRY_TO_NUMBER` and `TRY_TO_DATE` where needed. Table count: `information_schema.tables` filtered by `table_catalog`, `table_schema` (current account/db/schema or from inventory). Register as `common_snowflake`.
4. **Registration:** In `agent/platform/__init__.py`, import snowflake adapter and clean_snowflake suite.
5. **Coverage:** Update `docs/coverage/README.md` with Snowflake + Clean.
6. **Verify:** Run assess against your Snowflake instance (Cortex Code CLI or local) and confirm Clean results appear.

**Acceptance:** Single-connection assess to Snowflake returns report with `results` containing Clean factor tests (table_discovery, null_rate, duplicate_rate, etc.) and correct pass/fail.

---

### SM2: One measured test per factor (1–5) so every factor appears in measured results

**Outcome:** Report `results` list includes at least one row for each of Contextual, Consumable, Current, Correlated, Compliant (so the demo shows "we ran a test" for every factor).

**Tasks:**
1. **Requirement keys:** Define one requirement key per factor for the demo (can be minimal):
   - **Contextual:** e.g. `column_comment_coverage` or `semantics_documented` — one test that queries Snowflake (e.g. count of columns with COMMENT, or placeholder `SELECT 1 AS v`).
   - **Consumable:** e.g. `serving_capability` — placeholder or simple query (e.g. role/session check).
   - **Current:** e.g. `freshness_metadata` — query `information_schema.tables` for `last_altered` or similar if available; or placeholder.
   - **Correlated:** e.g. `lineage_metadata` — placeholder or query for Snowflake objects that indicate lineage (e.g. streams/tasks); or `SELECT 1`.
   - **Compliant:** e.g. `access_control_metadata` — placeholder or query for grants/roles; or `SELECT 1`.
2. **Implement:** Add these tests to the Snowflake suite (or a small "demo" suite that runs after Clean). Each test: `factor`, `requirement`, `query` (fixed) or `query_template`, `target_type: platform`. Use trivial `SELECT 1 AS v` for any factor where we don’t have a real Snowflake query yet (so report still shows the factor).
3. **Thresholds:** Add placeholder thresholds in `agent/thresholds.py` for the new requirement keys (e.g. pass if v <= 1.0 so `SELECT 1` passes).
4. **Report:** No change needed; results already list factor/requirement per row. Summary can stay L1/L2/L3 roll-up across all tests.

**Acceptance:** Report `results` contains at least one entry for factor `contextual`, one for `consumable`, one for `current`, one for `correlated`, one for `compliant`. No need for real logic beyond "we ran something" for demo.

---

### SM3: Question-based flow — registry, survey step, report section

**Outcome:** Agent can run a "survey" of question-based requirements; answers are stored and reported in `question_results`. At least one question per factor (6 total).

**Tasks:**
1. **Questions registry:** Add `factors/questions.yaml` (or `agent/questions_registry.yaml`) with one entry per factor. Each entry: factor, requirement (key), question (text), optional rubric. Example keys: `freshness_sla_defined` (Current), `column_meaning_documented` (Contextual), `serving_latency_acceptable` (Consumable), `lineage_tooling` (Correlated), `governance_policy` (Compliant), plus one for Clean (e.g. `validation_at_ingestion`).
2. **Loader:** Add `agent/questions_loader.py` (or in pipeline): load YAML, return list of question defs; optional filter by workload.
3. **Survey step:** In pipeline (or a dedicated function callable from assess): after measured tests (or before), run "survey" — for each question in registry (or filtered by factor/workload), prompt user (or in demo, accept a pre-filled dict of answers for automation). Record answer per requirement. Output list of `{ factor, requirement, question_text, answer, l1_pass?, l2_pass? }` using rubric if present.
4. **Report:** Extend `build_report` to accept optional `question_results` list. Merge into report as `question_results`. Extend markdown reporter to render a "Question-based (survey)" section.
5. **Integration:** Pipeline: when running assess, after building report from measured results, if survey is enabled (e.g. `--survey` or always for demo), run survey step and merge question_results into report. For tomorrow, survey can be interactive (agent asks, user types) or CLI can accept a path to a pre-filled YAML of answers for a non-interactive demo.
6. **Demo:** Ensure at least 6 questions (one per factor) and that report shows them.

**Acceptance:** Report contains `question_results` with at least one entry per factor. Markdown output shows a "Question-based" section with question text and answer (and pass/fail if rubric applied).

---

### SM4: File-based evidence (one question)

**Outcome:** At least one question accepts file evidence; user can point to a file (e.g. governance policy); agent records evidence_source and evidence_ref and derived answer.

**Tasks:**
1. **Question def:** Add one question in the registry with `accepts_file: true`, `file_types: [pdf, md, txt]`, optional `file_evaluator: { type: "keyword_present", terms: ["governance", "policy"] }` or `agent_interprets`.
2. **File handling:** In survey step, when user provides a path (or upload): resolve path (allow current workspace or configured dir), read file with size limit (e.g. 1MB), run evaluator. Set evidence_source=`file_path`, evidence_ref=path, extracted_answer=result of evaluator or short summary.
3. **Report:** question_results entry includes evidence_source, evidence_ref, extracted_answer when file was used.
4. **Demo:** User points to a small policy doc or CSV; report shows that requirement answered from file.

**Acceptance:** One question-based result in the report has evidence_source `file_path` (or `file_upload`) and evidence_ref set; answer reflects file content (e.g. "pass" if keyword found).

---

### SM5: Demo runbook and E2E check

**Outcome:** Clear steps to run the demo with Cortex Code CLI and Snowflake; one command (or short sequence) produces the full report with all factors and all test types.

**Tasks:**
1. **Runbook:** Add `docs/demo-snowflake.md` (or section in E2E/README): connection string format for Snowflake, env vars if needed, `pip install -e ".[snowflake]"`, `aird assess -c "snowflake://..."` (or from manifest). Optional: how to run survey (interactive vs pre-filled YAML). How to point to a file for the file-based question.
2. **Cortex Code CLI:** Note any Cortex-specific steps (e.g. how connection string is passed, how to upload or point to a file if needed).
3. **Sanity check:** Run full flow once: Snowflake connection → discover → run measured tests (Clean + 5 factor placeholders) → run survey (6 questions + 1 file if time) → build report → output markdown. Confirm no crashes and report has all sections.

**Acceptance:** A person with Snowflake credentials and Cortex Code CLI can follow the runbook and produce a single report that shows: Clean measured tests, one measured test per factor 1–5, question_results for all 6 factors, and at least one file-based evidence entry (if SM4 done).

---

## Order of execution (recommended)

| Order | Submilestone | Dependency |
|-------|--------------|------------|
| 1 | **SM1** Snowflake platform + Clean | None. Do first so you have a working Snowflake assess. |
| 2 | **SM2** One measured test per factor 1–5 | SM1 (Snowflake suite exists). |
| 3 | **SM3** Question-based flow (registry, survey, report) | None for registry/report; survey can run after measured tests. |
| 4 | **SM4** File-based evidence | SM3 (survey step exists). |
| 5 | **SM5** Demo runbook + E2E | SM1–SM4 (or SM1–SM3 if SM4 is stretch). |

**If time is short:** Do SM1 → SM2 → SM3 → SM5 so the demo has measured tests for all factors and question-based for all factors; defer SM4 (file-based) to "if time" or a follow-up.

---

## Out of scope for this milestone

- Full requirement coverage per factor (only "each factor represented").
- Remediation linkage or interpret step beyond what’s already there.
- Parallel execution or performance tuning.
- Multiple Snowflake databases/schemas in one run (single connection is enough for demo).

---

## Checklist (quick reference)

- [ ] SM1: Snowflake adapter, discovery, Clean suite, registered, docs/coverage updated.
- [ ] SM2: One measured test per factor 1–5 in Snowflake suite (or demo suite); thresholds added.
- [ ] SM3: questions registry (YAML), loader, survey step, report question_results + markdown section.
- [ ] SM4: One question accepts_file; file path read + evaluator; evidence_source/evidence_ref in report.
- [ ] SM5: docs/demo-snowflake.md (or runbook); E2E sanity run.
