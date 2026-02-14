# Factor 0: Clean

**Definition:** Clean data is consistently accurate, complete, valid, and free of errors that would compromise downstream consumption.

## Why It Matters for AI

The importance of data quality is nothing new, but the consequences of poor data quality are dramatically increased when used by AI systems.

Clean data is not perfect data. Perfection is neither achievable nor necessary. What matters is that data is clean *enough* for the workload it feeds. Different workloads have materially different tolerance thresholds for data quality. The demands escalate as the system's autonomy increases and as the cost of errors shifts from recoverable to permanent.

Clean data is Factor 0 because nothing else in the framework matters without it. Context, consumability, freshness, lineage, and compliance all assume that the underlying data is trustworthy. If it isn't, you are building on a foundation that will fail — not loudly or immediately, but quietly and pervasively.

Models optimize on whatever signal is present — including noise. Dirty data doesn't just degrade output quality; it gets encoded into weights and embeddings as learned patterns, making errors systematic and hard to detect downstream.

## Per-Workload Tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for dirty data: Moderate.** Humans are in the loop. They interpret results, notice anomalies, and ask clarifying questions before acting.

**L2 (RAG and retrieval systems)** — **Tolerance for dirty data: Low.** The model selects chunks from your corpus and presents them — often verbatim — as answers. Any individual chunk can become the basis of a response.

**L3 (ML model training and fine-tuning)** — **Tolerance for dirty data: Very low.** Errors in training data are not retrieved — they are *learned*. The model encodes patterns from the training distribution into its weights. A bias, a labeling error, or a systematic data quality issue produces a model that is structurally inclined toward wrong answers across every inference it serves. Remediation means retraining.

## Requirements

| Requirement | Description |
|-------------|-------------|
| **Data completeness** | Data assets should not have missing values that compromise downstream consumption. |

### Tests

| Test | Requirement | Scope | Direction | L1 | L2 | L3 |
|------|-------------|-------|-----------|----|----|-----|
| `null_rate` | Data completeness | Per column | lte | ≤ 0.20 | ≤ 0.05 | ≤ 0.01 |

**Assessment variants** in `assess.sql.jinja`:

| Block | When to use |
|-------|-------------|
| `null_rate` | Default. Full table scan, exact result. |
| `null_rate_sampled` | Large tables (>1M rows). Uses `TABLESAMPLE` for an estimate. |

## Interpretation

| Score | Interpretation |
|-------|---------------|
| 0.00 | Perfect — no nulls detected |
| ≤ threshold | Pass — within acceptable bounds for workload |
| > threshold | Fail — requires remediation |
| > 0.50 | Critical — significant data quality issue |
