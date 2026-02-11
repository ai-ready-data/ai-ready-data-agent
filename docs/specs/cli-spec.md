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
| **assess** | Full pipeline in one shot: connect → discover → generate tests → execute → score → report → (optional) save → output. Supports **single connection** (one `-c` or env) or **multiple connections** (estate mode: repeatable `-c` or `--connections-file`); in estate mode, one report per run with per-connection sections and optional aggregate summary. Equivalent to running discover, then run, then report, then optionally save, with sensible defaults. |
| **history** | List saved assessments from local SQLite. Optional filters: connection, limit. |
| **diff** | Compare two reports. Input: two assessment ids, or two report files (e.g. `diff <id1> <id2>` or `diff --left report1.json --right report2.json`). |
| **suites** | List available test suites (e.g. auto, common, snowflake). No side effects. |

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
| **Report** | report, assess (score step) | save, output, diff | Full report: summary, factor scores, tests, environment, user_context. Conforms to report schema. **Single-connection report:** one connection_fingerprint, one summary, one results list. **Estate report:** when assess is run with multiple connections, report includes per-connection sections (e.g. `platforms`: list of connection_fingerprint, summary, results, inventory) and an optional aggregate summary. |

Pipeline: **connection(s) + context** → [per connection: discover → **inventory** → run (generate + execute) → **results**] → report (score + render, merge if estate) → **report** → (optional) save, output. Single-connection: one discover → run → report. Estate: N connections → N discover+run → one merged report.

---

## 4. Command contracts

### 4.1 assess

**Purpose:** Run the full assessment pipeline. Convenience command; equivalent to discover → run → report → [save] → output. Supports **single-connection** (one database) or **multi-connection / estate** (multiple databases in one run).

**Arguments (summary):**

| Argument | Env fallback | Default | Description |
|----------|--------------|---------|-------------|
| `--connection`, `-c` | `AIRD_CONNECTION_STRING` (single) | — | Database connection string. **Repeatable:** when given multiple times (or combined with `--connections-file`), all connections are assessed in one run (estate mode). At least one connection required via one or more `-c` or `--connections-file`. |
| `--connections-file` | `AIRD_CONNECTIONS_FILE` | — | Path to connections manifest (YAML or JSON; extension .yaml, .yml, or .json). List of entries; each entry is a connection string or an object with `connection` and optional `targets` (databases, schemas, tables). See [manifest-spec.md](manifest-spec.md). If not set and no `-c` given, CLI uses default `~/.aird/connections.yaml` when it exists. Combined with any `-c`; together they form the assessment target list. |
| `--schema`, `-s` | — | all non-system | Schemas to include (repeatable). Applies to all connections. |
| `--tables`, `-t` | — | — | Specific tables (schema.table); when set, only these tables are in scope. Applies to all connections. |
| `--suite` | — | auto | Test suite: auto (detect from connection), common, snowflake, etc. Resolved per connection. |
| `--output`, `-o` | `AIRD_OUTPUT` | markdown | Output: `stdout` (JSON), `markdown`, or `json:<path>`. |
| `--thresholds` | `AIRD_THRESHOLDS` | built-in | Path to custom thresholds JSON. |
| `--context` | `AIRD_CONTEXT` | — | Path to user context YAML (scope, overrides, target level). Applies to all connections. |
| `--no-save` | — | false | Do not persist report to local history. |
| `--compare` | — | false | After run, output diff against previous assessment. Single-connection: same connection; estate: implementation-defined (e.g. same connection set or last estate run). |
| `--dry-run` | — | false | Stop after generate; do not execute tests. Output preview (test count, sample). |
| `--interactive`, `-i` | — | false | Emit structured interview questions (e.g. post-discover, post-results) for agent consumption. |
| `--log-level` | `AIRD_LOG_LEVEL` | info | Log level: debug, info, warn, error. |
| `--audit` | `AIRD_AUDIT` | false | Enable audit log: persist all queries and conversation to the same SQLite DB. |

**Behavior (single connection):** When exactly one connection is supplied (one `-c` or env only): connect → discover (with context filters) → generate tests → [if not dry-run] execute → score → build report (single-connection shape: top-level `connection_fingerprint`, `summary`, `results`) → [if not --no-save] save to SQLite → output report. If --compare and save was done, output diff vs previous run for that connection.

**Behavior (estate / multiple connections):** When two or more connections are supplied (multiple `-c` and/or `--connections-file`): for each connection, discover → generate tests → [if not dry-run] execute → collect (connection_fingerprint, results, inventory). Then build one **estate report** with per-connection sections (e.g. `platforms`: list of `{ connection_fingerprint, summary, results, inventory }`) and an **aggregate summary** (e.g. roll-up L1/L2/L3 or per-connection summary table). Save one assessment id for the whole run; output the estate report. If --compare, diff vs previous run (implementation-defined). Failed connections may be recorded in the report; implementation defines fail-fast vs continue-on-error.

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

---

## 5. Configuration and state

**Configuration:**

- **Connection(s):** Single connection via `--connection` / `-c` or `AIRD_CONNECTION_STRING`. For **estate** (multi-connection) runs: repeatable `-c` and/or `--connections-file` (path to a YAML/JSON manifest); env `AIRD_CONNECTIONS_FILE` may supply the path. When no `-c` and no `--connections-file` are given, the CLI uses the default **connections manifest** `~/.aird/connections.yaml` if that file exists. Manifest entries may use `env:VAR_NAME`; the CLI expands from the environment. Connection string format is platform-specific; see the platform support doc in the repo. Example forms: `snowflake://…`, `duckdb://path/to/file`.
- **Context:** Optional YAML file (scope, exclusions, target level, nullable-by-design, PII overrides, freshness SLAs). Via `--context` or `AIRD_CONTEXT`.
- **Thresholds:** Optional JSON file (per-requirement L1/L2/L3 thresholds). Via `--thresholds` or `AIRD_THRESHOLDS`. Default: built-in thresholds.
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

Report and results JSON conform to documented schemas (e.g. report schema, test-result schema) so that agents and other tools can parse them.

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

- The current implementation may expose only **assess**, **history**, **diff**, and **suites**. The composable commands (discover, run, report, save) and the extended diff (by id or by file) are part of this spec for implementation when needed.
- **assess** can be implemented as a composition of discover → run → report → save (when not --no-save) → output, or as a single flow; the observable behavior and artifacts are what this spec defines. For component boundaries and package layout, see [design-cli-architecture.md](../log/design-cli-architecture.md).
- Artifact schemas (inventory, results, report) are defined elsewhere (e.g. agent schema docs or test suite spec); this spec references them and the flow between commands.

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

- **Multi-connection / estate:** assess supports multiple connections (repeatable `-c`, `--connections-file`); report shape extends to estate (per-connection sections + aggregate summary). See [design-multi-connection-estate.md](../log/design-multi-connection-estate.md).

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
