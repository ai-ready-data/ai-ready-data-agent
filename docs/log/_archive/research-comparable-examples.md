# Research: Comparable examples (data quality & assessment)

**Date:** 2026-02-10

**Context:** Good examples of what we’re trying to do—declarative assessment over data platforms, threshold-based scoring, report generation for tooling/agents—and how our project compares.

---

## 1. dbt (data tests) — Closest execution model

**What they do:** Declarative tests in YAML; **generic tests** are SQL templates that take `model` and `column_name` and are expanded per column/table. A single definition turns into many concrete checks. Tests return 0 rows = pass.

**Relevance to us:** Our `expand_tests()` + `query_template` + inventory (columns/tables) is the same idea: one suite definition → many tests. dbt uses severity (`warn` / `error`) instead of L1/L2/L3.

**Takeaways:** Their generic test pattern (SQL file with `model`/`column_name`, one test per resource) is a good reference for “one definition, N runs.” Their **singular tests** (custom SQL, 0 rows = pass) are like our one-off queries (e.g. `table_discovery`).

- [Writing custom generic data tests](https://docs.getdbt.com/best-practices/writing-custom-generic-tests)

---

## 2. DataHub Open Data Quality Assertions Spec — Portable, declarative format

**What they do:** [Open Assertions Spec](https://docs.datahub.com/docs/assertions/open-assertions-spec): **YAML-first**, framework-agnostic assertions (Freshness, Volume, Column, Custom SQL, Schema). Each assertion has a **condition** (e.g. `between`, `equal_to`) and optional **failure_threshold**. The spec compiles to Snowflake DMFs, dbt tests, Great Expectations, etc.

**Relevance to us:** Same goal: “declare checks in one place, run them anywhere.” They don’t have workload tiers (L1/L2/L3); they have one condition per assertion. Our factor spec + requirement keys + L1/L2/L3 thresholds are a more structured, workload-aware version of that.

**Takeaways:** Their condition + value/min/max pattern is a clean way to describe “pass when metric ≤ X.” Our threshold overrides (milestone) are the same idea (policy in config). Their **Custom SQL** type (single scalar result compared to a condition) is very close to our “query returns one number, compare to threshold.”

---

## 3. SDF (Semantic Data Framework) — Checks as SQL

**What they do:** [SDF Checks](https://docs.sdf.com/guide/data-quality/checks): **Checks** are SQL queries run against an **information schema** (metadata from `sdf compile`). Pass = query returns no rows. They also have **Tests** (data-level, e.g. non-null, ranges) and **Reports** (SQL over the info schema for analysis).

**Relevance to us:** Different target (metadata vs our data metrics) but same “declarative SQL check” idea. We run SQL on the **data** (null rate, duplicate rate, etc.); they run SQL on **metadata** (e.g. “no PII column without a classifier”). Our discovery → inventory → expand is analogous to their compile → information schema → check.

**Takeaways:** “Check = SQL that should return empty” is a simple, portable contract. We already do “query returns one number, then threshold”; the empty-result pattern could be useful for future metadata or “must not exist” checks.

---

## 4. Great Expectations (GX) — Expectations and thresholds

**What they do:** Expectations (e.g. `expect_column_values_to_not_be_null`, `expect_column_mean_to_be_between`) with **thresholds**; run in Python or via YAML. Often used as a **pipeline gate** (fail the job if expectations fail).

**Relevance to us:** Same idea: “measure something, compare to a threshold.” GX is more pipeline- and Python-centric; we’re read-only assessment + report. Our L1/L2/L3 is a **tiered threshold** model they don’t have.

**Takeaways:** Their expectation + kwargs pattern is another way to get to “declarative check + threshold”; our factor/requirement keys + threshold JSON are a cleaner fit for multi-workload (L1/L2/L3) and agent consumption.

---

## 5. OpenMetadata / DataHub (products) — Catalog + DQ

**What they do:** Data catalog with **tests** (row count, freshness, null %, custom SQL) and **configurable thresholds**; results shown in the UI and sometimes in APIs.

**Relevance to us:** Same “run checks, store results, show in a report” flow. They’re full catalog products; we’re a focused assessment runner that produces a report (and remediation refs) for an **agent** and CLI.

**Takeaways:** Our **report schema** (summary + results list + per-test pass/fail + optional remediation_ref) is the same kind of artifact these systems expose; keeping it stable and documented is the right approach.

---

## 6. Research: “AI data readiness” (e.g. AIDRIN) — Conceptual sibling

**What they do:** Frameworks like [AIDRIN](https://osti.gov/servlets/purl/2545803) and “Data Readiness Reports” define **dimensions** (completeness, duplicates, fairness, FAIR, etc.) and sometimes scores. They’re usually research prototypes, not production runners.

**Relevance to us:** We’re implementing the same **concept** (assess data for AI readiness along multiple dimensions) as a **runnable system**: factors = dimensions, requirements = measurable criteria, L1/L2/L3 = workload-specific bars. No open-source runner does exactly “factors + workload tiers + multi-connection estate + agent-oriented report” in one stack.

---

## Summary table

| Example                | Declarative checks | SQL / metrics     | Thresholds     | Workload tiers (L1/L2/L3) | Portable / multi-back end | Agent-oriented report |
|------------------------|-------------------|-------------------|----------------|---------------------------|----------------------------|------------------------|
| **dbt**                | ✅ YAML + generic  | ✅ SQL templates  | Severity       | ❌                        | ❌ (dbt only)              | ❌                     |
| **DataHub Assertions** | ✅ YAML            | ✅ (incl. custom SQL) | ✅ condition | ❌                        | ✅                         | ❌                     |
| **SDF**                | ✅ SQL checks      | ✅ (metadata)     | Pass = 0 rows  | ❌                        | ✅ (Trino)                 | ❌                     |
| **Great Expectations** | ✅ Python/YAML     | ✅                | ✅             | ❌                        | Partial                   | ❌                     |
| **Our project (AIRDF)**| ✅ Suites + factor spec | ✅ Query templates | ✅ L1/L2/L3  | ✅                        | ✅ (platform adapters)     | ✅                     |

---

## Bottom line

The **closest existing examples** are **dbt’s generic tests** (expansion from one definition to many tests) and **DataHub’s Open Assertions Spec** (portable, declarative, condition-based). None of them combine **AI-readiness factors**, **L1/L2/L3 workload tiers**, **estate/multi-connection**, and **report + remediation for an agent** the way we do—so there aren’t direct “do it like X” clones, but those two are the best references for patterns and formats we can reuse or cite.
