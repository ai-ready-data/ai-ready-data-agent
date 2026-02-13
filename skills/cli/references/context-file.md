# Context file

Optional YAML file used to pass scope and overrides into the CLI. Via `--context` or `AIRD_CONTEXT`.

**Purpose:** Scope (schemas/tables to include) and optional overrides so the agent and CLI don't re-ask on every run. When set, discovery uses context **schemas** and **tables** when the manifest target does not specify them; the report includes `user_context` for the interpret step.

**YAML shape (current):**
- `schemas`: optional list of schema names (restrict discovery to these).
- `tables`: optional list of table names (e.g. `schema.table`; restrict discovery to these).

Example:
```yaml
schemas: [main, staging]
tables: [main.fact_sales]
```

**Canonical definition:** [docs/specs/cli-spec.md](../../../docs/specs/cli-spec.md) § Configuration.

**Usage:** When the user has confirmed scope in the interview, write a YAML file and pass it with `--context <path>` on assess (or discover/run in a composed flow).
