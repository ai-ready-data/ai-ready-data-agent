# Factor 5: Compliant

**Definition:** Data is governed with explicit ownership, enforced access boundaries, and AI-specific safeguards.

## The Shift

AI introduces novel governance surface area that traditional data governance doesn't cover:

- **PII leaks through embeddings:** Personal data encoded in vector representations can't be masked at query time — it's baked into the model. Once trained, the PII is permanent.
- **Bias encoded in training distributions:** A biased dataset produces a biased model. The bias becomes structural, affecting every inference the model serves.
- **Model outputs as regulated decisions:** Credit scoring, hiring, content moderation — AI outputs increasingly fall under regulatory scrutiny (EU AI Act, CCPA, GDPR).
- **Consent and purpose limitations:** Data collected for analytics may not be permissible for training. Purpose creep from "reporting" to "AI training" may violate original consent.

Traditional RBAC and audit logs are necessary but insufficient. You need:
- **Technical protection:** Masking, anonymization applied *before* AI consumption — not at query time
- **Classification:** Sensitive data identified and tagged so policies can be enforced automatically
- **Purpose boundaries:** Explicit permissions for which AI systems can access what data for what purposes

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for governance gaps: Moderate.** Humans access data through controlled interfaces. RBAC and audit logs provide reasonable protection.

**L2 (RAG and retrieval systems)** — **Tolerance for governance gaps: Low.** The model may surface sensitive information in responses. PII must be masked before indexing. Access controls must prevent retrieval of restricted content.

**L3 (ML model training and fine-tuning)** — **Tolerance for governance gaps: Very low.** Training data becomes permanent. PII in training data is PII in the model. Bias in training data is bias in every inference. EU AI Act requires documented, representative datasets with provenance.

## Requirements

What must be true about the data for each workload. Current implementation focuses on PII protection and data classification.

### PII Protection

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Masking policies** | Masking on obvious PII (SSN, credit card) | Masking on all PII before AI consumption | Near-complete masking coverage; PII never reaches training |
| **Row-level security** | Row access policies on sensitive tables | Row access policies on AI-serving tables | Row access policies on all tables with restricted data |

### Classification

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Sensitivity classification** | Key sensitive columns tagged | All PII columns tagged for automated policy enforcement | Full classification; untagged sensitive data is a failure |

## Required Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Dynamic masking** | Platform supports column-level masking policies | Role-based conditional masking | — |
| **Row access policies** | Platform supports row-level security | Context-aware policies (role, time, purpose) | — |
| **Sensitivity tags** | Platform supports data classification tags | Tags drive automated policy application | — |

## Requirement keys (for tests and remediation)

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| PII Protection | Masking policies | `masking_policy_coverage` |
| PII Protection | Row-level security | `row_access_policy_coverage` |
| Classification | Sensitivity classification | `sensitive_column_tagged` |

## Not Yet Implemented

These requirements from `/factors.md` address the AI-specific compliance challenges but are not yet testable:

### Addressing PII in Embeddings
- **Pre-training anonymization:** PII removed or anonymized before embedding generation
- **Embedding audit:** Ability to verify embeddings don't leak personal data

### Addressing Bias
- **Bias assessment metadata:** Fairness metrics and demographic error rates on models
- **Training data representativeness:** Statistical validation of training distribution

### Addressing Regulatory Requirements
- **Legal basis metadata:** Documented consent, legitimate interest, or contractual basis
- **Training data provenance:** Source documentation for training datasets
- **Erasure-ready identifiers:** Ability to locate and delete personal data across all stores
- **Decision reconstruction:** Link decisions to inputs, model version, and context

### Addressing Purpose Limitations
- **Purpose boundaries:** Declared scope for which AI systems can access what data
- **Consent tracking:** Which data has consent for which purposes

Implementation status by suite and platform: [docs/coverage/README.md](../docs/coverage/README.md).
