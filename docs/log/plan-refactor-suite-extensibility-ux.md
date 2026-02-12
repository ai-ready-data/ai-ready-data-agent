# Refactor Plan: Suite Extensibility, Source of Truth, and UX Improvements

**Created:** 2026-02-12
**Status:** Planning
**Context:** Based on design review feedback and decisions to improve test suite extensibility, establish single source of truth for requirements/thresholds, remove multi-connection estate feature (defer to roadmap), and add interactive UX features.

---

## 1. Test Suite Extensibility

### 1.1 Declarative Suite Definitions

**Goal:** Move from Python-only suite definitions to declarative YAML/JSON for simpler tests, while keeping Python for complex logic.

**Current state:**
- Test suites are Python modules (`agent/suites/clean_duckdb.py`, etc.)
- Each suite manually registers itself via `register_suite()` on import
- Query templates are Python strings with placeholders

**Target state:**
- Simple tests defined in YAML files (e.g., `agent/suites/definitions/clean_common.yaml`)
- Complex tests (custom logic, dynamic queries) remain in Python
- Suite loader reads YAML and auto-registers

**Tasks:**
- [ ] Define YAML schema for test suite definitions (factor, requirement, query_template, target_type, thresholds)
- [ ] Create `agent/suites/definitions/` directory for declarative suite files
- [ ] Implement suite loader that reads YAML and registers tests
- [ ] Migrate existing simple tests (clean_duckdb, clean_sqlite) to YAML
- [ ] Keep complex tests (e.g., Snowflake semantic model checks) in Python
- [ ] Update suite registry to support both YAML and Python sources
- [ ] Document YAML schema in `docs/specs/test-suite-spec.md`

**Files to create:**
- `agent/suites/definitions/clean_common.yaml`
- `agent/suites/definitions/clean_sqlite.yaml`
- `agent/suites/definitions/clean_snowflake.yaml`
- `agent/suites/definitions/contextual_snowflake.yaml`
- `agent/suites/loader.py` (YAML suite loader)

**Files to update:**
- `agent/suites/__init__.py` (import loader, auto-discover)
- `agent/platform/registry.py` (support YAML-sourced suites)

---

### 1.2 Auto-Discovery of Suite Files

**Goal:** Automatically discover and register all suite files (YAML and Python) without manual imports.

**Current state:**
- Suite files must be explicitly imported in `agent/suites/__init__.py`
- Easy to forget to register new suites

**Target state:**
- On package init, scan `agent/suites/definitions/` for YAML files
- Scan `agent/suites/` for Python modules matching pattern (e.g., `*_suite.py`)
- Auto-register all discovered suites

**Tasks:**
- [ ] Implement auto-discovery in `agent/suites/__init__.py`
- [ ] Scan `definitions/` for `*.yaml` files
- [ ] Scan root `suites/` for Python modules (exclude `__init__.py`, `loader.py`)
- [ ] Load and register each discovered suite
- [ ] Add error handling for malformed suite files
- [ ] Log discovered suites (debug level) for troubleshooting

---

### 1.3 Suite Composition

**Goal:** Allow suites to be composed from other suites (e.g., `common_snowflake` = `clean_snowflake` + `contextual_snowflake`).

**Current state:**
- Suites are flat lists of tests
- No composition or inheritance

**Target state:**
- Suite definitions can reference other suites via `extends` or `includes` key
- Registry resolves composition and merges tests

**Tasks:**
- [ ] Add `extends` field to YAML schema (list of suite names to include)
- [ ] Update suite loader to resolve composition (recursive)
- [ ] Handle circular dependencies (error or warning)
- [ ] Update `aird suites` command to show composition tree
- [ ] Document composition in test-suite-spec.md

**Example YAML:**
```yaml
name: common_snowflake
extends:
  - clean_snowflake
  - contextual_snowflake
tests: []  # Additional tests specific to this suite
```

---

## 2. Single Source of Truth for Requirements & Thresholds

**Goal:** Ensure factor requirements, requirement keys, thresholds, and test definitions stay in sync.

**Current state:**
- Requirements defined in factor markdown files (`factors/factor-00-clean.md`)
- Requirement keys listed in factor docs
- Thresholds defined in code (`agent/thresholds.py`) and optional user config
- Test definitions in suite files reference requirement keys
- **Risk:** These can drift out of sync

**Target state:**
- **Single canonical source** for requirement keys and default thresholds
- Factor docs reference this source (or are generated from it)
- Test suites validate against canonical requirement keys
- Thresholds loaded from canonical source, overridable by user config

**Tasks:**
- [ ] Create `agent/requirements_registry.yaml` as canonical source
  - Structure: `{requirement_key: {name, description, direction, default_thresholds: {l1, l2, l3}}}`
- [ ] Update `agent/thresholds.py` to load from registry (with user override)
- [ ] Add validation in suite loader: error if test references unknown requirement key
- [ ] Update factor docs to reference or generate from registry
- [ ] Add `aird requirements` command to list all registered requirements
- [ ] Document registry schema in `docs/specs/requirements-registry-spec.md`

**Files to create:**
- `agent/requirements_registry.yaml`
- `docs/specs/requirements-registry-spec.md`

**Files to update:**
- `agent/thresholds.py` (load from registry)
- `agent/suites/loader.py` (validate requirement keys)
- `factors/factor-00-clean.md` (reference registry or note sync requirement)

---

## 3. Remove Multi-Connection/Estate Feature

**Goal:** Simplify to single-connection assessments; defer estate mode to future roadmap.

**Current state:**
- CLI supports multiple `-c` flags and `--connections-file`
- Pipeline and report support estate mode
- Adds complexity to error handling, aggregation, reporting

**Target state:**
- CLI accepts single connection only
- Remove estate-specific code paths
- Document estate feature in `docs/roadmap.md` for future implementation

**Tasks:**
- [ ] Create `docs/roadmap.md` and document estate feature as future work
- [ ] Update CLI to accept single `-c` or `AIRD_CONNECTION_STRING` only
- [ ] Remove `--connections-file` flag
- [ ] Remove estate-specific logic from `agent/pipeline.py`
- [ ] Remove `build_estate_report()` from `agent/report.py`
- [ ] Update `agent/manifest_loader.py` (if only used for estate, remove or simplify)
- [ ] Update README.md to remove estate examples
- [ ] Update skills (interview, connect, assess) to remove estate references
- [ ] Update tests to remove estate test cases
- [ ] Archive `docs/log/design-multi-connection-estate.md` (note: deferred to roadmap)

---

## 4. Interactive UX Improvements

### 4.1 Interactive Wizard (`aird init`)

**Goal:** Guided setup for first-time users to configure connection, scope, and thresholds.

**Tasks:**
- [ ] Create `aird init` command
- [ ] Prompt for platform (DuckDB, SQLite, Snowflake, other)
- [ ] Prompt for connection details (file path, connection string, env var)
- [ ] Test connection before proceeding
- [ ] Prompt for schemas to include/exclude
- [ ] Prompt for target workload level (L1, L2, L3, or all)
- [ ] Optionally create `.aird/config.yaml` with saved preferences
- [ ] Optionally run discovery preview (show table count, schema list)
- [ ] End with "Run `aird assess` to start assessment"
- [ ] Document in `docs/specs/cli-spec.md` and README

**Files to create:**
- `agent/commands/init.py` (interactive wizard logic)

**Files to update:**
- `agent/cli.py` (add `init` subcommand)
- `docs/specs/cli-spec.md` (document `init` command)
- `README.md` (add quick start with `aird init`)

---

### 4.2 Dry-Run Preview

**Goal:** Show what will be tested before running full assessment.

**Current state:**
- `run_tests()` has `dry_run=True` parameter (returns preview)
- Not exposed in CLI

**Target state:**
- `aird assess --dry-run` shows preview without executing queries
- Preview includes: test count, factors covered, sample tests, estimated runtime

**Tasks:**
- [ ] Add `--dry-run` flag to `aird assess` command
- [ ] Add `--dry-run` flag to `aird run` command
- [ ] Update pipeline to pass dry_run flag through to `run_tests()`
- [ ] Format dry-run output (table or list of tests to be run)
- [ ] Show estimated test count per factor
- [ ] Document in CLI spec and README

**Files to update:**
- `agent/cli.py` (add `--dry-run` flag)
- `agent/pipeline.py` (handle dry_run mode)
- `agent/run.py` (already supports dry_run, ensure output is user-friendly)
- `docs/specs/cli-spec.md` (document flag)

---

## 5. Implementation Order

**Phase 1: Foundation (Source of Truth)**
1. Create `agent/requirements_registry.yaml`
2. Create `docs/specs/requirements-registry-spec.md`
3. Update `agent/thresholds.py` to load from registry
4. Add validation in suite loader

**Phase 2: Declarative Suites**
5. Define YAML schema for test suites
6. Create `agent/suites/loader.py`
7. Create `agent/suites/definitions/` directory
8. Migrate existing suites to YAML
9. Implement auto-discovery
10. Implement suite composition

**Phase 3: Simplify (Remove Estate)**
11. Create `docs/roadmap.md`
12. Remove estate code from CLI, pipeline, report
13. Update docs and tests

**Phase 4: UX Improvements**
14. Implement `--dry-run` flag
15. Implement `aird init` wizard
16. Update documentation

---

## 6. Success Criteria

- [ ] All existing tests pass with new declarative suite system
- [ ] New suites can be added via YAML without touching Python code
- [ ] Requirement keys validated against canonical registry
- [ ] Estate feature removed; single-connection only
- [ ] `aird init` provides guided setup for new users
- [ ] `aird assess --dry-run` shows preview without executing
- [ ] Documentation updated to reflect all changes
- [ ] Community contribution guide includes "How to add a suite" with YAML example

---

## 7. Future Considerations (Out of Scope for This Plan)

- HTML/visualization reports
- Remediation templates
- Benchmarking and baselines
- Multi-connection estate mode (see roadmap.md)
- Performance optimization (parallel test execution)
