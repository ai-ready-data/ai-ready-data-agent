# Demo: Clean assessment on Snowflake

This runbook shows how to run a **Clean**-factor assessment against Snowflake, scoped to the datasets you use for your AI workload. The milestone focuses on making Clean very good and Snowflake-specific; other factors and the question-based survey are optional.

---

## Prerequisites

- Python 3.9+
- Snowflake account (or trial)
- (Optional) Cortex Code CLI, if you run from that environment

---

## 1. Install with Snowflake support

```bash
cd ai-ready-agent
pip install -e ".[snowflake]"
```

This installs `snowflake-connector-python` so the agent can connect without the Snowflake CLI.

---

## 2. Configure the connection

**Option A: Environment variables (good for CI / notebooks / servers)**

```bash
export SNOWFLAKE_ACCOUNT="your_org-your_account"   # no .snowflakecomputing.com
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="your_warehouse"       # or WAREHOUSE
export SNOWFLAKE_DATABASE="your_database"         # optional
export SNOWFLAKE_SCHEMA="your_schema"             # optional
```

Then use a connection string with the scheme so the agent picks the Snowflake adapter:

```bash
aird assess -c "snowflake://"
```

The adapter reads from the env vars above.

**Option B: Connection string (URL)**

```
snowflake://USER:PASSWORD@ACCOUNT/DATABASE/SCHEMA?warehouse=WH_NAME
```

- `ACCOUNT`: account identifier (e.g. `xy12345` or `org-account`), no `.snowflakecomputing.com`
- Optional query: `warehouse=...`, `role=...`

Example:

```bash
aird assess -c "snowflake://myuser:mypass@myorg-myaccount/analytics/public?warehouse=compute_wh"
```

---

## 3. Scope to your AI workload datasets

Run Clean only on **the specific datasets you care about**. Use one of these:

**Schemas only**

```bash
aird assess -c "snowflake://..." -s analytics -s staging
```

**Specific tables (schema.table)**

```bash
aird assess -c "snowflake://..." -t analytics.features -t analytics.labels
```

**Context file (YAML)** — for reuse

```yaml
# context.yaml
schemas:
  - analytics
  - staging
# or
tables:
  - analytics.features
  - analytics.labels
```

```bash
aird assess -c "snowflake://..." --context context.yaml
```

Discovery inventories only that scope; all Clean tests run against that inventory.

---

## 4. Run the Clean assessment

```bash
aird assess -c "snowflake://..." -o markdown
```

No `--survey` needed. The report includes:

- **Summary:** Total tests, L1/L2/L3 pass counts and percentages.
- **Results:** One row per Clean test (table count, null rate, duplicate rate, zero/negative rate, type inconsistency, format inconsistency). Each is PASS or FAIL based on thresholds.

Output is markdown by default. Use `-o stdout` for JSON or `-o json:path/to/report.json` to write JSON.

---

## 5. What Clean measures on Snowflake

| Requirement | What we measure |
|-------------|------------------|
| **table_discovery** | Count of tables in scope (excluding system schemas). Informational. |
| **null_rate** | Per column: fraction of rows where the column is NULL. Pass if ≤ threshold (L1/L2/L3). |
| **duplicate_rate** | Per table: fraction of rows that are duplicates (1 − distinct rows / total rows). Pass if ≤ threshold. |
| **zero_negative_rate** | Per numeric column: fraction of values ≤ 0. For columns that should be positive (amounts, counts). Pass if ≤ threshold. |
| **type_inconsistency_rate** | Per numeric column: fraction of non-null values that fail to cast to DOUBLE. Pass if ≤ threshold. |
| **format_inconsistency_rate** | Per string column with date-like name: fraction of non-null values that don’t parse as DATE. Pass if ≤ threshold. |

Queries use Snowflake-native SQL: `COUNT_IF`, `TRY_CAST`, double-quoted identifiers. See `agent/suites/clean_snowflake.py`.

---

## 6. Optional: question-based survey

If you want to add human-answerable questions (one per factor, scoped to “these datasets”), run with `--survey`:

```bash
aird assess -c "snowflake://..." --survey -o markdown
```

Answers default to “—” unless you supply a pre-filled YAML:

```bash
aird assess -c "snowflake://..." --survey --survey-answers answers.yaml -o markdown
```

Survey is **optional**; the main demo is Clean-only.

---

## 7. Cortex Code CLI

- Pass the connection string via your usual mechanism.
- Scoping (`-s`, `-t`, or `--context`) works the same; point at your AI workload datasets.
- For a Clean-only demo, omit `--survey`.

---

## 8. Sanity check (no Snowflake required)

To confirm the pipeline and Clean report shape without Snowflake credentials:

```bash
aird assess -c "duckdb://:memory:" --no-save -o markdown
```

You should see a report with a **Results** section (Clean tests). Add `--survey` only if you want to exercise the question-based flow.
