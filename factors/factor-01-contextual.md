# Factor 1: Contextual

**Definition:** Meaning is explicit and colocated with the data. No external lookup, tribal knowledge, or human context is required to take action on the data.

## The Shift

If the data's meaning lives outside the system or is not accessible at inference-time, the data is not interpretable. Traditional analytics tolerates implicit meaning — analysts learn the schema, read a wiki, ask colleagues. AI systems have none of that context. A model consuming data with ambiguous column names, missing relationship declarations, or undocumented business logic is operating blind.

Contextual data ensures consistent interpretation across contexts and models at inference-time. Meaning must be explicit, machine-readable, and colocated with the data it describes.

Meaning can be broken into four dimensions:

- **Structural Semantics (What the data is):** Typed schemas, constraint declarations, and evolution contracts encode the data's formal identity.
- **Business Semantics (What the data means):** Versioned definitions, calculation logic, and controlled vocabularies encode authoritative meaning.
- **Entity Semantics (How the data connects):** Typed, scoped, and/or probabilistic relationships encode referential integrity of meaning.
- **Contextual Semantics (When/where it applies):** Temporal scope, jurisdictional applicability, provenance, and confidence encode the boundaries of validity.

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for missing context: Moderate.** Humans are in the loop. They can look up column definitions in a wiki, ask a colleague what a table represents, or infer meaning from experience. Structural constraints and descriptions are helpful but not essential — the analyst compensates.

**L2 (RAG and retrieval systems)** — **Tolerance for missing context: Low.** The model has no tribal knowledge. If meaning is not colocated with the data, the model generates answers without understanding what the data represents. Business definitions, semantic models, and declared relationships become critical because they are the only context the model has at inference-time.

**L3 (ML model training and fine-tuning)** — **Tolerance for missing context: Very low.** Ambiguous semantics propagate into learned representations. If the model does not know what a column means, what relationships exist, or when data is valid, it cannot learn the right signal. Full semantic coverage is essential — meaning that is implicit or external to the data at training time is meaning the model will never have.

## Requirements

What must be true about the data for each workload. These are the core Contextual requirements, organized by semantic dimension. Requirements are additive by strictness: meeting the bar for a stricter workload implies meeting it for less strict workloads.

### Structural Semantics

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Primary key defined** | Primary keys declared on most tables so identity is explicit; analysts can compensate when missing | Primary keys declared on tables used for retrieval so the system can identify and deduplicate entities | Primary keys declared on all assessed tables; identity must be unambiguous in training data |

### Business Semantics

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Semantic model coverage** | A semantic model (business definitions, metrics, calculation logic) exists for key datasets; not required for all tables | Semantic model covers tables used by the retrieval system so the model has authoritative definitions at query time | Semantic model covers all assessed tables; business meaning is fully explicit and machine-readable for training |

### Entity Semantics

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Foreign key coverage** | Key relationships between tables are declared (FK constraints or equivalent); analysts can infer undeclared joins | Relationships are declared for tables in the retrieval scope so the system can traverse and join correctly | Relationships declared for all assessed tables; the model must learn from data with explicit relational structure |

### Contextual Semantics

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Temporal scope present** | Tables with time-bounded data have identifiable temporal columns (e.g. created_at, updated_at); analysts infer time context | Temporal columns are present and identifiable for retrieval-scoped tables so the system can scope by recency or validity | Temporal columns present on all assessed tables with time-bounded data; training data must have explicit temporal boundaries |

## Required Stack Capabilities

What the platform must support to consistently meet these requirements. Capabilities describe the system; requirements describe the data.

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Constraint declarations** | Platform supports PRIMARY KEY and FOREIGN KEY constraints (enforced or declared) | — | Constraints are enforced, not just declared |
| **Semantic model layer** | Platform supports or integrates with a semantic model (e.g. semantic views, dbt semantic layer, catalog with business definitions) | Semantic model is queryable at inference-time (not just documentation) | Semantic model is versioned and covers all assessed tables |
| **Metadata queryability** | Table and column metadata (types, constraints, descriptions) are queryable via SQL or API | — | — |

## Requirement keys (for tests and remediation)

Stable identifiers for use in test definitions, threshold config, and remediation templates.

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Structural | Primary key defined | `primary_key_defined` |
| Business | Semantic model coverage | `semantic_model_coverage` |
| Entity | Foreign key coverage | `foreign_key_coverage` |
| Contextual | Temporal scope present | `temporal_scope_present` |

Implementation status by suite and platform: [docs/coverage/README.md](../docs/coverage/README.md).
