# Factor specification (abstract)

This document defines the **abstract shape** of a factor in the AI-Ready Data Framework. Every factor document conforms to this spec. The spec ensures consistency, enables mapping to tests and remediation, and gives a clear contract for adding or revising factors.

---

## 1. Factor identity

Each factor has:

| Field | Description |
|-------|-------------|
| **Index** | Non-negative integer (0–5). Used for ordering and stable reference. |
| **Name** | Short label (e.g. Clean, Contextual). Used in UI, reports, and docs. |
| **Definition** | One-sentence definition of the factor. Must appear at the top of the factor doc. |

The definition answers: *What does this factor mean for the data layer?* It is the canonical summary for the factor; the rest of the doc elaborates by workload (use case).

---

## 2. Required structure of a factor document

A factor document **must** contain the following, in order:

1. **Title** — `# Factor N: Name` (e.g. `# Factor 0: Clean`).
2. **Definition** — One sentence, marked as `**Definition:**` or equivalent.
3. **Requirements** — A section `## Requirements` with a table: *Requirement* (name or key), *L1*, *L2*, *L3*. Each cell describes what must be true for that workload, or `--` if the requirement does not apply for that workload. Requirements are additive by strictness: meeting the bar for a stricter workload (e.g. L3) implies meeting it for less strict workloads (L2, L1) unless the factor doc states otherwise.
4. **Required stack capabilities** — A section `## Required Stack Capabilities` (or equivalent) with a table: *Capability*, *L1*, *L2*, *L3*. Each cell describes what the platform must support for that workload, or `--` if not applicable. Same additivity as requirements.

**Optional** sections (recommended where they add clarity):

- **The Shift** (or similar) — Rationale and context: why this factor matters, how AI changes the stakes.
- **Per-workload tolerance** — Short paragraphs for each workload (L1, L2, L3) describing tolerance for failure (e.g. "Moderate" for Analytics, "Very low" for Training).
- **Closing** — e.g. "The Common Thread", "Key Questions", or a short summary.

Prose style and length are not constrained; only the presence and role of the required sections and tables are.

---

## 3. Requirements and requirement keys

**Requirements** are what must be true about the data (or the platform) for each workload (use case). Each requirement should have a **stable key** (a machine- and human-readable identifier) for use in tests, thresholds, and remediation.

- **Key format:** Lowercase, words separated by underscores (e.g. `null_handling`, `column_comment_coverage`, `pii_redaction`). No spaces; avoid special characters.
- **Use:** The same key is used in:
  - The factor doc (as the row identifier or as a slug derived from the requirement name).
  - Test definitions (each test is bound to one factor and one requirement key).
  - Threshold configuration (L1/L2/L3 thresholds per requirement key).
  - Remediation templates (one template per requirement key, or a documented convention for when no template exists).

If the factor doc uses a human-readable requirement name in the table, the key can be the slug form of that name (e.g. "Null handling" → `null_handling`). The mapping from key to human-readable name can live in the factor doc or in a central index.

**Requirements table shape:**

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| *key or name* | Prose or `--` | Prose or `--` | Prose or `--` |

Each row is one requirement. A cell with `--` means that requirement does not apply for that workload.

---

## 4. Stack capabilities

**Stack capabilities** are what the platform must support so that the requirements can be met consistently. They are not the same as requirements: requirements describe the data; capabilities describe the system.

- Capabilities may be referenced in assessments (e.g. "does the platform support X?") for platform-capability tests.
- They do not need stable keys for tests unless we add capability-based checks that require them. For the factor doc, a clear capability name in the table is sufficient.
- Same table shape: *Capability*, *L1*, *L2*, *L3*; cells are prose or `--`.

---

## 5. Relationship to tests and remediation

- **Tests:** Each test in a suite is tagged with a **factor** (name or index) and a **requirement** (requirement key). The test measures one or more aspects of that requirement for one or more workloads (L1/L2/L3). Test results are scored using thresholds keyed by factor, requirement, and workload (L1/L2/L3).
- **Remediation:** For each requirement key, there may be a remediation template that explains the requirement, why it matters, and generic fix patterns. The agent uses these to generate concrete suggestions. Not every requirement need have a template; absence can be documented.
- **Traceability:** Factor doc (requirement key + prose) → test definition (same requirement key) → threshold config (same key) → remediation template (same key). The abstract factor spec does not mandate a single file format for thresholds or remediation; it only requires that the **key** is the stable link.

**Requirement evaluation: measured vs asked.** A requirement key can be evaluated by a **measured test** (query/API + threshold) and/or by an **asked question** (the agent asks the user and records the answer; optionally a rubric gives pass/fail). Question-based requirements use the same factor and key and allow assessing process, governance, and intent. See [design-question-based-requirements.md](../designs/design-question-based-requirements.md).

---

## 6. Workloads (use cases) and short names (L1, L2, L3)

Requirements and capabilities are defined for **three workloads** — that is, three use cases that the data may feed. Different use cases have different tolerance for issues and therefore different requirement strictness. The framework is use-case-driven: *What are you building? Analytics, RAG, or training? Your requirements depend on that.*

The three workloads are:

| Short name (tables & config) | Workload (use case) | Meaning |
|------------------------------|----------------------|---------|
| **L1** | Descriptive analytics and BI | Humans in the loop; moderate tolerance for issues. |
| **L2** | RAG and retrieval systems | Low tolerance; any chunk can become a response. |
| **L3** | ML model training and fine-tuning | Very low tolerance; errors are learned, not just retrieved. |

In factor tables, threshold config, and test/report schemas we use the **short names L1, L2, L3** for brevity. They are ordered by **strictness of requirements** (Analytics least strict, Training most strict), not by maturity or goal. There is no expectation that teams "move up" from L1 to L3; each workload is a distinct use case.

**Additivity:** For a given requirement, meeting the bar for a stricter workload implies meeting it for less strict workloads: if you meet L3 you meet L2 and L1 for that requirement, unless the factor doc states otherwise. This ordering is what allows a single table and threshold set to cover all three use cases.

---

## 7. Conformance

A factor document **conforms** to this spec if:

1. It has a title of the form `Factor N: Name` with N in 0..5 and Name matching the factor name.
2. It contains a single-sentence **Definition** at or near the top.
3. It contains a **Requirements** section with a table that has columns for Requirement (or key) and L1, L2, L3.
4. It contains a **Required Stack Capabilities** section (or equivalent) with a table that has columns for Capability and L1, L2, L3.
5. Each requirement that is used by tests or remediation has a defined **requirement key** (in the doc or in a maintained mapping).

Conformance is checked by review or by tooling (e.g. a script that parses the doc and validates presence and shape of the required sections and tables). This spec does not require automated validation for v0.

---

## 8. Factor list (canonical)

The framework defines six factors. Each has a dedicated document that conforms to this spec.

| Index | Name | Definition (one line) |
|-------|------|------------------------|
| 0 | Clean | Accurate, complete, valid, and free of errors that would compromise downstream consumption. |
| 1 | Contextual | Meaning is explicit and co-located with canonical semantics. |
| 2 | Consumable | Served in the right format, at the right latencies, at the right scale. |
| 3 | Current | Reflects the present state, with freshness enforced by systems. |
| 4 | Correlated | Traceable from source to every decision it informs. |
| 5 | Compliant | Governed with enforced access controls, ownership, and AI-specific safeguards. |

Factor documents may be named e.g. `factor-00-clean.md`, `factor-01-contextual.md`, or any consistent scheme. The index and name are canonical; the filename is a convention.
