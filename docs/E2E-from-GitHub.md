# Full E2E Test (from a fresh clone)

Use this when you’ve just landed on the repo (e.g. from the GitHub URL) and want to run a full end-to-end test of the assessment pipeline.

## Prerequisites

- Python 3.9+
- Git

## Steps

1. **Clone and enter the repo**
   ```bash
   git clone https://github.com/ai-ready-data/ai-ready-data-agent.git
   cd ai-ready-data-agent
   ```

2. **Install the package**
   ```bash
   pip install -e .
   ```

3. **Verify setup** (recommended when you first land — no credentials)
   ```bash
   python scripts/verify_setup.py
   ```
   Creates temporary DuckDB and SQLite DBs, runs the assessment for both, then removes them. Exit 0 means the agent is ready.

   **Optional: create sample files** for later CLI/estate runs:
   ```bash
   python scripts/verify_setup.py --write-files
   ```
   This creates `sample.duckdb`, `sample.sqlite`, and `connections.yaml` in the repo root (all in .gitignore).

4. **Run the assessment**
   ```bash
   aird assess -c "duckdb://sample.duckdb" -o markdown
   ```
   Or SQLite (after setup): `aird assess -c "sqlite://sample.sqlite" -o markdown`  
   Or in-memory DuckDB: `aird assess -c "duckdb://:memory:" -o markdown`

   **Optional: data estate** (multiple connections in one run):  
   After `verify_setup.py --write-files`: `aird assess --connections-file connections.yaml -o markdown`  
   Or: `aird assess -c "duckdb://sample.duckdb" -c "sqlite://sample.sqlite" -o markdown`

5. **Optional: history and diff**
   ```bash
   aird save --report report.json   # if you saved report as JSON
   aird history
   aird diff <id1> <id2>
   ```

## Expected outcome

- **Step 4** should complete with exit code 0 and print a report (summary, results, pass/fail by factor/level).
- **Step 5** `aird history` should list runs; `aird diff` should show differences between two report IDs.

## For coding agents

Start at [AGENTS.md](../AGENTS.md) and use the skills in [skills/](../skills/) for the full workflow: discover → connect → assess → interpret → remediate → compare. CLI-specific commands are in [skills/cli/](../skills/cli/). Factor knowledge (thresholds, SQL, remediation) is in [skills/factors/](../skills/factors/). The steps above are the minimal path to validate the CLI and Clean suite E2E.
