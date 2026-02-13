# AI-Ready Data Assessment CLI

The `aird` CLI is a Python tool that automates the AI-ready data assessment workflow. It handles discovery, test execution, scoring, reporting, storage, and comparison.

**The CLI is strictly read-only.** It never creates, modifies, or deletes anything in your data source. For SQL platforms, only `SELECT`, `DESCRIBE`, `SHOW`, `EXPLAIN`, and `WITH` are allowed; validation is enforced before execution.

## Quick Start

Requires **Python 3.9+**.

```bash
# Install the package (DuckDB is included)
pip install -e .

# Optional: Snowflake
pip install -e ".[snowflake]"

# Interactive setup wizard (first-time users)
aird init

# Run the assessment
aird assess -c "duckdb://:memory:" -o markdown
```

**Verify setup** (no credentials; run when you first land):

```bash
python scripts/verify_setup.py
```

**Full E2E with sample data:**

```bash
python scripts/verify_setup.py --write-files
aird assess -c "duckdb://sample.duckdb" -o markdown
```

Step-by-step checklist: [docs/E2E-from-GitHub.md](../docs/E2E-from-GitHub.md).

## How It Works

1. **Connect** — Point at your database (connection string or `AIRD_CONNECTION_STRING`). Snowflake users can use `snowflake://connection:NAME` to reuse `~/.snowflake/connections.toml`.
2. **Discover** — Enumerates schemas, tables, and columns.
3. **Generate** — Tests are generated from the selected suite and inventory.
4. **Execute** — Queries run against your data source (read-only), producing measurements.
5. **Score** — Measurements compared against thresholds at all three workload levels (L1, L2, L3).
6. **Report** — A scored report grouped by factor shows where you stand and what to fix.
7. **Save** — Results stored locally in SQLite (`~/.aird/assessments.db`) for history and diffing.

## Built-in Suites

Test suites are YAML-defined and auto-discovered from `cli/suites/definitions/`:

| Suite | Platform | Tests | Factors | Notes |
|-------|----------|-------|---------|-------|
| `common` | DuckDB | 6 | Clean | ANSI SQL + information_schema |
| `common_sqlite` | SQLite | 6 | Clean | SQLite-compatible (sqlite_master, pragma table_info) |
| `clean_snowflake` | Snowflake | 6 | Clean | Snowflake-native SQL via information_schema |
| `contextual_snowflake` | Snowflake | 4 | Contextual | PK, FK, semantic model, temporal scope |
| `common_snowflake` | Snowflake | 10 | Clean + Contextual | Composed suite (extends clean + contextual) |

The suite is auto-detected from your connection. Or specify it: `--suite common`, `--suite common_sqlite`, or `--suite common_snowflake`. Suites support composition via `extends` in YAML.

## Platforms

Built-in support for **DuckDB** and **SQLite** (no extra driver). Additional platforms (e.g. Snowflake) can be added via the platform registry.

Connection string formats and driver install: [skills/cli/references/platforms.md](../skills/cli/references/platforms.md).

## Commands

```bash
# Interactive setup wizard
aird init

# One-shot full pipeline
aird assess -c "duckdb://:memory:" -o markdown

# Interactive mode (guided scope selection)
aird assess -c "duckdb://file.duckdb" -i

# Filter to a single factor
aird assess -c "duckdb://file.duckdb" --factor clean

# Dry run (preview tests without executing)
aird assess -c "duckdb://file.duckdb" --dry-run

# Composable: discover → run → report → save
aird discover -c "duckdb://file.duckdb" -o inventory.json
aird run -c "duckdb://file.duckdb" --inventory inventory.json -o results.json
aird report --results results.json -o report.md
aird save --report report.json

# View assessment history
aird history

# Generate remediation scripts from failed tests
aird fix --dry-run
aird fix -o ./remediation

# List available suites
aird suites

# Compare two reports (by id or file)
aird diff <id1> <id2>

# Side-by-side comparison of two tables
aird compare

# Re-run failed tests from most recent assessment
aird rerun -c "duckdb://file.duckdb"

# Benchmark: compare multiple datasets
aird benchmark -c "duckdb://db1.duckdb" -c "duckdb://db2.duckdb"
```

Full command reference: [skills/cli/references/cli-commands.md](../skills/cli/references/cli-commands.md). CLI spec: [docs/specs/cli-spec.md](../docs/specs/cli-spec.md).
