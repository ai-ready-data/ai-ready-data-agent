# Design: Question-based requirements

**Date:** 2026-02-10

**Status:** Design; implementation to follow.

---

## 1. Rationale

Today, requirements are evaluated only by **measured tests**: the agent runs SQL (or platform API) and compares a result to a threshold. That covers what can be queried—null rates, duplicate rates, schema shape—but not:

- Process and governance: "Is there a defined SLA for data freshness?" "Who owns this dataset?"
- Organizational: "Is there a data dictionary or catalog?" "Are column meanings documented?"
- Capability and intent: "Do you run validation at ingestion?" "Is PII classified?"
- Subjective or context-dependent: "Are these nulls acceptable for this column?" "Which tables are critical for your RAG use case?"

Introducing **question-based requirements** lets the framework cover a much wider range of what "must be true" for AI-readiness: the agent **asks the user** a question tied to a requirement key, records the answer, and optionally scores it (e.g. pass/fail from a rubric or free-form for later interpretation). Same factor/requirement model, same report and history; different evaluation mechanism.

---

## 2. Concept

- **Requirement key** is unchanged: each requirement has a stable key (e.g. `null_rate`, `freshness_sla_defined`). A requirement can be:
  - **Measured:** Evaluated by a test (query or API); result is a measured value and threshold comparison.
  - **Asked:** Evaluated by the agent asking the user a question; result is the user's answer and optionally a derived pass/fail or category.
- **Factor docs** can list both. For "asked" requirements, the factor doc (or a linked questions registry) provides the **question text** (or template) and optionally **how to interpret** the answer (e.g. yes/no → pass/fail; free text → no automatic pass/fail, but included in report).
- **Report** includes both measured results and question-based results so the full picture is in one place (e.g. a `question_results` or `survey` section: factor, requirement key, question, answer, optional pass/fail).
- **Interview skill** (or a dedicated "survey" step) is responsible for asking question-based requirements, collecting answers, and passing them into the report. The agent does not invent answers; it only records what the user said.

**Evidence from files:** The user may **upload** or **point the agent at** a file to answer a requirement—e.g. a governance policy PDF, a CSV of data-ownership mappings, or a data-dictionary export. The agent reads the file (when the user provides a path or uploads it), optionally evaluates it (e.g. "does this doc mention SLAs?", "does this CSV have column X?"), and records the result as the "answer" for that requirement. So the **evidence source** for a question-based result can be: (1) user's verbal/text answer, (2) a file path the user pointed to, or (3) uploaded file content. The report stores both the evidence source/ref and the derived answer or pass/fail so the assessment is auditable.

This adds a large range of assessable items without new platform adapters or SQL: governance, process, documentation, and intent can all be captured as question-based requirements under the same factors (Clean, Contextual, Consumable, Current, Correlated, Compliant).

---

## 3. Scope

**In scope:**

- Extend the **factor spec** so a requirement can be marked as **measured** vs **asked** (or we maintain a separate "questions" registry keyed by factor + requirement).
- Define a **question definition** shape: requirement key, factor, question text (or template), optional workload (L1/L2/L3), optional rubric for pass/fail (e.g. "yes → pass", or "one of [a,b,c] → pass").
- **Report shape:** Add a section (e.g. `question_results`) with one entry per asked requirement: factor, requirement, question_text, answer (string or structured), optional l1_pass/l2_pass/l3_pass when rubric applies. When evidence comes from a file: **evidence_source** (e.g. `user_statement`, `file_path`, `file_upload`), **evidence_ref** (path or upload id), and optional **extracted_answer** or summary derived from the file.
- **File-based evidence:** User can provide a **path** to a file (e.g. in workspace or absolute) or **upload** a file. The agent reads the file and optionally runs an **evaluator** (e.g. keyword presence, CSV schema check, or free-form interpretation) to derive an answer or pass/fail. Question definitions can declare that they **accept_file** and optionally which **file_types** (e.g. pdf, csv, md) and **file_evaluator** hint (how to interpret the file).
- **Agent flow:** Interview (or survey phase) asks questions; for each, the user may answer in chat or provide a file. When a file is provided, the agent loads it (within safety limits), applies the evaluator if defined, and records evidence_source, evidence_ref, and derived answer. Answers are merged into the report.
- **Persistence:** Question answers (and evidence_ref when file-based) are part of the same assessment report. Stored file content or large excerpts are not required in the report; a ref (path or stable upload id) plus extracted answer is sufficient for audit. Optionally store a short hash or snippet for diff.

**Out of scope for this design:**

- Automatic scoring of free-text answers (NLP). Rubrics are simple (e.g. yes/no, choice from list).
- Mandatory vs optional questions (all can be optional initially; agent asks what's relevant to workload and scope).
- Multi-language question text (single language for v0).
- Full NLP or ML on file contents (evaluators are simple: keywords, schema, or agent summarization within context limits).

---

## 4. Question definition shape (proposed)

Each question-based requirement has:

| Field | Required | Description |
|-------|----------|-------------|
| **factor** | Yes | Factor name or index (e.g. `clean`, `contextual`). |
| **requirement** | Yes | Requirement key (e.g. `freshness_sla_defined`, `data_ownership_documented`). |
| **question** | Yes | Question text to ask the user (or template with placeholders). |
| **workload** | No | L1, L2, L3, or all; when set, only ask when user's target workload matches. |
| **rubric** | No | How to derive pass/fail from answer: e.g. `{ "type": "yes_no", "pass_if": "yes" }` or `{ "type": "choice", "pass_if": ["a","b"] }`. If absent, no automatic pass/fail; answer is still stored. |
| **accepts_file** | No | If true, the user may answer by providing a file path or upload. Agent will read the file and derive an answer (see file_evaluator). |
| **file_types** | No | When accepts_file is true, allowed types (e.g. `["pdf", "csv", "md", "txt"]`) for hinting or validation. |
| **file_evaluator** | No | When accepts_file is true, how to interpret the file: e.g. `{ "type": "keyword_present", "terms": ["SLA", "freshness"] }`, `{ "type": "csv_has_columns", "columns": ["owner", "dataset"] }`, or `{ "type": "agent_interprets" }` (agent summarizes or answers the question from content). Enables consistent pass/fail from file content when desired. |

**Where questions live:** Either (a) in the factor doc under a new "Question-based requirements" section (question text + key), or (b) in a separate file (e.g. `factors/questions.yaml` or per-factor `factor-00-clean-questions.yaml`) keyed by factor and requirement. Option (b) keeps factor docs stable and allows many questions without cluttering the doc; option (a) keeps everything in one place. Recommendation: **factor doc** can list the requirement key and a short question label; **full question text, rubric, and file acceptance** in a shared registry (YAML/JSON) so the agent and report builder can load them by key.

---

## 5. Report and flow

- **Report** shape extends to:
  - **question_results:** List of entries. Each entry: `factor`, `requirement`, `question_text`, `answer` (string or structured—the derived or user-stated answer). Optional: `l1_pass`, `l2_pass`, `l3_pass` when rubric or file_evaluator applies. When evidence is from a file: **evidence_source** (`user_statement` | `file_path` | `file_upload`), **evidence_ref** (path or upload id; no secrets, path may be redacted for storage if needed), and optionally **extracted_answer** (short summary or key finding from the file). Omitted when no question-based requirements were asked or user skipped.
- **Summary** can optionally roll up question-based pass/fail (e.g. "X of Y question-based requirements pass") when rubric or evaluator is present; otherwise treat as informational.
- **Flow:** During assess, after discovery (or after measured tests), the agent runs the "survey" step: for each question-based requirement applicable to the workload, ask the user (e.g. "Do you have a governance policy? You can answer here or point me to a file (e.g. PDF, CSV)."). If the user provides a path or uploads a file, the agent reads it (within size/type limits), runs the question's file_evaluator if defined (e.g. keyword check, CSV columns, or interpret), and records evidence_source, evidence_ref, and derived answer. If the user answers in chat, record as user_statement. Merge all into the same report object that already has `results` (measured) and `summary`. No separate "survey report"; one assessment, one report, two kinds of evidence (measured + question-based), with question-based supporting both text and file evidence.

---

## 6. Relationship to existing artifacts

- **Factor spec:** Add a subsection: "Requirement evaluation: measured vs asked." A requirement key may have a test (measured), a question (asked), or both. Same key, same factor, same L1/L2/L3 semantics.
- **Interview skill:** Phase 1 or a new "Survey" phase can be driven by the question registry: "I have N question-based requirements for this factor/workload; I'll ask them and record your answers."
- **Coverage doc:** docs/coverage can note which requirement keys are measured (with a suite) vs asked (with a question), so contributors know how to add either.
- **Remediation:** Failed question-based requirements (when rubric says fail) can link to the same remediation templates by requirement key; the agent can suggest "you said X; for this requirement we recommend Y."

---

## 7. Example question-based requirements (illustrative)

| Factor | Requirement key | Question (short) | Accepts file? |
|--------|------------------|------------------|---------------|
| Current | freshness_sla_defined | Is there a defined SLA or target for how fresh this data must be? | Optional: point to policy doc |
| Contextual | column_meaning_documented | Are column meanings or business definitions documented (e.g. in a catalog or wiki)? | Yes: CSV or doc |
| Compliant | pii_classification | Is PII identified and classified for this dataset? | Optional: point to classification export |
| Compliant | governance_policy | Do you have a data governance or usage policy? | Yes: PDF or doc |
| Correlated | lineage_tooling | Do you use lineage or data lineage tooling (e.g. OpenLineage, catalog lineage)? | No (verbal) |
| Clean | validation_at_ingestion | Is there validation (e.g. schema or quality checks) at ingestion? | No (verbal) |

For "Accepts file?" entries, the user can answer in chat or provide a path/upload; the agent reads the file and uses the question's file_evaluator (e.g. keyword check for "SLA", CSV column check for data dictionary) to derive an answer and optional pass/fail.

These do not replace measured requirements; they complement them. A factor can have both measured and question-based requirements under the same requirement key (e.g. measure null_rate and also ask "Are nulls in column X acceptable by design?").

---

## 8. File-based evidence: safety and scope

- **Scope of access:** The agent only reads files the user explicitly provides (path in workspace or allowed dir, or upload). No arbitrary filesystem discovery. Paths may be validated against an allow-list (e.g. current workspace, or a configured "evidence paths" list) to avoid reading sensitive locations.
- **Upload limits:** If uploads are supported, enforce max file size and allowed types (e.g. from question's `file_types`). Reject or truncate beyond limit; do not store full file content in the report by default—store evidence_ref (e.g. upload id or path) and extracted answer only. Optionally keep a small excerpt or hash for diff.
- **Evaluators:** Implement a small set of evaluator types (e.g. `keyword_present`, `csv_has_columns`, `agent_interprets`) so that file-based answers can be scored consistently. For `agent_interprets`, the agent uses the file content in context to answer the question or fill a rubric; output is still recorded as the requirement's answer and optional pass/fail.

---

## 9. Implementation notes (later)

- Add a **questions registry** (e.g. YAML per factor or one file) and a loader; include `accepts_file`, `file_types`, `file_evaluator` where applicable. Interview/survey step reads it and asks by workload.
- **File handling:** When user provides a path or upload, resolve path (with allow-list), read content (with size limit), and run the question's file_evaluator. Map evaluator output to `answer` and optional pass/fail; set evidence_source and evidence_ref in the result.
- Report builder accepts an optional `question_results` list and merges it into the report; markdown renderer outputs a "Question-based" or "Survey" section and, for file-based entries, shows evidence_source and evidence_ref (e.g. "Answer derived from: governance_policy.pdf").
- Storage: report JSON already allows extra keys; store `question_results` (with evidence_ref, not full file content) in the same report document so history and diff include them.
- Add at least one question-based requirement that **accepts_file** (e.g. "Point to your governance policy or data dictionary") as a pilot before expanding.
