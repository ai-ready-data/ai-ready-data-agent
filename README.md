# The AI-Ready Data Project

**Six factors that determine whether your data can reliably power AI systems.**

An open standard defining what "AI-ready data" actually means, plus an assessment agent that turns the framework into executable, red/green test suites against your data infrastructure.

## Background

The contributors to this framework include practicing data engineers, ML practitioners, and platform architects who have built and operated AI systems across industries. This document synthesizes our collective experience building data systems that power reliable and trustworthy AI systems.

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

# Run the assessment
aird assess -c "duckdb://:memory:"
# Or with a file: aird assess -c "duckdb://path/to/file.duckdb" -o markdown
# Or with env: export AIRD_CONNECTION_STRING="duckdb://path/to/file.duckdb" && aird assess
```

**Full E2E with sample data** (clone → install → create sample DB → assess):

```bash
git clone https://github.com/ai-ready-data/ai-ready-data-agent.git && cd ai-ready-data-agent
pip install -e .
python scripts/create_sample_duckdb.py
aird assess -c "duckdb://sample.duckdb" -o markdown
```

Step-by-step checklist: [docs/E2E-from-GitHub.md](docs/E2E-from-GitHub.md).

Built-in support for **DuckDB** (ANSI SQL baseline). Additional platforms (e.g. Snowflake) can be added via the platform registry — see [docs/specs](docs/specs/) and [docs/log](docs/log/).

## What's In This Repo

### [The Factors](factors/)

The AI-Ready Data Project defines six factors of AI-ready data with requirements at three workload levels (L1: Analytics, L2: RAG, L3: Training).

| Factor | Name | Definition |
|--------|------|-------------|
| **0** | [**Clean**](factors/factor-00-clean.md) | Accurate, complete, valid, and free of errors |
| **1** | **Contextual** | *(to be added)* |
| **2** | **Consumable** | *(to be added)* |
| **3** | **Current** | *(to be added)* |
| **4** | **Correlated** | *(to be added)* |
| **5** | **Compliant** | *(to be added)* |

Canonical definitions: [docs/definitions.md](docs/definitions.md). Factor documents conform to [docs/specs/factor-spec.md](docs/specs/factor-spec.md).

### [The Assessment Agent](agent/)

A Python CLI with purpose-built test suites. The output is a scored report showing which workload levels your data is ready for.

**The agent is strictly read-only.** It never creates, modifies, or deletes anything in your data source. For SQL platforms, only `SELECT`, `DESCRIBE`, `SHOW`, `EXPLAIN`, and `WITH` are allowed; validation is enforced before execution.

**Built-in suites:**

| Suite | What it uses |
|-------|----------------|
| `common` | ANSI SQL + information_schema. Works on any SQL database (DuckDB, etc.). |

The suite is auto-detected from your connection. Or specify it: `--suite common`.

### [Design & Specs](docs/)

Specifications, design rationale, and architecture:

- [Project spec](docs/specs/project-spec.md) — purpose, layers, outcomes
- [CLI spec](docs/specs/cli-spec.md) — commands, artifacts, config
- [Factor spec](docs/specs/factor-spec.md) — factor document shape, requirement keys
- [Design log](docs/log/) — composability, architecture, analysis

## How It Works

1. **Connect** — Point the agent at your database (connection string or `AIRD_CONNECTION_STRING`).
2. **Discover** — The agent enumerates schemas, tables, and columns (or use `aird discover` alone).
3. **Generate** — Tests are generated from the selected suite and inventory.
4. **Execute** — Queries run against your data source (read-only), producing measurements.
5. **Score** — Results are assessed against L1/L2/L3 thresholds.
6. **Report** — A scored report shows where you stand and what to fix.
7. **Save** — Results are stored locally in SQLite (`~/.aird/assessments.db` by default, or `AIRD_DB_PATH`) for history and diffing.

```bash
# One-shot full pipeline
aird assess -c "duckdb://:memory:" -o markdown

# Try the Clean factor suite on a real DB (create sample, then assess)
python scripts/create_sample_duckdb.py && aird assess -c "duckdb://sample.duckdb" -o markdown

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
```

## For coding agents

Start at **[AGENTS.md](AGENTS.md)** for the playbook. It outlines the workflow (interview → connect → discover → assess → interpret → remediate → compare), stopping points, and where to find the CLI, framework, and skills. Sub-skills live in [skills/](skills/) with step-by-step guidance per phase.

## Contributing

Specs and design rationale live under [docs/specs](docs/specs/) and [docs/log](docs/log/). Contributions that align with the project spec and CLI spec are welcome.

## License

MIT
