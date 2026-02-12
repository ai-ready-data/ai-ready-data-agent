# CLI specification

This document specifies the command-line interface for the AI-Ready Data assessment tool. The CLI is the single entry point for both humans and coding agents: it runs assessments, produces reports, and persists history. It is read-only with respect to the user's data sources. Design rationale for composability is in [docs/log/design-cli-composability.md](../log/design-cli-composability.md). **Components and architecture** (internal structure, package layout) are in [docs/log/design-cli-architecture.md](../log/design-cli-architecture.md).

---

## 1. Purpose and constraints

**Purpose:** Expose assessment, discovery, reporting, and history as commands that can be used in one shot (convenience) or composed (flexibility).

**Constraints:**

- **Read-only:** The CLI never creates, modifies, or deletes data in the user's data source. For SQL backends, only SELECT, DESCRIBE, SHOW, EXPLAIN, and WITH are allowed; validation is enforced before execution.
- **No credentials in code or logs:** Connection strings and secrets are supplied via arguments or environment; they are not logged or written to disk in plain text except where the user explicitly writes them (e.g. a context file).
- **Single entry point:** The tool is invoked as `aird` (or `python -m agent.cli`). All behavior is reachable via subcommands.

---

## 2. Command set

Commands are split into **convenience** (one-shot or simple) and **composable** (primitives that produce/consume artifacts). Optional/future commands are listed for completeness.

### 2.1 Convenience commands

| Command | Purpose |
|--------|---------|
| **assess** | Full pipeline in one shot: connect → discover → generate tests → execute → score → report → (optional) save → output. Single connection via `-c` or env. Equivalent to running discover, then run, then report, then optionally save, with sensible defaults. |
| **init** | Interactive setup wizard for first-time users. Walks through connection, scope, and context configuration. |
| **history** | List saved assessments from local SQLite. Optional filters: connection, limit. |
| **diff** | Compare two reports. Input: two assessment ids, or two report files (e.g. `diff <id1> <id2>` or `diff --left report1.json --right report2.json`). |
| **suites** | List available test suites (e.g. auto, common, snowflake). No side effects. |
| **compare** | Compare assessment results for two tables side-by-side from the same connection. |
| **rerun** | Re-run failed tests from the most recent (or specified) assessment and show improvement delta. |
| **benchmark** | N-way comparison: run assessments on multiple connections (repeatable `-c`, at least 2) and compare results side-by-side. |

### 2.2 Composable commands

| Command | Input | Output | Purpose |
|---------|--------|--------|---------|
| **discover** | Connection, schema/table filters, optional context file | Inventory (JSON to stdout or file) | Connect and discover only; no tests, no execution. Enables scope inspection or feeding into `run`. |
| **run** | Connection, inventory (file or stdin), suite, thresholds, optional context | Results (JSON to stdout or file) | Generate tests from inventory and execute them. Enables re-run with same scope without re-discovering. |
| **report** | Results (file or stdin), inventory (file; or embedded in results if defined), thresholds, optional context | Report (JSON or markdown to stdout/file) | Build report from results. Enables re-score with different thresholds or re-render in another format. |
| **save** | Report (file or stdin) | Assessment id (stdout) | Persist report to local history (SQLite). Enables saving a report produced by `report` or by another tool. |

### 2.3 Optional / future

| Command | Purpose |
|--------|---------|
| **connect** | Test connection only; output platform and version. Use case: "can I reach the DB?" without discovery. |
| **generate** | From inventory (and suite), output test list only (no execute). Use case: inspect or export tests; feed a custom executor. Lower priority than discover/run/report. |

---

## 3. Artifacts and data flow

Artifacts are the inputs and outputs that allow composition. Each has a stable shape (JSON schema or documented structure).

| Artifact | Produced by | Consumed by | Description |
|----------|-------------|-------------|-------------|
| **Inventory** | discover | run, report (for not_assessed) | Schemas, tables, columns; scope and context-aware filtering. |
| **Results** | run (execute) | report | Raw test results: per test, pass/fail per workload (L1/L2/L3), measured value, thresholds. |
| **Report** | report, assess (score step) | save, output, diff, compare, rerun | Full report: summary, factor_summary, results (with embedded thresholds and direction), not_assessed, target_workload, environment, user_context. Conforms to [report-spec.md](report-spec.md). One connection_fingerprint, one summary, one results list per report. |

Pipeline: **connection + context** → discover → **inventory** → run (generate + execute) → **results** → report (score + render) → **report** → (optional) save, output.

---

## 4. Command contracts

### 4.1 assess

**Purpose:** Run the full assessment pipeline. Convenience command; equivalent to discover → run → report → [save] → output. Single connection only.

**Arguments (summary):**

| Argument | Env fallback | Default | Description |
|----------|--------------|---------|-------------|
| `--connection`, `-c` | `AIRD_CONNECTION_STRING` | — | Database connection string. Single connection only; use `benchmark` for multi-connection comparison. |
| `--schema`, `-s` | — | all non-system | Schemas to include (repeatable). |
| `--tables`, `-t` | — | — | Specific tables (schema.table); when set, only these tables are in scope. |
| `--suite` | — | auto | Test suite: auto (detect from connection), common, snowflake, etc. |
| `--output`, `-o` | `AIRD_OUTPUT` | markdown | Output: `stdout` (JSON), `markdown`, or `json:<path>`. |
| `--thresholds` | `AIRD_THRESHOLDS` | built-in | Path to custom thresholds JSON. |
| `--context` | `AIRD_CONTEXT` | — | Path to user context YAML (scope, overrides, target level). |
| `--workload` | — | — | Target workload level: `analytics` (L1), `rag` (L2), or `training` (L3). |
| `--factor` | — | — | Filter to a single factor (e.g. `clean`, `contextual`). When set, only tests for that factor are run. |
| `--survey` | — | false | Run question-based survey and include results in report. |
| `--survey-answers` | — | — | Path to YAML of pre-filled survey answers (for non-interactive or demo use). |
| `--no-save` | — | false | Do not persist report to local history. |
| `--compare` | — | false | After run, output diff against previous assessment for the same connection. |
| `--dry-run` | — | false | Stop after generate; do not execute tests. Output preview (test count, sample). |
| `--interactive`, `-i` | — | false | Emit structured interview questions (e.g. post-discover, post-results) for agent consumption. |
| `--audit` | `AIRD_AUDIT` | false | Enable audit log: persist all queries and conversation to the same SQLite DB. |

**Behavior:** Connect → discover (with context filters) → generate tests → [if not dry-run] execute → score → build report (top-level `connection_fingerprint`, `summary`, `results`) → [if not --no-save] save to SQLite → output report. When `--compare` is set and save was done, output diff vs previous run for that connection. Output uses Rich colored tables and progress bars when running in a TTY.

### 4.2 discover

**Purpose:** Connect and discover only; output inventory.

**Input:** Connection (required), schema/table filters, optional context file.

**Output:** Inventory JSON to stdout or to file (e.g. `-o inventory.json`). Shape: schemas, tables, columns, and metadata needed for run/report.

**Arguments (summary):** `--connection`, `--schema`, `--tables`, `--context`, `--output` (stdout or path).

### 4.3 run

**Purpose:** Generate tests from an inventory and execute them; output results.

**Input:** Connection, inventory (file or stdin), suite, thresholds, optional context.

**Output:** Results JSON to stdout or file. Shape: list of test results (factor, requirement, target, pass/fail per workload, measured value, thresholds).

**Arguments (summary):** `--connection`, `--inventory` (path or `-` for stdin), `--suite`, `--thresholds`, `--context`, `--output`, `--audit` (when audit is enabled, queries from this run are logged to the same SQLite DB).

### 4.4 report

**Purpose:** Build and optionally render a report from results (and inventory).

**Input:** Results (file or stdin), inventory (file; or embedded in results if defined), optional thresholds, optional context.

**Output:** Report as JSON or markdown to stdout or file. Same shape as the report produced by assess.

**Arguments (summary):** `--results` (path or `-`), `--inventory`, `--thresholds`, `--context`, `--output` (format and path). Optional: `--id` to load a saved report by assessment id and re-output (e.g. different format).

### 4.5 save

**Purpose:** Persist a report to local history.

**Input:** Report (file or stdin).

**Output:** Assessment id to stdout. The id is a stable, opaque identifier (e.g. UUID) for use with `report --id` and `diff`.

**Arguments (summary):** `--report` (path or `-` for stdin), or report on stdin.

### 4.6 history

**Purpose:** List saved assessments.

**Arguments (summary):** `--connection` (filter by connection), `--limit`, `-n` (default 20).

**Output:** Table (e.g. id, timestamp, tables, L1/L2/L3 scores, connection).

### 4.7 diff

**Purpose:** Compare two reports.

**Input:** Two assessment ids, or two report files (e.g. `--left`, `--right`).

**Output:** Markdown (or structured) diff: tests added/removed, pass/fail changes, score deltas.

### 4.8 suites

**Purpose:** List available test suites.

**Arguments:** None. **Output:** Suite names and short descriptions.

### 4.9 init

**Purpose:** Interactive setup wizard for first-time users. Walks through connection configuration, scope selection, and context setup.

**Arguments:** None.

**Behavior:** Launches an interactive prompt that guides the user through setting up their first assessment. No flags required; all configuration is gathered interactively.

### 4.10 compare

**Purpose:** Compare assessment results for two tables side-by-side from the same connection. Useful for understanding how different tables in the same database score relative to each other.

**Arguments (summary):**

| Argument | Env fallback | Default | Description |
|----------|--------------|---------|-------------|
| `--connection`, `-c` | `AIRD_CONNECTION_STRING` | — | Database connection string. |
| `--tables` | — | — | Comma-separated table names to compare (e.g. `main.t1,main.t2`). |
| `--suite` | — | auto | Test suite. |
| `--thresholds` | `AIRD_THRESHOLDS` | built-in | Path to custom thresholds JSON. |
| `--no-save` | — | false | Do not persist reports to local history. |

**Behavior:** Discovers the specified tables, runs the assessment suite on each, then outputs a side-by-side comparison of results.

### 4.11 rerun

**Purpose:** Re-run only the failed tests from a previous assessment and show the improvement delta.

**Arguments (summary):**

| Argument | Env fallback | Default | Description |
|----------|--------------|---------|-------------|
| `--connection`, `-c` | `AIRD_CONNECTION_STRING` | — | Database connection string. |
| `--id` | — | most recent | Assessment ID to re-run failed tests from. Defaults to the most recent assessment. |
| `--thresholds` | `AIRD_THRESHOLDS` | built-in | Path to custom thresholds JSON. |
| `--no-save` | — | false | Do not persist the re-run report to local history. |

**Behavior:** Loads the specified (or most recent) assessment, identifies all failed tests, re-runs only those tests against the connection, then outputs the results with a delta showing which failures were fixed and which remain.

### 4.12 benchmark

**Purpose:** Run assessments on multiple connections and compare results side-by-side. This is the multi-connection comparison command (repeatable `-c`).

**Arguments (summary):**

| Argument | Env fallback | Default | Description |
|----------|--------------|---------|-------------|
| `--connection`, `-c` | — | — | Connection string. **Repeatable:** at least 2 required. Each connection is assessed independently. |
| `--label` | — | auto-generated | Comma-separated labels for each connection (e.g. `prod,staging`). Auto-generated from connection if omitted. |
| `--suite` | — | auto | Test suite. |
| `--factor` | — | — | Filter to a single factor (e.g. `clean`, `contextual`). |
| `--thresholds` | `AIRD_THRESHOLDS` | built-in | Path to custom thresholds JSON. |
| `--save` | — | false | Persist each individual report to history. |
| `--list` | — | false | List previous benchmark runs instead of running a new one. |

**Behavior:** For each connection: connect → discover → run → score. Then produce a combined comparison report showing per-connection scores and factor summaries side-by-side. Output uses Rich colored tables when running in a TTY.

---

## 5. Configuration and state

**Configuration:**

- **Connection:** Single connection via `--connection` / `-c` or `AIRD_CONNECTION_STRING`. Connection string format is platform-specific; see the platform support doc in the repo. Example forms: `snowflake://…`, `duckdb://path/to/file`. For multi-connection comparison, use `benchmark` with repeatable `-c`.
- **Workload:** Optional target workload via `--workload` on assess: `analytics` (L1), `rag` (L2), or `training` (L3).
- **Factor filter:** Optional `--factor` on assess and benchmark to restrict tests to a single factor (e.g. `clean`, `contextual`).
- **Context:** Optional YAML file (scope and overrides). Via `--context` or `AIRD_CONTEXT`. When present, **schemas** and **tables** are applied to discovery (per-target scope overrides context when set). Report includes `user_context` when context is loaded. YAML shape: `schemas: [string]`, `tables: [string]` (optional); future: target_level, exclusions, nullable-by-design, PII, freshness SLAs).
- **Thresholds:** Optional JSON file (per-requirement L1/L2/L3 thresholds). Via `--thresholds` or `AIRD_THRESHOLDS`. Default: built-in thresholds. JSON shape: `{ "<requirement_key>": { "l1": float, "l2": float, "l3": float }, ... }`; keys are merged over built-in (e.g. `null_rate`, `duplicate_rate`).
- **Output default:** Via `AIRD_OUTPUT` (e.g. markdown, stdout).
- **Log level:** Via `AIRD_LOG_LEVEL`.

**State:**

- **History:** SQLite database (e.g. `~/.aird/assessments.db`). Path configurable via `AIRD_DB_PATH`. Stores full report JSON per run for history and diff. All persistent state uses this same database (no separate DB for audit).
- **Context persistence:** Optional per-connection context files (e.g. under `~/.aird/contexts/`) so users don’t re-enter scope/overrides on re-run. CLI may save context after assess when connection is known.
- **No resource manifest:** Unlike tools that create cloud resources, we do not maintain a manifest of created objects; we only store assessment reports and context.

**Audit log (opt-in):** When enabled via `--audit` or `AIRD_AUDIT=1`, the same SQLite database maintains a full audit log:
  - **Queries:** Every query executed during a run (e.g. per test: query text, target, factor/requirement, assessment_id, timestamp). No redaction or size limit; full query text is stored.
  - **Conversation:** All conversation with the user (e.g. interview questions emitted, user answers, phase, assessment_id or session id, timestamp). Full content is stored. Conversation is recorded when interactive phases run (e.g. `--interactive` on assess).
  Audit applies to any command that executes queries (assess; run when used in a composed flow). Composable commands that execute queries support `--audit` so that a composed pipeline can enable audit on `run`. Retention and size are not limited for now; everything is kept. The feature is off by default so users must opt in.

---

## 6. Output formats and exit codes

**Output formats:**

- **stdout:** JSON written to stdout (e.g. `--output stdout` for assess/report). Machine-readable output (JSON, assessment id from save) is written **only to stdout** so that piping and parsing are safe (e.g. `aird assess -o stdout | jq …`, `aird save … | xargs …`). Errors and log messages go to **stderr**.
- **markdown:** Human-readable report (default for assess).
- **json:<path>:** Write JSON report (or inventory, or results) to the given path.

Report and results JSON conform to the documented schema in [report-spec.md](report-spec.md) so that agents and other tools can parse them.

**Exit codes:**

- `0` — Success.
- Non-zero — Failure (e.g. connection failed, invalid args, no tables found). Implementation should define distinct codes (e.g. 1 for runtime error, 2 for usage error) so scripts and agents can branch on failure type.

---

## 7. Agent and script usability

- **Stable flags:** Flags and subcommands are stable; scripts and agents can rely on them. New options are additive where possible.
- **Machine-readable output:** JSON output (report, results, inventory) is the contract for parsing. Markdown is for human reading.
- **Composition:** Agents can run `discover`, present scope to the user, then run `run` after confirmation; or run `assess` once and then `report --id <id> -o markdown` to re-render.
- **No interactive prompts required:** All commands can be driven by args and env; no mandatory prompts. Interactive mode (e.g. `--interactive` on assess) only adds structured question output for the agent to use in conversation.

---

## 8. Reference alignment

We align with the reference (e.g. snow-utils) on:

- **Single entry point** and clear subcommands.
- **Environment-based configuration** for connection, output, and optional paths.
- **Explicit behavior** (dry-run, no-save) so users can preview or skip persistence.

We diverge:

- **No resource manifest:** We do not create or delete resources in the user’s platform; we only assess and report. No create/cleanup/replay of cloud resources.
- **Composable primitives:** discover, run, report, save are first-class so the pipeline can be run in parts or recombined.

---

## 9. Implementation notes

- All 12 commands are implemented: **assess**, **discover**, **run**, **report**, **save**, **history**, **diff**, **suites**, **init**, **compare**, **rerun**, **benchmark**.
- **assess** is implemented as a composition of discover → run → report → save (when not --no-save) → output. For component boundaries and package layout, see [design-cli-architecture.md](../log/design-cli-architecture.md).
- Artifact schemas (inventory, results, report) are defined elsewhere (e.g. agent schema docs or test suite spec); this spec references them and the flow between commands.
- **Rich UI:** Output uses Rich library for colored tables, progress bars, and formatted reports when running in a TTY. Non-TTY output falls back to plain text for machine consumption.

---

## 10. Evaluation: gaps and considerations

This section records gaps, ambiguities, and design choices that affect agent and user usability. Items may be resolved in this spec or deferred to implementation.

**Covered well:** Read-only guarantee; no credentials in logs; single entry point; convenience + composable commands; artifacts and data flow; env-based config; audit opt-in and same-DB design; agent-oriented usability (stable flags, machine-readable JSON, no mandatory prompts).

**Clarified in spec (see inline):**

- **stdout vs stderr:** Machine-readable output (JSON, assessment id) is written only to stdout so that `aird assess -o stdout | jq …` and `aird save … | xargs …` are safe; errors and log messages go to stderr.
- **Assessment id:** A stable, opaque identifier (e.g. UUID) so scripts and agents can reliably use it with `report --id` and `diff`.
- **Audit scope:** When `--audit` is enabled, it applies to any command that executes queries (assess; run when used in a composed flow). Conversation is recorded when `--interactive` is used during assess (or equivalent interactive phases). Composable commands that support audit accept `--audit` so that a composed discover → run → report → save flow can enable audit on run.
- **Connection string format:** Platform-specific; documented in the platform support doc (see project layout). CLI does not define connection syntax per platform.
- **Exit codes:** Implementation should define at least: 0 = success; non-zero for failure, with distinct codes for runtime error vs usage error so scripts can branch.

**Resolved by this spec:**

- **Multi-connection comparison:** The `benchmark` command provides N-way dataset comparison with repeatable `-c`. Single-connection `assess` is kept simple; multi-connection is a separate workflow.
- **Re-run failed tests:** The `rerun` command targets only failed tests from a previous assessment, reducing iteration time.
- **Table-level comparison:** The `compare` command enables side-by-side comparison of tables within the same connection.
- **Interactive setup:** The `init` wizard lowers the barrier for first-time users.

**Gaps and considerations (for implementation or later spec):**

| Area | Gap / consideration |
|------|----------------------|
| **Composable args** | discover, run, report, save, history, diff list only summary arguments. Full flag tables (with env fallbacks and defaults) would help agents script any combination; consider adding them or a single "Global and per-command flags" reference. |
| **run --dry-run** | assess has --dry-run; composable `run` does not yet specify it. For parity, `run` may support --dry-run (generate tests only, no execute; output test list or results skeleton). |
| **history / diff output** | history outputs a "table"; diff outputs "markdown (or structured)". For agents, machine-readable output (e.g. `history -o json`, `diff -o json`) should be supported; format can be defined with report schema. |
| **suites output** | "Suite names and short descriptions" — if agents need to pick a suite programmatically, a JSON output option (e.g. `suites -o json`) would help. |
| **Context persistence** | "CLI may save context after assess" — whether this is automatic or opt-in is TBD. Implementation should avoid overwriting user context without clear intent. |
| **Paths** | Context, thresholds, and output paths are relative to process CWD unless absolute. No explicit note in spec; agents running from different working directories should be aware. |
| **Log level and secrets** | debug log level must not log connection strings or secrets; implementation should redact or exclude. |
| **Timeout / interrupt** | Long-running assess: behavior on SIGINT (e.g. Ctrl+C) and exit code (e.g. 130) not specified; useful for agents that cancel runs. |
| **report --id** | report has two modes: (1) from artifacts (--results, --inventory), (2) from history (--id). When using --id, connection is not required. Already implied; could be stated in report contract. |
| **Optional commands** | connect (test connection), generate (test list only): if implemented, their contracts (args, output) should match the patterns above (env fallbacks, machine-readable where relevant). |
