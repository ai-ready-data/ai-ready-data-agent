# CLI commands quick reference

Invoke as `aird` or `python -m agent.cli`. If `aird` is not on PATH, use `python -m agent.cli` instead. Full spec: [docs/specs/cli-spec.md](../../docs/specs/cli-spec.md).

| Command | Purpose | Main flags |
|---------|---------|------------|
| **assess** | Full pipeline: discover → run → report → [save] → output. Takes a single connection via `-c`. | `-c`, `-o`, `--no-save`, `--compare`, `--dry-run`, `--context`, `--suite`, `-i`/`--interactive`, `--audit`, `--factor`, `--survey`, `--survey-answers`, `--workload`, `--thresholds`, `-s`/`--schema`, `-t`/`--tables` |
| **discover** | Connect and list schemas, tables, columns; output inventory | `-c`, `-o`, `-s`/`--schema`, `-t`/`--tables`, `--context`, `--inventory` |
| **run** | Run tests from an inventory; output results | `-c`, `--inventory`, `-o`, `--results`, `--suite`, `--thresholds`, `--context`, `--dry-run`, `--audit` |
| **report** | Build report from results, or re-output a saved report | `--results`, `--inventory`, `--thresholds`, `--context`, `--id`, `-o` |
| **save** | Persist report to history; output assessment id | `--report` (path or `-` for stdin) |
| **history** | List saved assessments | `--connection` (filter), `-n`/`--limit` |
| **diff** | Compare two reports | `<id1> <id2>` or `--left <path> --right <path>` |
| **suites** | List available test suites | (none) |
| **init** | Interactive setup wizard for first-time users | (none) |
| **compare** | Compare assessment results for two tables side-by-side (uses most recent assessment) | `-c`, `--tables`, `--suite`, `--thresholds`, `--no-save` |
| **rerun** | Re-run failed tests from most recent assessment; show improvement delta | `-c`, `--id`, `--thresholds`, `--no-save` |
| **benchmark** | N-way dataset comparison across multiple connections | `-c` (repeatable, ≥2 required), `--label`, `--suite`, `--factor`, `--thresholds`, `--save`, `--list` |

**Common env:** `AIRD_CONNECTION_STRING`, `AIRD_CONTEXT`, `AIRD_OUTPUT`, `AIRD_DB_PATH`, `AIRD_LOG_LEVEL`, `AIRD_AUDIT`, `AIRD_THRESHOLDS`.
