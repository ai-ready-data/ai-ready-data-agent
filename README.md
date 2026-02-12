# The AI-Ready Data Framework

**Six factors that determine whether your data can reliably power AI systems.**

An open standard defining what "AI-ready data" actually means, plus an assessment agent that turns the definition into executable, red/green test suites against your data infrastructure.

## Background

The contributors to this project include practicing data engineers, ML practitioners, and platform architects who have built and operated AI systems across industries. This document synthesizes our collective experience building data systems that power reliable and trustworthy AI systems.

The format is inspired by Martin Fowler's work on defining technical patterns, the 12-Factor App methodology, and the 12 Factor Agent.

## Who Should Read This

* **Data engineers** deploying pipelines that power AI systems.
* **Platform teams** designing infrastructure for ML and AI workloads.
* **Architects** evaluating whether their stack can support RAG, agents, or real-time inference.
* **Data leaders** who need to assess organizational AI readiness and communicate gaps to their teams.
* **Coding agents** building the infrastructure they'll eventually consume.

## Quick Start

Requires **Python 3.9+**.

```bash
# Clone and enter the repo
git clone https://github.com/ai-ready-data/ai-ready-data-agent.git
cd ai-ready-data-agent

# Install the package (DuckDB is included)
pip install -e .

# Optional: Snowflake — pip install -e ".[snowflake]"

# Interactive setup wizard (first-time users)
aird init

# Run the assessment
aird assess -c "duckdb://:memory:"
# Or with a file: aird assess -c "duckdb://path/to/file.duckdb" -o markdown
# Or with env: export AIRD_CONNECTION_STRING="duckdb://path/to/file.duckdb" && aird assess
# Interactive mode (guided scope selection): aird assess -c "duckdb://file.duckdb" -i
# Dry run (preview tests without executing): aird assess -c "duckdb://file.duckdb" --dry-run
```

**Verify setup** (no credentials; run when you first land):

```bash
python scripts/verify_setup.py
```

**Full E2E with sample data** (clone → install → verify → assess):

```bash
git clone https://github.com/ai-ready-data/ai-ready-data-agent.git && cd ai-ready-data-agent
pip install -e .
python scripts/verify_setup.py --write-files
aird assess -c "duckdb://sample.duckdb" -o markdown
```

**Compare datasets** (benchmark N connections side-by-side):

```bash
aird benchmark -c "duckdb://db1.duckdb" -c "duckdb://db2.duckdb"
```

Step-by-step checklist: [docs/E2E-from-GitHub.md](docs/E2E-from-GitHub.md).

Built-in support for **DuckDB** and **SQLite** (no extra driver). Additional platforms (e.g. Snowflake) can be added via the platform registry — see [docs/specs](docs/specs/) and [docs/log](docs/log/). Run `python scripts/verify_setup.py` to confirm the agent works (no credentials); use `--write-files` to create sample data for CLI runs.

## The Three Workload Levels

Whether data is "AI-ready" depends on what you're building. Different use cases have different tolerance for issues, so the framework defines three workload levels. Every requirement and threshold is scoped to a level.

| Level | Workload | Tolerance for issues | What it means |
|-------|----------|----------------------|---------------|
| **L1** | Descriptive analytics and BI | Moderate | Humans are in the loop. An analyst can spot and compensate for a missing value or an undeclared relationship. |
| **L2** | RAG and retrieval systems | Low | Any chunk of data can become a model response. Ambiguity, staleness, or missing context propagates directly to the end user. |
| **L3** | ML model training and fine-tuning | Very low | Errors are not just retrieved — they are *learned*. Bad data becomes bad weights, silently and permanently. |

Levels are ordered by **strictness of requirements**, not by maturity. L3 is not "better" than L1 — it is a different use case with stricter demands. Meeting a stricter level implies meeting the less strict ones (additivity): if your data passes at L3 for a given requirement, it passes at L2 and L1 too.

Canonical definitions and rationale: [docs/definitions.md](docs/definitions.md).

---

## What's In This Repo

### [The Factors](factors/)

The AI-Ready Data Project defines six factors of AI-ready data. Each factor has requirements at all three workload levels.

| Factor | Name | Definition |
|--------|------|-------------|
| **0** | [**Clean**](factors/factor-00-clean.md) | Accurate, complete, valid, and free of errors |
| **1** | [**Contextual**](factors/factor-01-contextual.md) | Meaning is explicit and colocated with the data |
| **2** | **Consumable** | *(to be added)* |
| **3** | **Current** | *(to be added)* |
| **4** | **Correlated** | *(to be added)* |
| **5** | **Compliant** | *(to be added)* |

Canonical definitions: [docs/definitions.md](docs/definitions.md). Factor documents conform to [docs/specs/factor-spec.md](docs/specs/factor-spec.md).

### [The Assessment Agent](agent/)

A Python CLI with purpose-built test suites. The output is a scored report showing which workload levels your data is ready for. You can assess a single database, or use `aird benchmark` to compare multiple datasets side-by-side.

**The agent is strictly read-only.** It never creates, modifies, or deletes anything in your data source. For SQL platforms, only `SELECT`, `DESCRIBE`, `SHOW`, `EXPLAIN`, and `WITH` are allowed; validation is enforced before execution.

**Built-in suites** (YAML-defined, auto-discovered from `agent/suites/definitions/`):

| Suite | Platform | Tests | Factors | Notes |
|-------|----------|-------|---------|-------|
| `common` | DuckDB | 6 | Clean | ANSI SQL + information_schema |
| `common_sqlite` | SQLite | 6 | Clean | SQLite-compatible (sqlite_master, pragma table_info) |
| `clean_snowflake` | Snowflake | 6 | Clean | Snowflake-native SQL via information_schema |
| `contextual_snowflake` | Snowflake | 4 | Contextual | primary_key_defined, semantic_model_coverage, foreign_key_coverage, temporal_scope_present |
| `common_snowflake` | Snowflake | 10 | Clean + Contextual | Composed suite (extends clean_snowflake + contextual_snowflake) |

The suite is auto-detected from your connection. Or specify it: `--suite common`, `--suite common_sqlite`, or `--suite common_snowflake`. Suites support composition via `extends` in YAML.

### [Design & Specs](docs/)

Specifications, design rationale, and architecture:

- [Project spec](docs/specs/project-spec.md) — purpose, layers, outcomes
- [CLI spec](docs/specs/cli-spec.md) — commands, artifacts, config
- [Factor spec](docs/specs/factor-spec.md) — factor document shape, requirement keys
- [Report spec](docs/specs/report-spec.md) — canonical report JSON schema and markdown rendering
- [Design log](docs/log/) — composability, architecture, analysis

## How It Works

1. **Connect** — Point the agent at your database (connection string or `AIRD_CONNECTION_STRING`). Snowflake users can use `snowflake://connection:NAME` to reuse `~/.snowflake/connections.toml`. Run `aird init` for an interactive setup wizard.
2. **Discover** — The agent enumerates schemas, tables, and columns (or use `aird discover` alone).
3. **Generate** — Tests are generated from the selected suite and inventory.
4. **Execute** — Queries run against your data source (read-only), producing measurements.
5. **Score** — Each measurement is compared against thresholds at all three workload levels (L1, L2, L3). The report tells you which levels your data is ready for.
6. **Report** — A scored report grouped by factor shows where you stand and what to fix. Report schema: [docs/specs/report-spec.md](docs/specs/report-spec.md).
7. **Save** — Results are stored locally in SQLite (`~/.aird/assessments.db` by default, or `AIRD_DB_PATH`) for history and diffing.

```bash
# Interactive setup wizard
aird init

# One-shot full pipeline (single database)
aird assess -c "duckdb://:memory:" -o markdown

# Interactive mode (guided scope selection)
aird assess -c "duckdb://file.duckdb" -i

# Filter to a single factor
aird assess -c "duckdb://file.duckdb" --factor clean

# Dry run (preview tests without executing)
aird assess -c "duckdb://file.duckdb" --dry-run

# Try the Clean factor suite (create sample files, then assess)
python scripts/verify_setup.py --write-files && aird assess -c "duckdb://sample.duckdb" -o markdown

# Composable: discover → run → report → save
aird discover -c "duckdb://file.duckdb" -o inventory.json
aird run -c "duckdb://file.duckdb" --inventory inventory.json -o results.json
aird report --results results.json -o report.md
aird save --report report.json

# View assessment history
aird history

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

## For coding agents

Start at **[AGENTS.md](AGENTS.md)** for the playbook. It outlines the workflow (interview → connect → discover → assess → interpret → remediate → compare), stopping points, and where to find the CLI, project, and skills. Sub-skills live in [skills/](skills/) with step-by-step guidance per phase. Key commands: `aird init` (setup), `aird assess` (full pipeline), `aird benchmark` (multi-dataset comparison), `aird compare`/`aird diff` (result comparison), `aird rerun` (retry failures).

## Contributing

Specs and design rationale live under [docs/specs](docs/specs/) and [docs/log](docs/log/). Contributions that align with the project spec and CLI spec are welcome.

## License

MIT
