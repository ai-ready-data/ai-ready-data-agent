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

3. **Create the sample DuckDB** (optional but recommended for a realistic run)
   ```bash
   python scripts/create_sample_duckdb.py
   ```
   This creates `sample.duckdb` in the repo root (ignored by git) with `main.products` and some nulls/duplicates for the Clean suite.

4. **Run the assessment**
   ```bash
   aird assess -c "duckdb://sample.duckdb" -o markdown
   ```
   Or with in-memory: `aird assess -c "duckdb://:memory:" -o markdown`

   **Optional: data estate** (multiple connections in one run):  
   `aird assess -c "duckdb://sample.duckdb" -c "duckdb://:memory:" -o markdown`  
   Or use `--connections-file <path>` (one connection per line).

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

Start at [AGENTS.md](../AGENTS.md) and use the skills in [skills/](../skills/) for the full workflow: connect → discover → assess → interpret → remediate → compare. The steps above are the minimal path to validate the CLI and Clean suite E2E.
