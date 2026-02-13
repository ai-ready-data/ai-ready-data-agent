# Context File Specification

Defines the schema for the assessment context file (`context.yaml`) — the persisted output of the discovery workflow.

---

## 1. Purpose

The context file captures every decision made during discovery: platform, workload level, scope, exclusions, data products, and factor selection. It is the single artifact that makes an assessment **repeatable** — any agent runtime can read it and produce the same assessment without re-asking the user.

**Use cases:**
- Re-run the same assessment later (same scope, same thresholds)
- Compare assessments over time (same context, different results)
- Share assessment configuration across team members
- Hand off from one agent runtime to another (e.g. Cortex Code to CLI)

---

## 2. File location

Context files live in project directories (see M5 in the milestone plan) or alongside the assessment:

```
projects/<project-name>/context.yaml
```

Or for standalone use:

```
~/.snowflake/cortex/aird-context.yaml
```

The CLI also accepts `--context <path>` or the `AIRD_CONTEXT` environment variable.

---

## 3. Schema

Keys correspond 1:1 to `answer_title` values in [definitions/questions.yaml](../../definitions/questions.yaml). The context file is the "answer file" for the discovery workflow.

### Required fields

| Key | Type | Description |
|-----|------|-------------|
| `platform` | string | Database platform. One of: `Snowflake`, `DuckDB`, `PostgreSQL`, `SQLite`, `BigQuery`, `Databricks`, `Redshift`, `Other`. |
| `target_workload` | string | Workload level. One of: `L1`, `L2`, `L3`. |
| `database` | string | Database name to assess. |
| `schemas` | list of strings | Schemas in scope. |
| `factor_scope` | string or list | `all` or list of factor names (e.g. `["0: Clean", "3: Current"]`). |

### Optional fields

| Key | Type | Description |
|-----|------|-------------|
| `data_products` | list of objects | Named groups of tables. Each has `name` (string, required), `schemas` (list, required), `owner` (string, optional), `target_workload` (string, optional override). |
| `excluded_schemas` | list of strings | Schemas to skip. |
| `tables` | list of strings | Specific tables to exclude. If omitted, all tables in `schemas` are assessed. |
| `critical_tables` | list of strings | Tables to prioritize in reporting. |
| `infrastructure_tools` | list of strings | Tools in the stack (dbt, catalog, Iceberg, etc.). Informational — helps interpretation. |
| `pain_points` | string | What prompted the assessment. Informational — helps prioritization. |

### Metadata fields

These are written by the agent, not provided by the user.

| Key | Type | Description |
|-----|------|-------------|
| `created_at` | string | ISO 8601 timestamp, UTC. When the context file was created. |
| `created_by` | string | Agent or tool that created the file (e.g. `cortex-code`, `cursor`, `aird-cli`). |
| `questions_version` | string | Git SHA or version of `definitions/questions.yaml` used. Enables forward compatibility — if questions change, you know which version produced this context. |

---

## 4. Serialization rules

- **Format:** YAML.
- **Encoding:** UTF-8.
- **Comments:** Allowed. Agents should add a header comment with the project name, creation date, and a note that keys match `definitions/questions.yaml`.
- **Null values:** Omit optional keys rather than writing `null`. Presence of a key implies the user provided a value.
- **Lists:** Use YAML flow style (`[A, B, C]`) or block style (`- A\n- B\n- C`). Both are valid.
- **Workload level:** Store the short name only (`L1`, `L2`, `L3`), not the full description.
- **Factor scope:** Store `all` (string) or a list of factor identifiers.

---

## 5. Validation

A context file is **valid** if all required fields are present and non-empty. A context file is **complete** if all optional fields relevant to the user's answers are also present.

An agent or tool should validate before starting the assess phase:

1. `platform` is a recognized value
2. `target_workload` is one of `L1`, `L2`, `L3`
3. `database` is non-empty
4. `schemas` has at least one entry
5. `factor_scope` is `all` or a non-empty list of valid factor names
6. If `data_products` is present, each entry has `name` and `schemas`

Validation failures should be reported with the missing field name and what's needed, not silently defaulted.

---

## 6. Example

```yaml
# AI-Ready Data Assessment Context
# Project: customer-360-prod
# Created: 2026-02-13T14:30:00Z
# Agent: cortex-code
# Keys match definitions/questions.yaml answer_title values

created_at: "2026-02-13T14:30:00Z"
created_by: cortex-code

# --- Phase 1: Pre-connect ---
platform: Snowflake
target_workload: L2
data_products:
  - name: customer_360
    schemas: [ANALYTICS.CUSTOMERS, ANALYTICS.ORDERS, ANALYTICS.INTERACTIONS]
    owner: data-eng
  - name: event_stream
    schemas: [RAW.EVENTS, TRANSFORM.EVENTS_ENRICHED]
    owner: platform-team
    target_workload: L3
excluded_schemas: [STAGING, SCRATCH, TEST, _INTERNAL]
infrastructure_tools: [dbt, Apache Iceberg]
pain_points: "Deploying a RAG pipeline next month, need to validate data quality"

# --- Phase 3: Post-discovery ---
database: ANALYTICS_PROD
schemas: [ANALYTICS, RAW, TRANSFORM]
critical_tables: [ANALYTICS.CUSTOMERS, ANALYTICS.ORDERS, RAW.EVENTS]
factor_scope: all
```

A minimal valid context file:

```yaml
created_at: "2026-02-13T14:30:00Z"
created_by: cortex-code
platform: Snowflake
target_workload: L2
database: ANALYTICS_PROD
schemas: [ANALYTICS]
factor_scope: all
```

---

## 7. Relationship to other artifacts

| Artifact | Relationship |
|----------|-------------|
| `definitions/questions.yaml` | Context file keys are the `answer_title` values from this manifest. |
| `aird-results.db` (SQLite) | Assessment results reference the context via `session_id`. The context file captures *what* was assessed; the results database captures *how it scored*. |
| `aird-audit.jsonl` | The `start` event logs `platform` and `workload` from the context. The context file is the full record; the audit log is the operational trail. |
| `projects/<name>/` | Context file is the anchor artifact in a project directory. |
