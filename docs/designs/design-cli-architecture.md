# Design: CLI components and architecture

This document defines the **internal components and architecture** of the CLI for the AI-Ready Data assessment tool. It complements the [CLI spec](../specs/cli-spec.md) (which defines the external surface: commands, artifacts, config) and guides implementation and future refactors. The design keeps the pipeline testable, composable, and aligned with the spec’s command and artifact flow.

---

## 1. Purpose and scope

**Purpose:** Describe the main components of the CLI, their responsibilities, how they depend on each other, and where they live in the repo. This gives implementers and agents a clear map of “where does X happen?” and “what does Y depend on?”

**Scope:**

- **In scope:** Component boundaries, data flow between components, platform and storage abstraction, suggested package layout, cross-cutting concerns (config, errors, audit).
- **Out of scope:** Detailed API of each module (that belongs in code or a later implementation spec), skill/agent orchestration (see agentic system spec), and test-suite internals (see test suite spec).

**Principles:** Single responsibility per component; artifacts (inventory, results, report) as the contract between steps; read-only and no-secrets enforced at the platform boundary; one SQLite DB for all persistent state.

---

## 2. High-level architecture

```mermaid
flowchart TB
  subgraph CLI ["CLI layer"]
    Entry[Entry point: aird]
    Args[Arg parse + env]
    Entry --> Args
    Args --> Assess[assess]
    Args --> Discover[discover]
    Args --> Run[run]
    Args --> Report[report]
    Args --> Save[save]
    Args --> History[history]
    Args --> Diff[diff]
    Args --> Suites[suites]
  end

  subgraph Pipeline ["Pipeline / orchestration"]
    Assess --> Discover
    Assess --> Run
    Assess --> Report
    Assess --> Save
  end

  subgraph Core ["Core services"]
    Discovery[Discovery]
    TestRunner[Test runner]
    Reporter[Reporter]
    Storage[Storage]
  end

  subgraph Platform ["Platform layer"]
    Registry[Platform registry]
    Conn[Connection factory]
    SuitesReg[Suite registry]
    Exec[Query executor\n(read-only)]
    Registry --> Conn
    Registry --> SuitesReg
    Conn --> Exec
  end

  subgraph Audit ["Audit (opt-in)"]
    AuditSink[Audit sink]
  end

  Discover --> Discovery
  Run --> TestRunner
  Report --> Reporter
  Save --> Storage
  History --> Storage
  Diff --> Storage

  Discovery --> Registry
  Discovery --> Conn
  TestRunner --> Registry
  TestRunner --> Conn
  TestRunner --> Exec

  Reporter --> Storage

  TestRunner -.->|if --audit| AuditSink
  Pipeline -.->|conversation if -i| AuditSink
  AuditSink --> Storage
```

**Flow in words:** The CLI parses args and env and dispatches to command handlers. **Convenience** commands (e.g. assess) use a pipeline that composes **core services**: discovery → test runner → reporter → optional save. **Composable** commands (discover, run, report, save) call the same core services directly. Discovery and the test runner go through the **platform layer** (registry, connection, suite, read-only executor). **Storage** holds history and, when enabled, **audit** writes queries and conversation into the same DB via the storage layer.

---

## 3. Components

### 3.1 CLI layer

**Responsibility:** Single entry point (`aird` or `python -m agent.cli`), argument parsing, environment resolution, and dispatching to the right handler. No business logic; only wiring and validation of flags/paths.

**Inputs:** argv, env (e.g. `AIRD_CONNECTION_STRING`, `AIRD_DB_PATH`).

**Outputs:** Exit code; stdout/stderr (delegated to handlers). Machine-readable output only on stdout; errors and logs to stderr.

**Key behavior:**

- Resolve config: connection, context path, thresholds path, output format, log level, audit flag, DB path.
- Validate required args (e.g. connection for assess/discover/run).
- Pass resolved config and artifact paths (or stdin) to the handler for each subcommand.

**Dependencies:** Pipeline (for assess), Discovery, TestRunner, Reporter, Storage, Platform (for suites, and indirectly via Discovery/TestRunner). No direct dependency on Audit; audit is enabled via config and used by pipeline/run.

---

### 3.2 Pipeline / orchestration

**Responsibility:** Implement the “assess” flow: discover → run → report → [save] → output. Ensures artifacts are passed between steps in memory or via temp/files as needed, and that options like `--no-save`, `--dry-run`, `--compare`, `--interactive` are applied.

**Inputs:** Resolved config (connection, context, suite, thresholds, output, flags).

**Outputs:** Report (or dry-run preview) to stdout/file; optionally saved assessment id; optional diff output.

**Key behavior:**

- Call Discovery to get inventory.
- If `--dry-run`, call TestRunner in dry-run mode (generate only) and exit with preview.
- Otherwise call TestRunner with inventory to get results.
- Call Reporter with results (and inventory) to get report.
- If not `--no-save`, call Storage to save report; capture assessment id.
- If `--compare`, load previous assessment for same connection from Storage and produce diff.
- Emit interactive questions (if `--interactive`) at defined points; when audit is on, conversation is sent to Audit sink.

**Dependencies:** Discovery, TestRunner, Reporter, Storage; optional Audit (when enabled).

---

### 3.3 Discovery

**Responsibility:** Connect to the data source, introspect schemas/tables/columns (and optionally other metadata), apply context filters (scope, exclusions), and produce the **inventory** artifact.

**Inputs:** Connection, schema/table filters, context (scope, overrides).

**Outputs:** Inventory (JSON shape: schemas, tables, columns, metadata needed for run/report).

**Key behavior:**

- Use platform registry to resolve connection and get a read-only connection (or adapter).
- Run platform-appropriate introspection (e.g. information_schema, system views); only read-only operations.
- Apply context (included/excluded schemas/tables, target level).
- Return structured inventory; no test execution.

**Dependencies:** Platform layer (registry, connection factory). Does not depend on TestRunner, Reporter, or Storage.

---

### 3.4 Test runner

**Responsibility:** From an **inventory** and a **suite** (and thresholds), generate the set of tests, execute them in a read-only way, and produce **results**. Optionally support dry-run (generate only, no execute). When audit is enabled, log every executed query to the audit sink.

**Inputs:** Connection, inventory (in memory or from file/stdin), suite name, thresholds, context, dry_run flag, audit flag.

**Outputs:** Results artifact (per test: factor, requirement, target, pass/fail per workload, measured value, thresholds).

**Key behavior:**

- Resolve suite from platform registry (e.g. auto-detect from connection).
- Generate test list (tests with query, target, factor, requirement).
- For each test: execute query via platform executor (read-only only); compare outcome to thresholds; record result. If audit enabled, send (query text, target, factor, requirement, assessment_id/session, timestamp) to audit.
- Aggregate into results JSON.

**Dependencies:** Platform layer (registry, connection, suite registry, query executor). Optional Audit sink when `--audit`.

---

### 3.5 Reporter

**Responsibility:** From **results** (and **inventory** when needed) and **thresholds**, compute scores and build the **report** artifact (JSON and/or markdown). Can also load a saved report by assessment id and re-output (e.g. different format).

**Inputs:** Results (file or stdin), optional inventory (file or embedded), thresholds, optional context; or assessment id (load from Storage).

**Outputs:** Report (JSON or markdown to stdout or file).

**Key behavior:**

- If input is assessment id, load report from Storage and re-render according to output format.
- Otherwise load results (and inventory); score against thresholds (L1/L2/L3 per requirement); build full report structure; render to requested format.

**Dependencies:** Storage (for report-by-id). No dependency on Platform or Discovery at report-build time (only on artifact shape).

---

### 3.6 Storage

**Responsibility:** Single SQLite database for all persistent state: saved reports (history), optional per-connection context, and when enabled, audit log (queries and conversation). Expose: save report (return assessment id), list assessments (history), get report by id, write audit entries.

**Inputs:** Report JSON (save); assessment id (get); filters (connection, limit for list); audit records (query rows, conversation rows).

**Outputs:** Assessment id (on save); list of assessments; report JSON (by id); success/failure for audit writes.

**Key behavior:**

- DB path from config (`AIRD_DB_PATH` or default `~/.aird/assessments.db`).
- Tables (logical): assessments (id, timestamp, connection fingerprint, report JSON, etc.), optional context cache, audit_queries, audit_conversation. Schema can be versioned for migrations.
- No business logic beyond persistence; no credentials stored (connection stored only in redacted/fingerprint form if at all, per spec).

**Dependencies:** None on other application components. Used by Pipeline, Reporter (load by id), History and Diff commands, and Audit sink.

---

### 3.7 Platform layer

**Responsibility:** Abstract the data platform so the rest of the CLI can work without knowing the specific backend. Provides: connection parsing and creation, suite selection (e.g. auto or by name), and **read-only** query execution. Enforces that only allowed statement types (SELECT, DESCRIBE, SHOW, EXPLAIN, WITH) are executed.

**Sub-components:**

- **Platform registry:** Map connection scheme or type to a platform adapter (e.g. snowflake, duckdb). Used by Discovery and Test runner to get a connection and the right suite.
- **Connection factory:** Parse connection string, create a connection (or adapter) that can run read-only operations. No credentials in logs.
- **Suite registry:** Map platform (or “common”) to a test suite (list of tests: factor, requirement, query ref or inline, target type).
- **Query executor:** Execute a single query against the connection; validate that the statement is read-only before execution; return result rows or error.

**Inputs:** Connection string; platform/suite name; query text; (for discovery) introspection “query” or API.

**Outputs:** Connection handle/adapter; suite definition; query results.

**Key behavior:**

- Read-only enforcement: parse or validate SQL (and/or restrict API) so that only SELECT, DESCRIBE, SHOW, EXPLAIN, WITH are allowed. Reject others before execution.
- Connection string format is platform-specific; documented in platform support doc, not in CLI spec.

**Dependencies:** None on Discovery, TestRunner, Reporter, Storage. Drivers (e.g. snowflake-connector-python) are external dependencies.

---

### 3.8 Audit (opt-in)

**Responsibility:** When `--audit` (or `AIRD_AUDIT=1`) is set, receive events for “query executed” and “conversation” and write them into the same SQLite DB via Storage. No filtering or retention; full content stored (spec: keep everything, behind flag).

**Inputs:** Query events (query text, target, factor, requirement, assessment_id or session_id, timestamp); conversation events (phase, content, assessment_id or session_id, timestamp).

**Outputs:** Writes to Storage (audit tables). No direct output to user.

**Key behavior:**

- Only active when audit is enabled in config. Pipeline and Test runner pass events to the audit sink when they run; interactive conversation is attached when `--interactive` is used during assess.
- Implementation can be a small “audit logger” that receives events and calls Storage to append rows.

**Dependencies:** Storage. Used by Pipeline (conversation) and Test runner (queries).

---

## 4. Data flow and dependencies (summary)

| Component    | Consumes                    | Produces / uses                    | Depends on                          |
|-------------|-----------------------------|------------------------------------|-------------------------------------|
| CLI         | argv, env                   | Exit code, dispatch                | All command handlers / pipeline     |
| Pipeline    | Config, connection, context | Report, optional id, diff          | Discovery, TestRunner, Reporter, Storage, (Audit) |
| Discovery   | Connection, context, filters| Inventory                          | Platform (registry, connection)     |
| Test runner | Inventory, suite, thresholds| Results                            | Platform; Audit (if enabled)        |
| Reporter    | Results, inventory, thresholds; or id | Report (JSON/md)            | Storage (for --id)                  |
| Storage     | Report, id, filters, audit rows | Id, list, report JSON, audit persisted | —                                   |
| Platform    | Connection string, suite, query | Connection, suite, query results | External drivers                    |
| Audit       | Query/conversation events   | Writes via Storage                 | Storage                             |

Artifacts (inventory, results, report) are the **contract** between Pipeline, Discovery, TestRunner, and Reporter. They are defined by schema/docs elsewhere; this architecture assumes they exist and flow as in the CLI spec.

---

## 5. Key design decisions

- **One SQLite DB:** History and audit live in the same database; path is `AIRD_DB_PATH` (or default). Simplifies deployment and backup; no separate “audit server.”
- **Platform behind an abstraction:** Discovery and Test runner depend on a platform abstraction (registry + connection + executor), not on a specific driver. This keeps adding platforms and suites a matter of registering adapters and suites.
- **Read-only at the platform boundary:** The platform layer (executor) is the single place that enforces read-only (e.g. SQL allow-list). No write path in the rest of the stack.
- **Assess as composition:** Assess is implemented by orchestrating Discovery → TestRunner → Reporter → Save (and optional Diff). Composable commands call the same core services; no duplicate logic.
- **Config resolved once:** The CLI layer resolves env and args into a config object (or structured namespace) that is passed down; components do not read env directly. This makes testing and scripting predictable.
- **Audit as optional sink:** Audit is not a core dependency of Pipeline or Test runner from a “must have” perspective; they check a flag and, if set, send events to the audit sink. Storage remains the single writer to the DB.

---

## 6. Suggested package layout

Layout under the **agent** package (installable via `pip install -e "./agent"` or similar). This is a target layout; existing code may differ until refactored.

```
agent/
  __init__.py
  cli.py              # Entry point, argparse/typer, dispatch to commands
  config.py           # Resolve args + env into config (paths, flags, connection)
  pipeline.py         # Assess orchestration: discover → run → report → save
  discovery.py        # Discovery service (inventory from connection + context)
  run.py              # Test runner (generate + execute, results)
  report.py           # Reporter (results → report; or load by id and re-output)
  storage.py          # SQLite: history, get/save report, audit writes
  audit.py            # Audit sink (receives events, delegates to storage)
  platform/
    __init__.py
    registry.py       # Platform and suite registration
    connection.py     # Connection factory, read-only adapter
    executor.py       # Read-only query execution
    # Platform-specific adapters (e.g. snowflake.py, duckdb.py) and
    # suite definitions (e.g. common, snowflake) can live here or in
    # a sibling package like suites/ — see test suite spec.
```

- **Framework** (factors, definitions) and **skills** stay at repo root as in project-spec; they are not part of the agent package.
- **Queries** and **test suite** definitions may live under `agent/suites/` or a shared `suites/` (or under platform); the test suite spec can define that. The important point is that the **test runner** receives a suite (list of tests) from the platform/suite registry and executes them via the platform executor.

---

## 7. Cross-cutting concerns

- **Config:** Resolved in CLI layer; passed into pipeline and each command. Includes: connection, context path, thresholds path, output format, log level, audit flag, DB path, dry_run, no_save, compare, interactive. No secrets in logs (debug must not log connection strings).
- **Errors:** Use consistent exception types or error codes so the CLI can map to exit codes (e.g. 1 runtime, 2 usage). Errors go to stderr; machine output only to stdout.
- **Logging:** Single log level (e.g. `AIRD_LOG_LEVEL`). Logs to stderr. Debug must not emit credentials or full connection strings.
- **Interactive / audit:** When `--interactive` is used, the pipeline (or a dedicated helper) emits structured questions; when audit is enabled, those exchanges are sent to the audit sink and persisted via Storage.

---

## 8. Relationship to other specs

- **CLI spec:** Defines the external surface (commands, args, artifacts, config, exit codes). This doc defines the internal components that implement that surface.
- **Project spec:** Describes the repo layout and the “agent package”; this doc refines the package layout for the CLI and core services.
- **Test suite spec:** Will define test model, suites, and queries; the **platform layer** and **test runner** depend on that contract (suite = list of tests; executor runs one query per test).
- **Factor spec:** Defines requirement keys and factor structure; thresholds and report scoring align with it; no direct component dependency except in Reporter (scoring logic) and suite definitions.

This architecture is intended to stay stable as new commands or platforms are added: new commands plug into the CLI layer and call existing core services; new platforms register in the platform layer and optionally add suites.
