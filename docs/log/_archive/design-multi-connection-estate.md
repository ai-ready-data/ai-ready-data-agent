# Design: Multi-connection and data estate assessment

**Date:** 2026-02-10

**Status:** Deferred to roadmap. See [docs/roadmap.md](../roadmap.md).

---

## 1. Rationale

The agent today evaluates **one connection per report**. For data estates (many databases, warehouses, or files across an organization), users need to assess multiple platforms in one logical run and get a single view: per-connection results plus an optional estate-level summary. Multi-connection/estate support is a core capability for value: it shifts the product from "assess a single database" to "assess your data estate."

**Goals:**

- Support **multiple connections in one `assess` run** (estate mode).
- Produce **one report per run** that includes per-connection sections and, when multiple connections are used, an aggregate/estate summary.
- Preserve **backward compatibility**: a single connection (one `-c` or env) behaves exactly as today (single-connection report shape).
- Keep **one assessment id per run** when saving to history (whether single- or multi-connection); diff continues to compare two reports (each may be single- or estate).

---

## 2. Scope

**In scope:**

- **assess** accepts multiple connections via repeatable `-c` and/or `--connections-file` (one connection string per line). When two or more connections are supplied, the pipeline runs discover → run for each connection, then builds one **estate report**.
- **Report shape** extends to support estate: in addition to the current top-level `summary`, `results`, `connection_fingerprint`, the report may include a **per-connection** structure (e.g. `platforms` or `connections`: list of `{ connection_fingerprint, summary, results, inventory }`) and an **aggregate summary** (e.g. roll-up L1/L2/L3 across connections, or per-connection summary table).
- **Single-connection report** remains unchanged: when exactly one connection is given, the report has the existing shape (no `platforms` array; `connection_fingerprint` and `summary`/`results` at top level).
- **history** and **save**: one assessment id per run; estate runs store the full estate report (with all connections). **diff** compares two reports (each may be single or estate); implementation may diff per-connection sections by fingerprint or present a high-level comparison.
- **Composable commands** (discover, run, report) remain **single-connection** in this phase. Estate is a convenience feature of **assess**; composable flow can still be used per-connection and reports merged externally if needed.

**Out of scope for this design:**

- Composable `run` or `report` accepting multiple result files in one call (could be a future extension).
- Parallel execution of connections (implementation may run sequentially first; parallelism can be added later).
- Context or scope per connection (e.g. different `--context` per connection); future enhancement.

---

## 3. Specification alignment

- **CLI spec** ([docs/specs/cli-spec.md](../specs/cli-spec.md)): Section 2.1 (assess purpose), section 3 (artifacts: Report with single vs estate shape), section 4.1 (assess: `-c` repeatable, `--connections-file`, single vs estate behavior), section 5 (Configuration: connection(s) and `AIRD_CONNECTIONS_FILE`). Single-connection behavior and report shape remain the default when one connection is supplied.
- **Project spec** ([docs/specs/project-spec.md](../specs/project-spec.md)): Layer 2 (CLI) and Outcomes updated to state that the CLI supports single-database and data-estate (multi-connection) assessment.

---

## 4. Implementation notes

- **Config:** Extend to hold `connections: list[str]` (and optionally `connections_file: Path`). When multiple connections are set, pipeline loops over them (or fans out), then merges into one report.
- **Report builder:** Add a path that builds an estate report from a list of (connection_fingerprint, results, inventory) and optional aggregate summary; markdown renderer outputs per-connection sections and estate summary.
- **Backward compatibility:** Single `-c` (or `AIRD_CONNECTION_STRING` only) → single connection list → existing report builder and shape.
- **Failure handling:** If one connection fails (discover or run), implementation may fail fast, or continue and record errors per-connection in the report; spec should define preferred behavior (e.g. continue and mark failed connection in report).

---

## 5. Implementation (2026-02-10)

- **Config:** `connections: list[str]`, `get_connections()`; `with_args(connections=...)`.
- **CLI:** `-c` / `--connection` is repeatable (action="append"); `--connections-file` and `AIRD_CONNECTIONS_FILE`; `_resolve_assess_connections()` builds list from file + args.
- **Pipeline:** `run_assess()` uses `config.get_connections()`; single connection → `_run_assess_single()` (unchanged); multiple → `_run_assess_estate()` (loop discover → run per connection, continue on error; then `build_estate_report(platforms)`).
- **Report:** `build_estate_report(platforms)`; `report_to_markdown()` delegates to `_estate_report_to_markdown()` when report has `platforms`.
- **Failure handling:** Estate continues on connection failure and records `error` in that platform entry.

## 6. References

- Conversation: user requested multi-connection/estate support as crucial for value and capabilities; log and spec updates first, then implementation.
- CLI spec section 4.1 (assess) and section 3 (artifacts); project spec Layer 2 and outcomes.
