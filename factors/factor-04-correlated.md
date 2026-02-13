# Factor 4: Correlated

**Definition:** Data is traceable from source to every decision it informs.

## The Shift

AI systems are compositional. Data flows through transformations, feature engineering, model inference, and post-processing before producing an output. When something goes wrong — a bad prediction, a hallucinated answer, a biased decision — you need to trace backward: Was it the source data? A transformation bug? A model issue? A post-processing error?

Without end-to-end traceability, a bad output is a black box.

Traditional analytics has similar needs, but the stakes are different. A wrong dashboard number gets noticed, investigated, fixed. A wrong AI decision may be invisible — or may have already triggered downstream actions before anyone notices.

Correlated data enables:
- **Root cause analysis:** Trace a bad output back to its source
- **Impact analysis:** Understand what's affected when source data changes
- **Reproducibility:** Reconstruct any past decision for audit or debugging
- **Cost attribution:** Know which data and transformations contributed to what outcomes

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for missing traceability: Moderate.** Analysts can investigate issues manually. Lineage is helpful for impact analysis but not critical for every query.

**L2 (RAG and retrieval systems)** — **Tolerance for missing traceability: Low.** When a chatbot gives a wrong answer, you need to know: which chunks were retrieved? What were their sources? What was the ranking? Without this, debugging is guesswork.

**L3 (ML model training and fine-tuning)** — **Tolerance for missing traceability: Very low.** Training data provenance is a regulatory requirement (EU AI Act). You must be able to reconstruct what data trained what model at what time. Drift detection requires baselines to compare against.

## Requirements

What must be true about the data for each workload. Current implementation focuses on classification and lineage infrastructure.

### Classification & Ownership

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Object classification** | Key tables tagged with domain/owner | Tables in AI scope have classification tags | All tables have domain, owner, and sensitivity tags |
| **Column classification** | Sensitive columns identified | Columns in retrieval scope classified (PII, sensitivity) | All columns classified for governance and feature selection |

### Lineage & Traceability

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Lineage queryable** | Lineage data exists and can be queried | Lineage covers AI-serving data paths | Full lineage with column-level granularity; temporal reconstruction |

## Required Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Tagging infrastructure** | Platform supports object and column tags | Tags are queryable at runtime | Tag inheritance through transformations |
| **Lineage capture** | Automated lineage from SQL | Column-level granularity | Bi-temporal reconstruction |
| **Access history** | Query logs available | Access patterns queryable | Full audit trail |

## Requirement keys (for tests and remediation)

Current implementation measures classification coverage and lineage availability:

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Classification | Object classification | `object_tag_coverage` |
| Classification | Column classification | `column_tag_coverage` |
| Lineage | Lineage queryable | `lineage_queryable` |

## Not Yet Implemented

These requirements from `/factors.md` are not yet testable via automated SQL checks:

- **Data quality signals:** Quality metadata (completeness, freshness scores) attached to data
- **Drift baselines:** Reference distributions stored for comparison
- **Decision traces:** Linked traces from inputs → retrieval → outputs
- **Retrieval quality metadata:** Relevance scores and ranking signals logged per query
- **Faithfulness signals:** Claim support scores and source attribution on outputs

Implementation status by suite and platform: [docs/coverage/README.md](../docs/coverage/README.md).
