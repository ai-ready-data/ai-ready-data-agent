# Skills

Portable, agent-agnostic knowledge and workflows for AI-Ready Data assessment. This directory is the **single source of truth** for the assessment framework — factor definitions, thresholds, SQL, remediation patterns, and workflow guidance.

## Architecture

```
ai-ready-data-agent/
├── AGENTS.md                 # Agent playbook — start here
├── definitions/
│   ├── questions.yaml        # Discovery question manifest (M1)
│   ├── context-sample.yaml   # Annotated context file example (M2)
│   └── workflow.yaml         # Assessment step manifest — inputs, outputs, stops (M3)
├── docs/
│   └── specs/
│       ├── context-spec.md       # context.yaml schema reference (M2)
│       └── project-structure-spec.md  # Project directory convention (M5)
├── projects/
│   └── sample/               # Example project with sample artifacts (M5)
│       ├── context.yaml
│       ├── reports/
│       └── remediation/
└── skills/
    ├── SKILL.md              # Universal entry point (no CLI dependency)
    ├── audit/                # Audit logging (optional)
    │   ├── SKILL.md
    │   ├── schema.sql
    │   └── queries.md
    ├── factors/              # Factor definitions: requirements, thresholds, SQL, remediation
    ├── platforms/            # Platform-specific SQL patterns and connection details
    ├── workflows/            # Step-by-step workflow guides (discover, assess, interpret, remediate)
    └── README.md             # You are here
```

### Portable Knowledge

Self-contained markdown files with everything an agent needs to assess data: factor definitions, numeric thresholds, assessment SQL, interpretation rules, and remediation patterns. No CLI, no Python, no package install required. Any agent that can execute SQL can follow these skills.

- **`factors/`** — Single source of truth for each factor. Requirements, thresholds, assessment SQL, interpretation, remediation, and stack capabilities.
- **`platforms/`** — Platform-specific SQL patterns, connection details, and dialect notes.
- **`workflows/`** — Step-by-step workflow guides: discover, assess, interpret, remediate.
- **`audit/`** — Optional audit logging to a local SQLite database.

### CLI Orchestration (separate repo)

For agents with the `aird` CLI installed, see the [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repo. It provides shell commands that automate the workflow, plus CLI-specific agent skills that reference this directory for domain knowledge.

## How to Use

### As an agent (any runtime)

1. Start at [SKILL.md](SKILL.md)
2. Load the factor skills from [factors/](factors/) and platform skills from [platforms/](platforms/)
3. Follow the workflow in [workflows/](workflows/)

### As an agent with the aird CLI

1. Install `aird` from the [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repo
2. Follow CLI-specific skills in that repo for each workflow step
3. Load [factors/](factors/) from this repo for domain knowledge when interpreting results or generating remediation

### As a human

1. Read [factors/README.md](factors/README.md) for the threshold quick reference
2. Read individual factor files for full requirements, SQL, and remediation patterns

## Adding a New Platform

To add support for a new database platform (e.g., PostgreSQL, BigQuery):

1. **Create `platforms/{platform}.md`** with:
   - Connection patterns
   - Key information_schema views (or equivalent)
   - Important columns by view
   - SQL dialect notes (quoting, casting, date functions)
   - Required permissions

2. **Verify factor SQL works** — Each factor in `factors/` uses `{schema}`, `{table}`, `{column}` placeholders. Review the assessment SQL for dialect compatibility. If the platform uses different syntax (e.g., BigQuery backticks vs double quotes), document the differences in your platform file.

## Forking for a New Domain

This skill structure is designed to be replicable for other assessment domains. To build a new assessment agent (e.g., "security readiness", "cost optimization"):

1. **Fork the `skills/` directory structure**
2. **Replace `factors/`** with your domain factors:
   - Follow the same template: Definition, Why It Matters, Requirements (metric table), Assessment SQL, Interpretation, Remediation, Stack Capabilities
   - Define your own L1/L2/L3 equivalents (or use different levels)
3. **Write `platforms/`** for your target platforms
4. **Keep `workflows/`** mostly as-is — the discover/assess/interpret/remediate pattern is universal

The key insight: domain knowledge lives in `factors/` and `platforms/`. The workflow is generic. An agent reads the skills, understands what to check, runs the queries, and interprets the results.
