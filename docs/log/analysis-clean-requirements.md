# Analysis: Clean factor requirement set

Goal: Keep in Clean only what is (1) inarguably "clean" data quality, (2) testable via SQL or platform CLIs (e.g. AWS, Databricks). Move requirements that belong to other factors or are not yet testable to those factors or defer.

---

## Current Clean requirements (from factor-00-clean) vs. fit and testability

| Requirement | Keep in Clean? | Why |
|-------------|----------------|-----|
| **Format standardization** | Yes | Inarguable: inconsistent dates/currencies/formats break aggregation and learning. **Testable:** SQL pattern checks, type checks (e.g. `format_consistency.sql`, `type_consistency.sql` in v0). |
| **Null handling** | Yes | Inarguable: nulls affect correctness and model behavior. **Testable:** SQL `null_rate` per column (v0). |
| **Deduplication** | Yes | Inarguable: duplicates skew counts and training. **Testable:** SQL duplicate rate on candidate keys (v0). |
| **Business rule validation** | Partial | Complex rules (e.g. ship date &gt; purchase date) are domain-specific and not generically SQL-testable. **Keep:** a narrow, testable slice: numeric/domain validity (e.g. values that should be positive are not zero/negative). v0 has `zero_negative_rate`. Full "business rule validation" → defer. |
| **Documentation** | No (move) | "Known data quality issues documented" is about metadata and descriptions → **Contextual** (column/table descriptions, documentation). Defer from Clean. |
| **Noise removal** | Defer | Content quality for RAG (boilerplate, headers removed before embedding). Not generically SQL-testable; would need content/embedding pipelines. Defer. |
| **PII redaction** | No (move) | PII handling, detection, masking are governance and compliance → **Compliant** (PII handling, PII detection, masking policies). v0 has `pii_detection_rate` under Clean; for the *factor doc* we treat PII as Compliant and can reference "data quality aspect of PII" there. Clean stays about non-PII data quality. |
| **Factual accuracy** | Defer | Would require ground truth; not SQL/CLI-testable. Defer. |
| **Bias auditing** | No (move) | **Compliant** already has "Bias monitoring". Not generically SQL-testable. Belongs in Compliant; defer from Clean. |
| **Harmful content removal** | Defer | Content safety; not SQL-testable in a generic way. Defer. |
| **Label validation** | Defer | ML labels; not SQL-testable without label metadata. Defer. |
| **Dataset versioning** | Defer | Reproducibility/traceability; could be **Correlated** or platform capability. Not a simple per-column/table SQL check. Defer. |

---

## Core Clean set (inarguable, SQL/CLI-testable)

1. **Null handling** — Null rate per column; acceptable threshold by workload. Key: `null_rate`. SQL: `COUNT(*) - COUNT(col)` / `COUNT(*)`.
2. **Deduplication** — Duplicate rate on candidate key columns. Key: `duplicate_rate`. SQL: `1 - COUNT(DISTINCT key) / COUNT(key)`.
3. **Format consistency** — Dates, currencies, units, and types consistent so aggregations and models see uniform formats. Key: `format_consistency` or `format_inconsistency_rate`. SQL: pattern/format checks per column.
4. **Type consistency** — Values in a column match expected type (e.g. string column not mixing numeric and non-numeric in a way that breaks parsing). Key: `type_inconsistency_rate`. SQL: pattern or type checks.
5. **Numeric validity** — Columns that should be positive (e.g. quantities, amounts) have no zero/negative values beyond an acceptable rate. Key: `zero_negative_rate`. SQL: `SUM(CASE WHEN col <= 0 THEN 1 ELSE 0 END) / COUNT(*)`.

These five are the **core Clean** set: each is clearly data quality, and each is testable with SQL (or platform CLI where applicable). They align with what v0 already tests under Clean (null_rate, duplicate_rate, format_consistency, type_inconsistency_rate, zero_negative_rate). PII is treated as Compliant in the factor docs; the agent can still run a PII-pattern test and report it under Compliant or a dedicated PII requirement there.

---

## Moved to other factors

- **PII redaction / PII detection** → **Compliant** (PII handling, masking, detection).
- **Documentation** (of quality issues) → **Contextual** (descriptions, metadata) or drop from Clean.

---

## Deferred (later or other factors)

- **Business rule validation** (full) — Keep only the testable slice (zero_negative, type) in Clean; complex rules later or as extensions.
- **Noise removal** — RAG content quality; not generic SQL.
- **Factual accuracy** — Would need ground truth.
- **Bias auditing** → Compliant (bias monitoring).
- **Harmful content removal** — Content safety; defer.
- **Label validation** — ML-specific; defer.
- **Dataset versioning** — Correlated or platform; defer.

---

## Stack capabilities (Clean)

Keep capabilities that support the five core requirements and are observable or configurable via platform:

- **Validation & quality checks** — Schema validation at ingestion (type, range, mandatory). Observable via schema/catalog; some platforms expose via CLI/API.
- **Profiling & baselines** — Data profiling to establish baselines. Testable via platform profiling tools or SQL.
- **Deduplication** — Dedup in ingestion or transformation. Platform capability; can be noted in assessment.
- **Alerting** — Alerting on validation failures. Platform capability; defer detailed testing or note in report.

Capabilities that are clearly Compliant (PII detection, audit, etc.) or not yet testable (re-indexing, quality monitoring) can be dropped from Clean or moved to other factor docs.
