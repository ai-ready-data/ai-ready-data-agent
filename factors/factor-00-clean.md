# Factor 0: Clean

**Definition:** Clean data is consistently accurate, complete, valid, and free of errors that would compromise downstream consumption.

## The Shift

The importance of data quality is nothing new, but the consequences of poor data quality are dramatically increased when used by AI systems.

Clean data is not perfect data. Perfection is neither achievable nor necessary. What matters is that data is clean *enough* for the workload it feeds. Different workloads (use cases) have materially different tolerance thresholds for data quality. The demands escalate as the system's autonomy increases and as the cost of errors shifts from recoverable to permanent.

Clean data is Factor 0 because nothing else in the framework matters without it. Context, consumability, freshness, lineage, and compliance all assume that the underlying data is trustworthy. If it isn't, you are building on a foundation that will fail — not loudly or immediately, but quietly and pervasively.

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for dirty data: Moderate.** Humans are in the loop. They interpret results, notice anomalies, and ask clarifying questions before acting.

**L2 (RAG and retrieval systems)** — **Tolerance for dirty data: Low.** The model selects chunks from your corpus and presents them — often verbatim — as answers. Any individual chunk can become the basis of a response.

**L3 (ML model training and fine-tuning)** — **Tolerance for dirty data: Very low.** Errors in training data are not retrieved — they are *learned*. The model encodes patterns from the training distribution into its weights. A bias, a labeling error, or a systematic data quality issue produces a model that is structurally inclined toward wrong answers across every inference it serves. Remediation means retraining.

## Requirements

What must be true about the data for each workload. These are the **core** Clean requirements. Requirements are additive by strictness: meeting the bar for a stricter workload implies meeting it for less strict workloads.

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Null handling** | Null rate per column is within acceptable bounds; nulls are filled where business logic supports a default, or flagged/categorized | Stricter null thresholds where nulls would appear in retrieved chunks | Stricter still; nulls in training data affect learned representations |
| **Deduplication** | Duplicate rate on candidate key columns is within bounds so counts and totals are not skewed | Corpus deduplicated (including near-duplicates) so retrieval rankings are not skewed | Strict deduplication so duplicate examples do not overweight patterns in the training distribution |
| **Format consistency** | Dates, currencies, and units are consistent so aggregations are valid | Terminology and structure consistent across the corpus to improve retrieval | Formats rigorously normalized so the model learns signal, not formatting noise |
| **Type consistency** | Values in a column match the expected type (e.g. no mixed numeric/non-numeric in a string column where one type is expected) | Same, with stricter thresholds where type confusion would affect retrieval or parsing | Same, with strict normalization for training |
| **Numeric validity** | Columns that should be positive (quantities, amounts) have zero/negative rate within bounds | Stricter where invalid numerics would appear in responses | Stricter for training data |

## Required Stack Capabilities

What the platform must support to consistently meet these requirements. Same additivity as requirements. (Capabilities that are primarily governance or compliance — e.g. PII detection — are specified under **Compliant**.)

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Validation & quality checks** | Schema validation at ingestion (type checks, range constraints, mandatory fields) | — | Automated quality gates that block training runs when data quality thresholds are not met |
| **Profiling & baselines** | Data profiling to establish and track quality baselines over time | — | Distribution drift monitoring against the distribution the model was trained on |
| **Deduplication** | Deduplication logic applied during ingestion or transformation | Corpus-level deduplication with similarity detection for near-duplicates | — |
| **Alerting** | Alerting on validation rule failures so issues are surfaced | — | — |

## Requirement keys (for tests and remediation)

Stable identifiers for use in test definitions, threshold config, and remediation templates. These align with SQL- and CLI-testable checks.

| Requirement (name) | Key |
|--------------------|-----|
| Null handling | `null_rate` |
| Deduplication | `duplicate_rate` |
| Format consistency | `format_inconsistency_rate` |
| Type consistency | `type_inconsistency_rate` |
| Numeric validity | `zero_negative_rate` |

