# Test Suite Specification

This document defines the YAML schema for declarative test suite definitions and the composition model.

---

## 1. Purpose

- **Declarative suites:** Simple tests are defined in YAML; complex logic remains in Python.
- **Auto-discovery:** Suites in `agent/suites/definitions/*.yaml` are loaded automatically.
- **Composition:** Suites can extend other suites via `extends`.
- **Validation:** Requirement keys must match `agent/requirements_registry.yaml`.

---

## 2. YAML schema per file

### 2.1 Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suite_name` | string | yes | Name to register (e.g. `common`, `common_sqlite`, `common_snowflake`) |
| `platform` | string | no | Informational (e.g. `duckdb`, `snowflake`) |
| `extends` | list of strings | no | Suite names whose tests are merged first. Load order matters: parent suites must be loaded before children |
| `tests` | list | yes* | List of test definitions. May be empty when `extends` is set |

\* If `extends` is non-empty, `tests` may be empty. Otherwise `tests` must be non-empty.

### 2.2 Test definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique test identifier (e.g. `null_rate`, `duplicate_rate`) |
| `factor` | string | yes | Factor (e.g. `clean`, `contextual`) |
| `requirement` | string | yes | Must match a key in `requirements_registry.yaml` |
| `target_type` | string | yes | `platform`, `table`, or `column` |
| `query` | string | one of | Fixed SQL (no placeholders). Mutually exclusive with `query_template` |
| `query_template` | string | one of | SQL with `{schema_q}`, `{table_q}`, `{column_q}` placeholders. Mutually exclusive with `query` |

### 2.3 Placeholders

- `{schema_q}` — quoted schema identifier (platform-specific)
- `{table_q}` — quoted table identifier
- `{column_q}` — quoted column identifier (for column-level tests)

The test runner expands these per target (table, column) when generating concrete queries.

---

## 3. Composition (extends)

Suites can compose from other suites:

```yaml
suite_name: common_snowflake
platform: snowflake
extends:
  - clean_snowflake
  - contextual_snowflake
tests: []
```

- Parent suites must be loaded before the child (files are loaded in sorted order).
- Circular dependencies raise an error.
- Tests from parents are merged, then the current file's own tests are appended.

---

## 4. Example: minimal suite

```yaml
suite_name: common
platform: duckdb

tests:
  - id: clean_table_count
    factor: clean
    requirement: table_discovery
    query: SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    target_type: platform

  - id: null_rate
    factor: clean
    requirement: null_rate
    query_template: SELECT COUNT(*) FILTER (WHERE {column_q} IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v FROM {schema_q}.{table_q}
    target_type: column
```

---

## 5. Python suites

Complex tests (custom logic, dynamic queries, platform-specific behavior) remain in Python modules. Python suites register via `register_suite(name, tests)` on import. The loader does not auto-discover Python modules; they are imported explicitly by platform adapters or `__init__.py` as needed.

---

## 6. Adding a new suite

1. Create `agent/suites/definitions/<name>.yaml`.
2. Define `suite_name`, `platform`, and `tests`.
3. Ensure every `requirement` key exists in `agent/requirements_registry.yaml`.
4. Run `aird suites` to verify the suite is registered.
