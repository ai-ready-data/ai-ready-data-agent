# Requirements Registry Specification

This document defines the canonical schema for `agent/requirements_registry.yaml`, the single source of truth for requirement keys, their metadata, and default L1/L2/L3 thresholds.

---

## 1. Purpose

- **Single source of truth:** All requirement keys used by test suites must be defined in the registry.
- **Threshold defaults:** Each requirement has default thresholds per workload level (L1=analytics, L2=RAG, L3=training).
- **Direction:** Each requirement specifies whether lower is better (`lte`) or higher is better (`gte`).
- **Validation:** The suite loader validates that every test's `requirement` field matches a registry key.

---

## 2. Schema

The registry is a YAML mapping at the top level. Each key is a requirement identifier (e.g. `null_rate`, `primary_key_defined`).

### 2.1 Per-requirement structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable name (e.g. "Null Rate") |
| `description` | string | yes | Brief description of what the requirement measures |
| `factor` | string | yes | Factor this requirement belongs to (clean, contextual, etc.) |
| `direction` | string | no | `lte` (default) or `gte`. `lte` = pass when measured ≤ threshold (rate-of-bad). `gte` = pass when measured ≥ threshold (coverage) |
| `default_thresholds` | object | yes | `{ l1: float, l2: float, l3: float }` — thresholds per workload level |

### 2.2 Example

```yaml
null_rate:
  name: Null Rate
  description: Fraction of null values per column. Lower is better.
  factor: clean
  direction: lte
  default_thresholds: {l1: 0.2, l2: 0.05, l3: 0.01}

primary_key_defined:
  name: Primary Key Defined
  description: Fraction of tables with a declared primary key constraint. Higher is better.
  factor: contextual
  direction: gte
  default_thresholds: {l1: 0.5, l2: 0.8, l3: 0.95}
```

---

## 3. Threshold direction

- **`lte` (default):** Pass when `measured_value <= threshold`. Used for rate-of-bad metrics (null_rate, duplicate_rate, format_inconsistency_rate).
- **`gte`:** Pass when `measured_value >= threshold`. Used for coverage metrics (primary_key_defined, semantic_model_coverage).

---

## 4. User overrides

Users may override thresholds via `--thresholds path/to/thresholds.json`. The JSON shape:

```json
{
  "null_rate": { "l1": 0.01, "l2": 0.01, "l3": 0.01 },
  "primary_key_defined": { "direction": "gte", "l1": 0.6 }
}
```

Overrides merge on top of registry defaults. `direction` may also be overridden per requirement.

---

## 5. Special requirements

- **`table_discovery`:** Informational; always passes. Used for platform-level tests that report table count.
- Placeholder requirements (e.g. `serving_capability`, `freshness_metadata`) may use `1.0` thresholds until implemented.

---

## 6. CLI

The `aird requirements` command lists all registered requirements with their metadata and default thresholds.
