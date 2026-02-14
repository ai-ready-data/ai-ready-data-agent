# Factor 1: Contextual

**Definition:** Meaning is explicit and colocated with the data. No external lookup, tribal knowledge, or human context is required to take action on the data.

## Why It Matters for AI

If the data's meaning lives outside the system or is not accessible at inference-time, the data is not interpretable. Traditional analytics tolerates implicit meaning — analysts learn the schema, read a wiki, ask colleagues. AI systems have none of that context. A model consuming data with ambiguous column names, missing relationship declarations, or undocumented business logic is operating blind.

Contextual data ensures consistent interpretation across contexts and models at inference-time. Meaning must be explicit, machine-readable, and colocated with the data it describes.

Meaning can be broken into four dimensions:

- **Structural Semantics (What the data is):** Typed schemas, constraint declarations, and evolution contracts encode the data's formal identity.
- **Business Semantics (What the data means):** Versioned definitions, calculation logic, and controlled vocabularies encode authoritative meaning.
- **Entity Semantics (How the data connects):** Typed, scoped, and/or probabilistic relationships encode referential integrity of meaning.
- **Contextual Semantics (When/where it applies):** Temporal scope, jurisdictional applicability, provenance, and confidence encode the boundaries of validity.

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for missing context: Moderate.** Humans are in the loop. They can look up column definitions in a wiki, ask a colleague what a table represents, or infer meaning from experience. Structural constraints and descriptions are helpful but not essential — the analyst compensates.

**L2 (RAG and retrieval systems)** — **Tolerance for missing context: Low.** The model has no tribal knowledge. If meaning is not colocated with the data, the model generates answers without understanding what the data represents. Business definitions, semantic models, and declared relationships become critical because they are the only context the model has at inference-time.

**L3 (ML model training and fine-tuning)** — **Tolerance for missing context: Very low.** Ambiguous semantics propagate into learned representations. If the model does not know what a column means, what relationships exist, or when data is valid, it cannot learn the right signal. Full semantic coverage is essential — meaning that is implicit or external to the data at training time is meaning the model will never have.

## Requirements

| Requirement | Description |
|-------------|-------------|
| **Documented semantics** | Data assets carry explicit, machine-readable descriptions so AI systems can interpret meaning without human context. |

### Tests

| Test | Requirement | Scope | Direction | L1 | L2 | L3 |
|------|-------------|-------|-----------|----|----|-----|
| `comment_coverage` | Documented semantics | Per schema | gte | ≥ 0.30 | ≥ 0.70 | ≥ 0.90 |

**Assessment variants** in `assess.sql.jinja`:

| Block | When to use |
|-------|-------------|
| `comment_coverage` | Default. Measures fraction of columns with non-empty comments. |

## Interpretation

| Score | Interpretation |
|-------|---------------|
| 1.00 | Perfect — every column has a description |
| ≥ threshold | Pass — sufficient coverage for workload |
| < threshold | Fail — too many columns lack descriptions for AI to interpret reliably |
| < 0.10 | Critical — schema is essentially undocumented |
