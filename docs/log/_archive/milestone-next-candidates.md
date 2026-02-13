# Next milestone candidates

**Date:** 2026-02-10

**Context:** Clean factor is E2E on DuckDB and SQLite (all five requirement keys + table_discovery). Estate assessment and YAML/JSON manifest with per-target scope are done. Add-platform meta-skill and docs/coverage exist. Below are recommended next milestones in rough priority order.

---

## 1. Threshold overrides (recommended next)

**Goal:** Users can override L1/L2/L3 thresholds without changing code.

**Why now:** The CLI already has `--thresholds` and `AIRD_THRESHOLDS`; config has `thresholds_path`. Only the runner and scoring path still use the built-in dict. Wiring the file is a small, spec-aligned change that unlocks per-project or per-environment tuning.

**Scope:**
- Load optional JSON from `config.thresholds_path` (same shape as `DEFAULT_THRESHOLDS`: requirement key → { l1, l2, l3 }).
- In `agent/run.py` (or `agent/thresholds.py`), use loaded overrides when present; merge with or override defaults by key.
- Document the JSON shape in CLI spec or a short thresholds reference.
- No change to report schema; pass/fail already per workload.

**Out of scope:** UI for editing thresholds; validation beyond “valid JSON and expected keys.”

---

## 2. Remediation linkage

**Goal:** Failed tests link to remediation content so the agent (or user) can suggest fixes.

**Why:** Project spec calls out “remediation suggestions” and “remediation templates per requirement key.” Today the report only has pass/fail and measured values; there is no content for “what to do when null_rate fails.”

**Scope:**
- Define a remediation template shape and location (e.g. `factors/remediation/clean/null_rate.md` or under `docs/`).
- Add at least one template per Clean requirement key (short: what it is, why it matters, 1–2 fix patterns).
- Report builder: for each failed test, include a `remediation_ref` (path or requirement key) so the agent skill can load and tailor the suggestion.
- Interpret/remediate skill: use the ref when generating suggestions.

**Out of scope:** Agent executing fixes; full coverage for all factors.

---

## 3. Context file wired into discovery

**Goal:** Optional context YAML actually influences scope or behavior.

**Why:** Spec and config support `--context` / `AIRD_CONTEXT`, but discovery (and run) never read it. Wiring it closes the loop for “scope, exclusions, target level” and nullable-by-design or PII hints mentioned in the spec.

**Scope:**
- Define context YAML shape (schemas, tables, exclusions, target_level L1|L2|L3, optional overrides).
- In discovery (or pipeline), pass `config.context_path`; if present, load and apply (e.g. filter schemas/tables, or pass context into report for interpret step).
- Document the shape in CLI spec or `skills/references/context-file.md`.

**Out of scope:** Persisting context per connection; full use of every override in scoring.

---

## 4. Automated E2E test

**Goal:** A single pytest (or script) that creates temp DBs, runs assess, and asserts on report shape and expected pass/fail.

**Why:** `verify_setup.py` is manual. A test in CI would catch regressions in pipeline, report shape, and threshold behavior.

**Scope:**
- Add pytest (or equivalent) that: builds temp DuckDB (and optionally SQLite) with known data (e.g. nulls, duplicates), runs `run_assess` or CLI assess, loads report.
- Assert: report has expected top-level keys; result count in a known range; at least one failure where we expect it (e.g. null_rate on a column we left null).
- Run in CI (e.g. GitHub Actions) on push or PR.

**Out of scope:** Full matrix of platforms; property-based tests.

---

## 5. First community platform (e.g. Snowflake or Postgres)

**Goal:** One new platform added using the add-platform meta-skill pattern; documented in docs/coverage.

**Why:** Validates the add-platform skill, proves the extension path, and gives contributors a reference. Snowflake is mentioned in the project spec; Postgres is a common second SQL platform.

**Scope:**
- Implement adapter, Clean suite, and (if needed) discovery path for one platform.
- Register in `agent/platform/__init__.py` and update `docs/coverage/README.md`.
- Optionally add a short “Adding a platform” section to CONTRIBUTING.md referencing the add-platform skill and manifest/coverage docs.

**Out of scope:** Supporting every dialect; official “blessed” driver list.

---

## Recommendation

**Do “Threshold overrides” next.** It’s small, spec-aligned, and unblocks per-project tuning. Then either **Remediation linkage** (high user value) or **Automated E2E** (stability for everything that follows).

---

## Moving forward (after 1, 3, 4 are done)

Once threshold overrides, context file, and E2E tests are in place, spend time on **how** to move forward:

- **Remediation (2)** vs **first platform (5):** Remediation ties failures to fix guidance and completes the “assess → interpret → suggest” loop. A first community platform validates the add-platform skill and attracts contributors. Decide whether “complete the loop” or “prove extensibility” matters more for the next release or demo.
- **Factor 2 (Contextual) and beyond:** Clean is fully implemented. The next factor (Contextual, Consumable, etc.) will need requirement keys, a minimal suite, and possibly new target types (e.g. column comments, lineage). Plan one factor at a time; reuse the Clean pattern (requirement keys → suite → coverage doc).
- **CI:** Add a GitHub Action (or similar) that runs `pytest tests/` and optionally `scripts/verify_setup.py` on push/PR so regressions are caught automatically.
- **Community:** Document “Adding a platform” in CONTRIBUTING and point to the add-platform skill and docs/coverage. Consider a small “community suites” or “examples” area for out-of-tree platforms once the first one is in-tree.
