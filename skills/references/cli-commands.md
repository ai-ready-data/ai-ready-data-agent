# CLI commands quick reference

Invoke as `aird` or `python -m agent.cli`. If `aird` is not on PATH, use `python -m agent.cli` instead. Full spec: [docs/specs/cli-spec.md](../../docs/specs/cli-spec.md).

| Command | Purpose | Main flags |
|---------|---------|------------|
| **assess** | Full pipeline: discover → run → report → [save] → output. Single DB or **estate** (multiple connections → one report). | `-c` (repeatable), `--connection`, `--connections-file` (or `AIRD_CONNECTIONS_FILE`), `AIRD_CONNECTION_STRING`, `-o` (markdown \| stdout \| json:path), `--no-save`, `--compare`, `--dry-run`, `--context`, `--suite`, `-i`/`--interactive`, `--audit` |
| **discover** | Connect and list schemas, tables, columns; output inventory | `-c`, `--connection`, `-o` (stdout or path), `--schema` (repeatable), `--tables` (repeatable), `--context` |
| **run** | Run tests from an inventory; output results | `-c`, `--connection`, `--inventory` (path or `-` for stdin), `-o`, `--suite`, `--thresholds`, `--context`, `--dry-run`, `--audit` |
| **report** | Build report from results, or re-output a saved report | `--results` (path or `-`), `--id` (saved assessment id), `-o` (markdown \| stdout \| json:path) |
| **save** | Persist report to history; output assessment id | `--report` (path or `-` for stdin) |
| **history** | List saved assessments (tab-separated: id, created_at, L1%, L2%, L3%, connection_fingerprint) | `--connection` (filter), `-n`/`--limit` (default 20) |
| **diff** | Compare two reports | `<id1> <id2>` or `--left <path> --right <path>` |
| **suites** | List available test suites | (none) |

**Common env:** `AIRD_CONNECTION_STRING`, `AIRD_CONNECTIONS_FILE` (estate), `AIRD_CONTEXT`, `AIRD_OUTPUT`, `AIRD_DB_PATH`, `AIRD_LOG_LEVEL`, `AIRD_AUDIT`, `AIRD_THRESHOLDS`.
