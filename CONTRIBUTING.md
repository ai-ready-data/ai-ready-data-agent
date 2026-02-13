# Contributing

Contributions that align with the project spec and factor spec are welcome.

## Adding a platform

To add support for a new database platform (e.g., PostgreSQL, BigQuery):

1. Create `skills/platforms/{platform}.md` with connection patterns, key system views, SQL dialect notes, and required permissions.
2. Verify the assessment SQL in `skills/factors/` works with the platform's SQL dialect. Factor SQL uses `{schema}`, `{table}`, `{column}` placeholders — document any dialect differences in your platform file.
3. Submit a PR with the new platform skill.

See [skills/README.md](skills/README.md) for the full guide.

## Adding or updating a factor

Factor docs live in `skills/factors/`. Each follows the template defined in [docs/specs/factor-spec.md](docs/specs/factor-spec.md): Definition, Why It Matters, Requirements (with thresholds), Assessment SQL, Interpretation, Remediation, Stack Capabilities.

## CLI contributions

The `aird` CLI tool lives in a separate repository: [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli). Platform adapters, test suites, CLI commands, and CLI-specific docs belong there.

## Specs and design

- Specifications: [docs/specs](docs/specs/)
- Design rationale and logs: [docs/log](docs/log/), [docs/designs](docs/designs/)
