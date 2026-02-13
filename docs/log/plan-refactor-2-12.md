# Architecture Analysis for Extensibility — Refactor Plan

**Created:** 2026-02-12
**Status:** Planning
**Context:** Analysis of current architecture to identify extensibility gaps for MVP (platform-specific test suites, Snowflake first) and future (multi-platform, user-customizable test selection).

---

## Architecture Analysis

### How It Works Today

**Suite lifecycle:**
1. Platform adapters (`snowflake_adapter.py`, `duckdb_adapter.py`) register with a default suite name (e.g., `common_snowflake`)
2. YAML suite definitions in `agent/suites/definitions/` are auto-loaded on import → registered into the suite registry
3. Suites compose via `extends` (e.g., `snowflake_common.yaml` extends `clean_snowflake` + `contextual_snowflake`)
4. `--suite auto` resolves to the platform's default suite; `run_tests()` calls `get_suite(name)` → `expand_tests()` → execute
5. Filtering is limited to `--factor` (one factor) and `--schema`/`--tables` (inventory scope)

**What's well-designed:**
- YAML suite definitions are a good declarative foundation
- `requirements_registry.yaml` as single source of truth for thresholds/directions
- Platform registry pattern (scheme → adapter → default_suite) is clean and extensible
- Suite composition via `extends` is the right primitive
- Read-only executor enforcement is solid
- `expand_tests()` template expansion handles platform-specific SQL cleanly

---

### Issues Found

#### 1. No user-level test customization (HIGH — blocks "let users pick what to test")

**Current:** Users can only choose `--suite` (entire suite, all-or-nothing) or `--factor` (exactly one factor). There's no way to say "run these specific requirements" or "skip this test."

**Impact:** A user who only cares about null_rate and primary_key_defined must run the full suite. A user who wants clean + contextual but not consumable can't express this (they'd need to run `--factor clean` and then `--factor contextual` separately, getting two reports).

**Missing primitives:**
- `--requirement null_rate,primary_key_defined` (filter by requirement keys)
- `--factor clean,contextual` (multiple factors, not just one)
- `--exclude-requirement format_inconsistency_rate` (exclusion)
- User profile in context YAML to save these preferences

#### 2. Legacy Python suite files still exist (MEDIUM — contributor confusion)

**Current:** Both Python files (`clean_snowflake.py`, `contextual_snowflake.py`, `clean_duckdb.py`, `clean_sqlite.py`) AND their YAML equivalents exist. The Python files are no longer auto-imported (the `__init__.py` docstring says "deprecated fallbacks") but they still live in the tree.

**Impact:** A contributor adding a new factor for Snowflake might look at the Python files as the pattern to follow. The `skills/add-platform/SKILL.md` still says "new file `clean_{platform}.py`" — pointing to the old pattern.

#### 3. Suite loader doesn't validate requirement keys (MEDIUM — silent drift)

**Current:** The YAML loader validates test structure (required fields, valid target_type) but does NOT check whether the `requirement` key exists in `requirements_registry.yaml`.

**Impact:** A contributor can add a test with a typo in the requirement key (e.g., `null_rates` instead of `null_rate`) and it will load fine, but thresholds will default to 0.0 and pass/fail will be meaningless.

#### 4. `--factor` only accepts one factor (LOW → MEDIUM when more factors ship)

**Current:** `factor_filter` in `expand_tests()` is a single string — `if factor_filter and t.get("factor") != factor_filter: continue`.

**Impact:** When Consumable, Current, Correlated, and Compliant ship with real tests, users will want to run e.g. "clean + contextual" but not the rest. Currently they'd need two separate `aird assess` runs.

#### 5. No contributor guide for adding a factor (MEDIUM — ecosystem growth)

**Current:** `CONTRIBUTING.md` says "will be documented here." The `skills/add-platform/SKILL.md` covers adding a platform adapter but still references the old Python suite pattern, not YAML.

**Impact:** External contributors face a blank page when trying to add tests for a new factor or extend an existing one.

#### 6. No test-level tags or metadata (LOW for MVP, HIGH for future)

**Current:** Tests have `id`, `factor`, `requirement`, `target_type`, `query`/`query_template`. No `tags`, `description`, `severity`, or `category`.

**Impact:** Can't offer profiles like "quick smoke test" (5 tests) vs "full assessment" (50 tests). Can't mark tests as "essential" vs "advanced."

---

### What to Change — MVP (Snowflake focus)

These changes make the MVP clean and set up the right extension points:

#### A. Multi-factor and multi-requirement filtering

Allow `--factor clean,contextual` and add `--requirement null_rate,primary_key_defined`.

**Scope:**
- `agent/run.py` → `expand_tests()`: accept `factor_filter` as `Optional[list[str]]` and add `requirement_filter: Optional[list[str]]`
- `agent/config.py` → add `requirement_filter` field
- `agent/cli.py` → add `--requirement` flag, change `--factor` to accept comma-separated
- `agent/pipeline.py` → pass through

**Why MVP:** This is the simplest way to let users scope what they test. It's just filtering — no new data model.

#### B. Remove legacy Python suite files

Delete `clean_duckdb.py`, `clean_snowflake.py`, `contextual_snowflake.py`, `clean_sqlite.py`. The YAML definitions are the canonical source. Update `skills/add-platform/SKILL.md` to reference YAML.

**Why MVP:** Eliminates contributor confusion. One path, one pattern.

#### C. Validate requirement keys in suite loader

In `loader.py`, after loading `requirements_registry.yaml`, check that every test's `requirement` key exists in the registry. Warn (not error) so existing suites aren't broken.

**Why MVP:** Prevents silent drift between suites and the registry.

#### D. Assessment profile in context YAML

Let users define their preferences in the context file:

```yaml
# ~/.aird/context.yaml
assessment_profile:
  factors: [clean, contextual]
  requirements:
    include: [null_rate, duplicate_rate, primary_key_defined]
  workload: rag
```

When `--context` is provided and contains `assessment_profile`, the pipeline applies these filters automatically. CLI flags override context.

**Why MVP:** Users with recurring assessments don't want to re-specify flags every time. This is where "what I personally want to test" lives.

---

### What to Change — Future (multi-platform + ecosystem)

#### E. Test tags and profiles

Add optional `tags` to test definitions:

```yaml
- id: null_rate
  factor: clean
  requirement: null_rate
  tags: [essential, quick]
  query_template: ...
```

CLI: `--tags essential` or `--profile quick` (where profiles are named tag sets).

#### F. Multi-platform benchmark with unified profiles

`aird benchmark -c snowflake://... -c duckdb://... --profile quick` runs the same logical requirements against both, using each platform's suite for the SQL.

This requires the test model to distinguish **logical requirement** (platform-agnostic) from **test implementation** (platform-specific SQL). The current `requirement` key already serves this role — the same `null_rate` requirement exists in both `clean_snowflake.yaml` and `clean_common.yaml` with different SQL. The benchmark command just needs to resolve each connection's suite independently and align results by requirement key — **no architectural change needed**.

#### G. Contributor tooling

- `aird validate-suite <path.yaml>` — validate a suite file against the registry
- Update `CONTRIBUTING.md` with step-by-step guide
- Add a `examples/` directory with a template suite YAML

---

### Summary: What's Blocking vs. What's Positioned Well

| Area | Status | Action |
|------|--------|--------|
| Suite YAML + composition | ✅ Good | Keep |
| Platform registry | ✅ Good | Keep |
| Requirements registry | ✅ Good | Add validation in loader |
| User test selection | ❌ Missing | Add multi-factor, requirement filter, context profile |
| Legacy Python suites | ⚠️ Confusing | Remove |
| Contributor docs | ⚠️ Stale | Update CONTRIBUTING.md and add-platform SKILL |
| Test tags/profiles | ⏳ Future | Not needed for MVP |
| Multi-platform benchmark | ⏳ Future | Architecture already supports it (requirement keys align) |

---

## Proposed Tasks

### Task 1: Multi-factor and requirement filtering
Add `--factor clean,contextual` (comma-separated) and `--requirement null_rate` filtering to the CLI and test runner.

**Scope:**
- `agent/run.py` → `expand_tests()`: accept `factor_filter` as `Optional[list[str]]` and add `requirement_filter: Optional[list[str]]`
- `agent/config.py` → add `requirement_filter` field
- `agent/cli.py` → add `--requirement` flag, change `--factor` to accept comma-separated
- `agent/pipeline.py` → pass through new filter params

### Task 2: Remove legacy Python suite files
Delete `clean_duckdb.py`, `clean_snowflake.py`, `contextual_snowflake.py`, `clean_sqlite.py`. Update any imports, docstrings, or skills that reference them.

### Task 3: Validate requirement keys in suite loader
In `agent/suites/loader.py`, after loading, check that every test's `requirement` key exists in `requirements_registry.yaml`. Emit a warning (not an error) for unknown keys.

### Task 4: Assessment profile in context YAML
Support `assessment_profile` in the context YAML file. When loaded, apply as default filters (factors, requirements, workload). CLI flags override context.

### Task 5: Update contributor documentation
Update `CONTRIBUTING.md` with actionable guides for adding a suite (YAML) and adding a platform. Update `skills/add-platform/SKILL.md` to reference YAML pattern.

---

## Acceptance Criteria

- [ ] Users can filter assessments by multiple factors (`--factor clean,contextual`)
- [ ] Users can filter by specific requirements (`--requirement null_rate`)
- [ ] Users can save their preferred test selection in context YAML
- [ ] Legacy Python suite files are removed; YAML is the single path
- [ ] Suite loader warns on unknown requirement keys
- [ ] CONTRIBUTING.md has actionable guides for adding suites and platforms
- [ ] All existing tests pass after changes

## Non-goals

- Multi-platform benchmark in a single command (future)
- Test tags/profiles (future)
- Plugin system for external suites (future)
- HTML/dashboard reports (future)

## Verification Plan

1. `python -m pytest tests/ -x` — full test suite passes
2. `aird suites` — lists all expected suites
3. `aird assess -c duckdb://:memory: --dry-run` — baseline behavior unchanged
4. `aird assess -c duckdb://:memory: --factor clean --dry-run` — only clean tests
5. `aird assess -c duckdb://:memory: --factor clean,contextual --dry-run` — (new) both factors
6. `aird assess -c duckdb://:memory: --requirement null_rate --dry-run` — (new) single requirement

## Rollback Plan

All changes are additive filters and file removals. To rollback:
- Revert the `--requirement` / multi-factor commits
- Restore deleted Python suite files from git history
- Context profile is opt-in; removing it has no side effects
