# Design: Onboarding — user supplies specific datasets for their AI workload

**Status:** Design. Assumption and flow; implementation is largely in place.

---

## 1. Core assumption

**The user supplies the specific datasets to assess — the ones that feed (or will feed) their AI workload.**

We do **not** assume "assess everything in the connection." We assume the user has a bounded set of tables/schemas that matter for a given use case (e.g. "the data we use for our RAG app," "the features and labels for our model"). The assessment is scoped to that set so that:

- **Measured tests** run only on those tables/columns (discovery is filtered).
- **Survey questions** are phrased in terms of "the tables in this assessment" / "these datasets," so answers are about that scope.
- **Reports** are interpretable: "this is how AI-ready *this* set of data is," not the entire warehouse.

---

## 2. How the user supplies scope (current)

The user can supply **connection** plus **scope** in several ways; all are supported today.

| Mechanism | Use case | How |
|-----------|----------|-----|
| **CLI flags** | One-off or scripted run | `-c "snowflake://..."` plus `-s schema1 -s schema2` or `-t analytics.features -t analytics.labels` |
| **Context file** | Reusable scope (and optional workload/target_level) | `--context context.yaml` with `schemas:` and/or `tables:` (and optionally other keys). Same scope can be reused across runs. |
| **Connections manifest** | Multi-connection or saved "target list" | `--connections-file targets.yaml` (or default `~/.aird/connections.yaml`). Each entry: `connection` + optional `targets: { schemas: [...], tables: [...] }`. |

So "specific datasets" = **connection + schemas and/or tables**. No new artifact is required; we only need to make this contract explicit in onboarding and docs.

---

## 3. Recommended onboarding flow

1. **Connect** — User has a connection (e.g. Snowflake) and credentials (env or URL).
2. **(Optional) Discover** — Run `aird discover -c "snowflake://..."` to see what schemas/tables exist. Helps the user decide what to include.
3. **Define scope** — User chooses the schemas or tables that correspond to their AI workload (e.g. "analytics.features, analytics.labels" or "schemas: analytics, staging").
4. **Run assess** — `aird assess -c "snowflake://..." -t analytics.features -t analytics.labels --survey` (or use a context file or manifest). Discovery is restricted to that scope; measured tests and survey run against that inventory only.
5. **Survey** — Questions are about "these datasets"; answers are stored in the report.

This flow is already supported. Onboarding docs and prompts should **lead with scope**: "Which datasets do you want to assess? (schemas or table list)."

---

## 4. Naming and reuse

- **"Assessment target"** (internal) = one `{ connection, schemas?, tables? }`. The manifest can hold multiple such targets (estate mode).
- **"AI workload" or "dataset scope"** (user-facing) = the same idea: a named or unnamed set of data the user cares about. Today we don’t require a name; the user can reuse scope via context file or manifest. A future improvement could be a first-class **named target** (e.g. "rag_catalog") in the manifest so the user can run `aird assess --target rag_catalog` without repeating connection and scope.

---

## 5. Workload type (L1 / L2 / L3)

Thresholds and reporting are per workload (L1 = analytics/BI, L2 = RAG, L3 = training). Today the user can pass **target_level** or **workload** in the context file; the report and thresholds already support L1/L2/L3. Onboarding can ask: "What is the primary use case for this data? (Analytics, RAG, or training)" and set context so the report emphasizes the right thresholds. This is optional; default is L1.

---

## 6. What to document or add

- **Demo and runbooks** — Explicitly say: "Scope to the datasets for your AI workload using `-s`/`-t` or a context file." (Done in [docs/demo-snowflake.md](../demo-snowflake.md).)
- **First-run guidance** — In docs or future CLI prompts: "Supply connection and the schemas or tables you want to assess (your AI workload datasets)."
- **Manifest examples** — Example manifest with one connection and a clear `targets: { schemas: [...] }` or `tables: [...]` labeled as "AI workload scope."
- **Optional later** — Named targets in manifest; interactive "pick schemas/tables" step; or a small "onboarding" command that writes a template context/manifest from discover output.

---

## 7. Summary

| Assumption | Supported today |
|------------|------------------|
| User supplies specific datasets to assess | Yes: connection + `-s`/`-t`, context file, or manifest `targets` |
| Scope = AI workload datasets | Yes: discovery and tests are restricted to that scope; survey questions reference "these datasets" |
| Reuse of scope | Yes: context file or connections manifest |
| Workload type (L1/L2/L3) | Yes: context and thresholds; can be surfaced more in onboarding |

No change to the core pipeline is required; the main work is **documentation and framing** so that "supply your AI workload datasets" is the default mental model for onboarding.
