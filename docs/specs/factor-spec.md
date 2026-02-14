# Factor File Specification

Defines the structure and conventions for factor definitions in `skills/factors/`.

---

## 1. Purpose

Each factor in the AI-Ready Data framework has its own directory containing separated concerns: narrative overview, structured requirements, assessment SQL, remediation SQL, and stack capabilities.

The separation enables:
- **Agents:** Parse `requirements.yaml` for structured thresholds without scanning prose
- **Renderers:** Read `assess.sql.jinja` and `remediate.sql.jinja` as templates without extracting SQL from markdown
- **Humans:** Read `overview.md` for the narrative without scrolling past SQL blocks
- **Tooling:** Validate requirements, aggregate thresholds, or generate reports programmatically

---

## 2. Directory structure

Each factor is a directory named `{N}-{factor}/` where `N` is the factor number (0-5) and `{factor}` is the lowercase factor name.

```
skills/factors/
├── README.md                       # Factor index + threshold quick reference
├── 0-clean/
│   ├── overview.md                 # Why it matters, per-workload tolerance (static prose)
│   ├── requirements.yaml           # Metric keys, thresholds, directions (structured)
│   ├── assess.sql.jinja            # Assessment SQL templates (renderable)
│   ├── remediate.sql.jinja         # Remediation SQL templates (renderable)
│   └── capabilities.md             # Stack capabilities table (static prose)
├── 1-contextual/
│   └── ...
├── 2-consumable/
│   └── ...
├── 3-current/
│   └── ...
├── 4-correlated/
│   └── ...
└── 5-compliant/
    └── ...
```

---

## 3. File specifications

### overview.md

Static prose describing the factor. Contains:

1. **Title and definition** — one-line canonical definition
2. **Why It Matters for AI** — narrative explanation
3. **Per-Workload Tolerance** — L1/L2/L3 tolerance descriptions
4. **Requirements** — table of high-level requirements (what the data must be)
5. **Tests** — table of specific measurable checks with thresholds and assessment variant descriptions
6. **Interpretation** — how to read score values

Does **not** contain SQL, execution patterns, or stack capability tables — those live in their own files. Execution patterns belong in the workflow skills (`assess.md`, `remediate.md`) or as comments in the `.sql.jinja` files.

### requirements.yaml

Machine-readable requirements and tests. Requirements are high-level properties the data must have. Tests are specific, measurable checks that verify a requirement. One requirement can have many tests.

```yaml
factor_id: 0
factor_name: Clean

requirements:
  - key: data_completeness
    name: Data completeness
    description: Data assets should not have missing values that compromise downstream consumption.
    tests:
      - key: null_rate
        description: Fraction of null values per column
        direction: lte                 # lte = lower is better, gte = higher is better
        scope: column                  # column | table | schema
        thresholds:
          L1: 0.20
          L2: 0.05
          L3: 0.01
```

**Field definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `factor_id` | integer | yes | Factor number (0-5) |
| `factor_name` | string | yes | Human-readable factor name |
| `requirements` | list | yes | List of requirement objects |
| `requirements[].key` | string | yes | Stable identifier (snake_case) |
| `requirements[].name` | string | yes | Human-readable short name |
| `requirements[].description` | string | yes | High-level description of what the data must be |
| `requirements[].tests` | list | yes | List of test objects that verify this requirement |
| `tests[].key` | string | yes | Stable test identifier. Used in results DB, audit log, reports. Matches block name in `assess.sql.jinja`. |
| `tests[].description` | string | yes | What this specific test measures |
| `tests[].direction` | enum | yes | `lte` (lower is better) or `gte` (higher is better) |
| `tests[].scope` | enum | yes | `column`, `table`, or `schema` |
| `tests[].thresholds` | object | yes | Keys: `L1`, `L2`, `L3`. Values: numeric thresholds. |

### assess.sql.jinja

Jinja2-templated assessment SQL. One named block per test key (matching `tests[].key` in `requirements.yaml`).

```sql
{# --- null_rate (per column) --- #}
{# Test for requirement: data_completeness #}
{% block null_rate %}
SELECT
  '{{ column }}' AS column_name,
  COUNT_IF({{ column }} IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS value
FROM {{ database }}.{{ schema }}.{{ table }}
{% endblock %}
```

**Conventions:**
- Template variables use double-brace Jinja2 syntax: `{{ database }}`, `{{ schema }}`, `{{ table }}`, `{{ column }}`
- Each test key gets its own named `{% block %}`
- Block names match `tests[].key` from `requirements.yaml`
- Variants (e.g. sampled) use the pattern `{test_key}_{variant}` (e.g. `null_rate_sampled`)
- Diagnostic/helper queries go after the test blocks, prefixed with `diag_`
- Platform is assumed to be Snowflake unless the block name includes a platform suffix

### remediate.sql.jinja

Jinja2-templated remediation SQL. Block names reference test keys from `requirements.yaml`.

```sql
{# --- null_rate: fill with default --- #}
{% block null_rate_fill %}
UPDATE {{ database }}.{{ schema }}.{{ table }}
SET {{ column }} = '{{ default_value }}'
WHERE {{ column }} IS NULL;
{% endblock %}

{# --- null_rate: add NOT NULL constraint --- #}
{% block null_rate_not_null %}
ALTER TABLE {{ database }}.{{ schema }}.{{ table }}
ALTER COLUMN {{ column }} SET NOT NULL;
{% endblock %}
```

**Conventions:**
- Block names follow the pattern: `{test_key}_{variant}`
- Multiple remediation options for the same test use different variant suffixes
- Include a brief comment above each block explaining what it does

### capabilities.md

Static markdown table documenting what platform features support this factor. Lists concrete platform capabilities (features, SQL commands, views) — not requirements or aspirational properties.

---

## 4. Backward compatibility

The original single-file factors (`0-clean.md`, `1-contextual.md`, etc.) are removed and replaced by the directory structure. All references in `AGENTS.md`, `skills/README.md`, workflow files, and `definitions/workflow.yaml` use the `skills/factors/{N}-{factor}/` path pattern.

Agents that previously loaded a single factor file now load the directory's `overview.md` for context and `requirements.yaml` for thresholds. The SQL templates in `assess.sql.jinja` and `remediate.sql.jinja` can be consumed either by extracting blocks or by reading the full file.

---

## 5. Cross-references

- **Workflow manifest:** [definitions/workflow.yaml](../../definitions/workflow.yaml) — references `skills/factors/*.md` (now `skills/factors/*/`)
- **Threshold quick reference:** [skills/factors/README.md](../../skills/factors/README.md) — aggregates all thresholds from `requirements.yaml` files
- **Assessment workflow:** [skills/workflows/assess.md](../../skills/workflows/assess.md) — loads factor directories
- **Interpretation workflow:** [skills/workflows/interpret.md](../../skills/workflows/interpret.md) — reads requirements for thresholds
- **Remediation workflow:** [skills/workflows/remediate.md](../../skills/workflows/remediate.md) — reads remediation templates
