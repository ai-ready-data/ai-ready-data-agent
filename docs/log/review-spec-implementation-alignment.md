# Review: Spec–implementation alignment

**Date:** 2026-02-11

**Scope:** Full read of all specs, designs, skills, factor docs, and implementation code. Assessment of how well the specs align with the current codebase and whether the implementation should be scrapped in favor of spec refinement.

---

## Summary

The implementation is a faithful, partial realization of the specs. Alignment is high where implementation exists; the gap is coverage (one factor, one category of tests), not architectural drift. The specs serve a critical role as the alignment mechanism for coding agents — they are not documentation overhead. The recommendation is to keep both and focus energy on factor content, platform-capability tests, and filling the framework.

---

## 1. Strong alignment

### CLI surface area

The CLI spec defines 8 commands (assess, discover, run, report, save, history, diff, suites). All 8 are implemented in `agent/cli.py` with the correct flags, argument shapes, and dispatch logic. The composable pipeline (discover → run → report → save) works, and assess is correctly implemented as an orchestration of those primitives. This is the spec's core contract and it is met.

### Architecture

The design doc (`design-cli-architecture.md`) prescribes a specific package layout: `cli.py`, `config.py`, `pipeline.py`, `discovery.py`, `run.py`, `report.py`, `storage.py`, `audit.py`, and a `platform/` package with `registry.py`, `connection.py`, `executor.py`, and platform adapters. The implementation matches this layout file for file.

### Config resolution

The spec says config is resolved once from env + args, passed down, and components do not read env directly. `Config.from_env()` + `Config.with_args()` implements exactly this pattern.

### Read-only enforcement

The spec's non-negotiable: only SELECT/DESCRIBE/SHOW/EXPLAIN/WITH. `executor.py` has a regex validator that blocks everything else. Enforced at the platform boundary as the architecture doc prescribes.

### Platform abstraction

Registry pattern, connection factory, suite registry — all implemented per spec. DuckDB, SQLite, and Snowflake adapters register on import. Suites are per-platform (common, common_sqlite, common_snowflake).

### Storage

Single SQLite DB at `~/.aird/assessments.db`, schema with assessments + audit tables, UUID-based assessment IDs, save/list/get — all per spec. Audit tables for queries and conversation exist and are wired through `AuditSink`.

### Estate mode

Multi-connection assess with per-connection sections and aggregate summary — implemented in `pipeline.py` with `_run_assess_estate`. Connection fingerprinting, error handling for failed connections (continue-on-error), manifest loading with `env:VAR_NAME` expansion, nested targets — all present.

### Thresholds

Per-requirement L1/L2/L3 thresholds with merge-over-defaults from JSON file. Implemented in `thresholds.py` exactly as the spec describes.

### Question-based requirements (survey)

The design doc (`design-question-based-requirements.md`, dated 2026-02-10) proposes a questions registry, per-suite questions, rubrics, file-based evidence. The implementation already has `questions_loader.py`, `survey.py`, per-suite YAML question files, rubric evaluation, and the `--survey` flag. The report includes `question_results`. File-based evidence (accepts_file, file_evaluator) is defined in the loader but not yet exercised.

### Skills and AGENTS.md

The agentic system spec prescribes AGENTS.md at root, a parent SKILL.md, and sub-skills (connect, discover, assess, interpret, interview, remediate, compare) with specific contract elements (identity, when-to-load, prerequisites, steps, forbidden actions). All 7 sub-skills exist and follow the contract. The parent skill has intent detection, workflow steps, and stopping points.

---

## 2. Gaps (spec > implementation)

| Area | Spec expectation | Current state |
|------|------------------|---------------|
| **Factor docs** | Six factors, each conforming to factor-spec | Only Factor 0 (Clean) exists; Factors 1–5 are "to be added" |
| **Test coverage** | Measured tests per factor + platform-capability tests | Only Clean factor has real tests (6 requirement keys); no platform-capability tests |
| **Diff** | Tests added/removed, pass/fail changes, score deltas | Prints L1/L2/L3 percentages side by side only — no test-level comparison |
| **Report schema** | "Documented schemas" for reports, results, inventory | No formal JSON schemas or runtime validation; shapes are implicit in code |
| **Audit conversation** | Full conversation recording when interactive + audit | Only one hardcoded message during pipeline; no structured conversation capture |
| **`--interactive` flag** | Structured interview question output for agent consumption | Flag exists but does not emit structured output; interview is entirely in skills layer |
| **Logging** | `--log-level` controls debug/info/warn/error output | Flag is accepted but not wired to a logger; no log output exists |
| **Context persistence** | "CLI may save context after assess" | Not implemented |
| **Optional commands** | `connect` (test connection), `generate` (test list) | Not implemented (spec marks as optional/future) |

---

## 3. Decision: do not scrap the implementation

**Reasoning:**

1. **The implementation validates the specs.** Architecture, CLI surface, composable pipeline, platform abstraction, estate mode, thresholds, survey — all work end-to-end. Scrapping it would discard proven validation.

2. **The specs serve a critical role.** This is an agentic project. The specs are the primary alignment mechanism for coding agents consuming the codebase. A high spec-to-code ratio is appropriate here — the specs tell agents what to build, how components relate, and what constraints hold. They are not overhead.

3. **The gap is coverage, not design.** The architecture supports six factors, three workloads, multiple platforms, question-based and measured requirements, composable pipelines, estate mode, audit, and history. The content only fills out one factor with one category of tests. The infrastructure is ready for more than it currently carries.

---

## 4. Recommendations (priority order)

1. **Write factor docs for Factors 1–5** (Contextual, Consumable, Current, Correlated, Compliant) with real requirement keys. This is where the project becomes meaningful — the framework's value is in breadth and specificity of what it assesses.

2. **Add platform-capability tests.** Currently every test is a data-quality measurement (rate of X per column/table). The spec explicitly calls out tests that check platform capabilities (lineage, masking, freshness metadata). These would differentiate the tool from a generic data quality checker.

3. **Shore up thin spots.** Make diff useful (test-level comparison), wire up logging, resolve `--interactive` (make it work or remove it). Small wins that make the tool feel complete.

4. **Specs evolve with code.** The architecture is settled. Future work should be code-first with specs updated to match, not spec-first with implementation catching up — unless a design decision needs resolution before coding (in which case a design doc is the right venue).
