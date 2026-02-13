# Skills

Portable, agent-agnostic knowledge and workflows for AI-Ready Data assessment. This directory is the **single source of truth** for the assessment framework — factor definitions, thresholds, SQL, remediation patterns, and workflow guidance.

## Architecture

```
skills/
├── SKILL.md              # Universal entry point (no CLI dependency)
├── audit/                # Audit logging (optional)
│   ├── SKILL.md          # Setup and logging instructions
│   ├── schema.sql        # SQLite schema
│   └── queries.md        # Analysis queries
├── factors/              # Factor definitions: requirements, thresholds, SQL, remediation
├── platforms/            # Platform-specific SQL patterns and connection details
├── workflows/            # Step-by-step workflow guides (discover, assess, interpret, remediate)
├── cli/                  # CLI orchestration layer (for aird CLI users)
│   ├── SKILL.md          # CLI entry point
│   └── references/       # CLI-specific references
└── README.md             # You are here
```

### Three-Layer Design

**Layer 1: Portable knowledge** (`skills/factors/`, `skills/platforms/`, `skills/workflows/`)

Self-contained markdown files with everything an agent needs to assess data: factor definitions, numeric thresholds, assessment SQL, interpretation rules, and remediation patterns. No CLI, no Python, no package install required. Any agent that can execute SQL can follow these skills.

**Layer 2: CLI orchestration** (`skills/cli/`)

For agents with the `aird` CLI available. Provides shell commands that automate the workflow from Layer 1. References Layer 1 for domain knowledge — never duplicates thresholds, SQL, or remediation patterns.

**Layer 3: Audit logging** (`skills/audit/`)

**Enabled by default.** Logs all assessment activity (sessions, commands, queries, results) to a local SQLite database at `~/.snowflake/cortex/aird-audit.db`. Useful for history, debugging, compliance, and tracking improvement over time. Disable with `--no-audit` if needed.

## How to Use

### As an agent (any runtime)

1. Start at [SKILL.md](SKILL.md)
2. Load the factor skills from [factors/](factors/) and platform skills from [platforms/](platforms/)
3. Follow the workflow in [workflows/](workflows/)

### As an agent with the aird CLI

1. Start at [cli/SKILL.md](cli/SKILL.md)
2. Follow CLI-specific commands for each workflow step
3. Load [factors/](factors/) for domain knowledge when interpreting results or generating remediation

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

3. **Optionally add CLI support** — If you have a CLI, add a platform adapter. See the existing adapters in `agent/platform/` for the pattern (connection parsing, PEP 249 interface, suite registration).

## Forking for a New Domain

This skill structure is designed to be replicable for other assessment domains. To build a new assessment agent (e.g., "security readiness", "cost optimization"):

1. **Fork the `skills/` directory structure**
2. **Replace `factors/`** with your domain factors:
   - Follow the same template: Definition, Why It Matters, Requirements (metric table), Assessment SQL, Interpretation, Remediation, Stack Capabilities
   - Define your own L1/L2/L3 equivalents (or use different levels)
3. **Write `platforms/`** for your target platforms
4. **Keep `workflows/`** mostly as-is — the discover/assess/interpret/remediate pattern is universal
5. **Optionally add `cli/`** if you build a CLI execution layer

The key insight: domain knowledge lives in `factors/` and `platforms/`. The workflow is generic. An agent reads the skills, understands what to check, runs the queries, and interprets the results.
