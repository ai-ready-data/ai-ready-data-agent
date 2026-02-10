# Design: CLI composability and flow

This document analyzes the current assess flow, its limitations, and a design that maximizes both **utility** (simple one-shot use) and **flexibility** (composable steps, arbitrary ordering where it makes sense). It informs the CLI spec.

---

## Current flow and where it's limiting

Today the CLI has one main pipeline:

**assess:** connect → discover → generate tests → execute → score → report → (optional) save → output

- **Rigid:** The user cannot run only discovery and get an inventory to inspect or edit. They cannot run only execution with a pre-defined scope. They cannot re-score or re-render a report from existing results without re-running the whole pipeline.
- **Escape hatches:** `--dry-run` (stop after generate; no execute) and `--no-save` (skip persistence). That helps preview but doesn't expose intermediate artifacts (inventory, test list, raw results) as first-class outputs.
- **Consequence:** Scripts and agents must either run the full pipeline or nothing. Power users cannot "discover once, tweak scope, then run tests" or "re-report from last run with different format."

So the flow is **limiting** whenever someone needs a subset of steps or wants to re-use outputs of one step as input to another (possibly in a different session or tool).

---

## Design principles

1. **Single responsibility per command** — Each command does one main thing. A high-level command can compose others, but the primitives are available.
2. **Explicit inputs and outputs** — Steps consume and produce well-defined artifacts (inventory JSON, test list, results JSON, report). That enables file-based and stream-based composition and scripting.
3. **Composability** — The same outcome as `assess` can be achieved by chaining: discover → run → report → save (if desired). No step is only available inside the monolith.
4. **Convenience preserved** — One-shot `assess` remains the default for "run everything"; it is equivalent to running the composed steps with sensible defaults.
5. **Idempotency where possible** — Commands that only read or only transform (e.g. report from existing results) can be re-run safely.
6. **Standard artifacts** — Intermediate and final outputs use stable JSON (or documented) shapes so that other tools or agents can consume them.

---

## Data flow (artifacts)

| Artifact | Produced by | Consumed by | Description |
|----------|-------------|-------------|-------------|
| **Inventory** | discover | run, (report for not_assessed) | Schemas, tables, columns; scope and metadata. |
| **Test list** | generate (internal to run or assess) | execute | List of tests (factor, requirement, query, target). Optional first-class output for debugging or custom execution. |
| **Results** | execute | score → report | Raw test results (per test: pass/fail per workload, measured value, thresholds). |
| **Report** | score / report | save, output, diff | Full report (summary, factor scores, tests, environment, user_context). |

So the pipeline is: **connection + context** → discover → **inventory** → generate → **tests** → execute → **results** → score → **report** → (optional) save, output.

---

## Proposed command set

### Primitive (composable) commands

- **discover** — Connect and discover only. **Input:** connection, schema/table filters, context. **Output:** inventory (JSON to stdout or file). No tests, no execution. Use case: inspect scope, feed into run, or integrate with external tooling.
- **run** — Generate tests from an inventory and execute them. **Input:** connection, inventory (from file or from discover via stdin), suite, thresholds, context. **Output:** results (JSON to stdout or file). Use case: "I have an inventory (from discover or from elsewhere); run tests only." Enables re-run with same scope without re-discovering.
- **report** — Build and optionally output a report from results (and inventory). **Input:** results (file or stdin), inventory (file; or embedded in results if we define that), thresholds, context. **Output:** report (JSON or markdown to stdout/file). Use case: re-score with different thresholds, re-render in a different format, or produce report from stored results without re-executing.
- **save** — Persist a report to local history (SQLite). **Input:** report (file or stdin). **Output:** assessment id. Use case: save a report produced by report or by assess for later history/diff.

### Convenience commands

- **assess** — Full pipeline in one shot: discover (in memory) → run → report → (optional) save → output. Same behavior as today; can be specified as "equivalent to: discover then run then report then [save if not --no-save] then output." Keeps the "one command" UX; flags (--dry-run, --no-save, --compare, etc.) unchanged in spirit.
- **history** — List saved assessments (from SQLite). Optional filters: connection, limit. Unchanged.
- **diff** — Compare two reports. **Input:** two assessment ids, or two report files. More flexible than "last two only" (e.g. diff id1 id2 or diff --left report1.json --right report2.json).
- **connect** — Test connection only; output connection info (e.g. platform, version). Use case: "can I reach the DB?" without discovery.
- **generate** — From inventory (and suite), output test list only (no execute). Use case: inspect or export the set of tests that would run; or feed into a custom executor. Lower priority than discover/run/report.

---

## How this gives maximum flexibility and utility

- **Utility:** `aird assess -c $CONN` still does the full job. Default path is unchanged.
- **Flexibility:**
  - "Only discover": `aird discover -c $CONN -o inventory.json`.
  - "Discover, then run with that scope": `aird discover -c $CONN -o inv.json` then `aird run -c $CONN --inventory inv.json -o results.json`.
  - "Re-report from last run": load saved report by id and re-output (already possible via history + report from file if we add report --id).
  - "Re-score with different thresholds": `aird report --results results.json --inventory inv.json --thresholds strict.json -o report.json`.
  - Agents can run discover, present scope to the user, then run only after confirmation; or run once and then report multiple times with different options.
- **Software design:** Primitives are single-purpose; the pipeline is a composition. Artifacts are explicit, so the system is testable (each command can be tested with fixed inputs) and integrable (other tools can produce or consume the same JSON).

---

## Implementation note

The existing codebase already has separate functions (connect, discover, execute_all, build_report, save_assessment). The CLI layer today only wires them in one path. The spec can define the composable commands and their inputs/outputs; implementation can either (a) add new subcommands that call the same functions and add file/stdin I/O for inventory and results, or (b) refactor assess to call discover, run, report, save as sub-flows. Either way, the **contract** (command set, artifacts, flags) is what the CLI spec should define so that flexibility is part of the design, not an afterthought.
