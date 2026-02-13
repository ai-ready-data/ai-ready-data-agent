# Milestone Plan: Blueprint-Manager Patterns for ai-ready-data-agent

**Created:** 2026-02-13  
**Source:** Analysis of `blueprint-manager` repo structure and how its patterns apply to `ai-ready-data-agent`  
**Status:** Proposed  

---

## Context

The `blueprint-manager` repo uses a declarative, template-driven architecture to guide users through complex Snowflake configuration workflows. It solves a similar problem to ours: take domain knowledge, formalize it into machine-readable artifacts, and let an agent (or a render pipeline) produce actionable output.

Our repo has strong domain content (6 factors, thresholds, assessment SQL, remediation patterns) but the agent workflow is largely prose-driven. The patterns below would make assessments repeatable, diffable, and more deterministic across agent runtimes.

---

## Milestones

### M1: Declarative Discovery Questions
**Priority:** High — this is the foundation everything else builds on  
**Effort:** Small  

**What:** Create `definitions/questions.yaml` with every question the agent asks during the discover/scope phase, structured with `answer_title`, `question_text`, `answer_type`, `options`, and `guidance`.

**Why:** Today, discovery questions live as prose in `skills/workflows/discover.md`. Different agent runtimes interpret them differently. A structured manifest makes the questions consistent, machine-readable, and referenceable by other artifacts.

**Questions to formalize:**

| answer_title | question_text | answer_type |
|--------------|---------------|-------------|
| `platform` | What database platform are you using? | multi-select |
| `target_workload` | What AI workload are you targeting? | multi-select |
| `data_products` | Do you organize data into data products? | text |
| `excluded_schemas` | Are there schemas to skip? | list |
| `infrastructure_tools` | Do you use dbt, a data catalog, OpenTelemetry, or Iceberg? | multi-select |
| `pain_points` | What prompted this assessment? | text |
| `factor_scope` | Should we assess all 6 factors or specific ones? | multi-select |
| `critical_tables` | Which tables are most critical for your AI workload? | list |

**Deliverables:**
- [x] `definitions/questions.yaml` — structured question manifest
- [x] Update `skills/workflows/discover.md` to reference the manifest
- [x] Ensure `AGENTS.md` points to the new file

---

### M2: Persist Discovery Answers as Project Artifacts
**Priority:** High — makes assessments repeatable and diffable  
**Effort:** Small  

**What:** After the discover phase, save the user's answers to a YAML file (e.g., `context.yaml` or `assessment-config.yaml`). Define the schema so any agent runtime can produce it.

**Why:** Today, when a user says "I'm on Snowflake, targeting L2, skip the staging schema," that context is ephemeral — it lives only in the conversation. Persisting it means assessments can be re-run, compared over time, and shared across team members.

**File shape:**

```yaml
# AI-Ready Data Assessment Context
# Created: 2026-02-13
# Agent: cortex-code

platform: Snowflake
target_workload: L2
data_products:
  - name: customer_360
    schemas: [ANALYTICS.CUSTOMERS, ANALYTICS.ORDERS]
    owner: data-eng
excluded_schemas: [STAGING, SCRATCH, TEST]
infrastructure_tools: [dbt, Iceberg]
factor_scope: all
critical_tables: [ANALYTICS.CUSTOMERS, ANALYTICS.EVENTS]
```

**Deliverables:**
- [x] Define context file schema (in `docs/specs/` or `definitions/`)
- [x] Update `skills/workflows/discover.md` with instructions to save context
- [x] Update `AGENTS.md` to reference persisted context

---

### M3: Machine-Readable Workflow Manifest
**Priority:** Medium — improves agent determinism  
**Effort:** Small  

**What:** Add a `meta.yaml` (or equivalent) that declares the assessment workflow steps in order, what each step requires as input, and what it produces.

**Why:** `AGENTS.md` describes the workflow in prose: discover, assess, interpret, remediate. But there's no structured manifest an agent can parse to know: "step 2 requires a context file and produces assessment results." A `meta.yaml` makes the workflow programmatically navigable.

**File shape:**

```yaml
workflow_id: ai-ready-data-assessment
name: AI-Ready Data Assessment
steps:
  - id: discover
    skill: workflows/discover.md
    inputs: []
    outputs: [context.yaml]            # YAML in projects/<name>/
    stop: true

  - id: assess
    skill: workflows/assess.md
    inputs: [context.yaml, factors/*.md, platforms/*.md]
    outputs: [aird-results.db]          # SQLite — assessment + factor_scores rows
    side_effects: [aird-audit.jsonl]    # JSONL — query events appended
    stop: true

  - id: interpret
    skill: workflows/interpret.md
    inputs: [aird-results.db, factors/*.md]
    outputs: [report.md]                # Markdown in projects/<name>/reports/
    stop: true

  - id: remediate
    skill: workflows/remediate.md
    inputs: [report.md, factors/*.md]
    outputs: [remediation.sql]          # SQL in projects/<name>/remediation/
    stop: true
```

**Deliverables:**
- [x] `definitions/workflow.yaml` — step manifest with inputs/outputs
- [x] Update `AGENTS.md` to reference the manifest
- [x] Update `skills/README.md` architecture section

---

### M4: Cortex Code Slash Commands
**Priority:** Medium — improves UX for Cortex Code users  
**Effort:** Medium  

**What:** Add `.cortex/commands/` with structured slash commands that map to assessment workflow steps. Mirror the pattern from blueprint-manager.

**Why:** Blueprint-manager exposes `/blueprints:list`, `/blueprints:build`, etc. We should expose `/assess:discover`, `/assess:run`, `/assess:report`, `/assess:compare`. This gives Cortex Code users a discoverable, ergonomic entry point instead of relying on the skill trigger alone.

**Proposed commands:**

| Command | Description | Delegates to |
|---------|-------------|-------------|
| `/assess` | Top-level help — list subcommands | — |
| `/assess:discover` | Run discovery and scope confirmation | `$ai-ready-data` discover workflow |
| `/assess:run` | Execute assessment against scoped tables | `$ai-ready-data` assess workflow |
| `/assess:report` | Interpret results, produce factor scores | `$ai-ready-data` interpret workflow |
| `/assess:fix` | Suggest remediation SQL for failures | `$ai-ready-data` remediate workflow |
| `/assess:compare` | Diff two assessment results | — |
| `/assess:status` | Show current assessment context and progress | — |

**Deliverables:**
- [ ] `.cortex/commands/assess.md` — top-level command
- [ ] `.cortex/commands/assess/discover.md`
- [ ] `.cortex/commands/assess/run.md`
- [ ] `.cortex/commands/assess/report.md`
- [ ] `.cortex/commands/assess/fix.md`
- [ ] `.cortex/commands/assess/compare.md`
- [ ] `.cortex/commands/assess/status.md`

---

### M5: Project-Based Assessment Organization
**Priority:** Medium — enables multi-database and longitudinal use  
**Effort:** Small  

**What:** Introduce a `projects/` directory convention where each assessment project stores its context, results, and reports.

**Why:** If someone assesses multiple databases or wants to track a single database over time, there's currently no organizational structure. Blueprint-manager's `projects/<name>/answers/` + `projects/<name>/output/` pattern solves this cleanly.

**Directory shape:**

```
projects/
└── customer-360-snowflake/
    ├── context.yaml              # Discovery answers (M2) — YAML
    ├── reports/
    │   └── 2026-02-13T14:30.md   # Interpreted report — markdown
    └── remediation/
        └── 2026-02-13T14:30.sql  # Suggested fixes — SQL
```

Assessment results live in SQLite (`~/.snowflake/cortex/aird-results.db`), not in the project directory. Results are queryable across projects; config and reports are per-project documents.

The audit log (`~/.snowflake/cortex/aird-audit.jsonl`) is also global, not per-project.

**Deliverables:**
- [x] Document the project directory convention in `docs/specs/project-structure-spec.md`
- [x] Add `projects/.gitignore` and a `projects/sample/` with example artifacts (context, report, remediation)
- [x] Update `discover.md` and `AGENTS.md` to reference project paths
- [x] Update `.gitignore` for project output directories (`.db`, `.jsonl`)

---

### M6: Factor File Separation of Concerns
**Priority:** Low — valuable refactor but not blocking  
**Effort:** Medium  
**Gate:** Only pursue after M1-M5 validate the direction and M7 confirms the render contract needs it.

**What:** Consider splitting each factor file (e.g., `0-clean.md`) into separate concern files, following blueprint-manager's three-file pattern.

**Why:** Each factor file currently contains static explanation, assessment SQL with placeholders, interpretation rules, remediation patterns, and stack capabilities — all in one file. This works well for human reading and current agent consumption, but limits composability. A render pipeline (M7) would benefit from having SQL templates in separate, parseable files.

**Possible structure (per factor):**

```
skills/factors/0-clean/
├── overview.md           # Why it matters, per-workload tolerance (static)
├── requirements.yaml     # Metric keys, thresholds, directions (structured)
├── assess.sql.jinja      # Assessment SQL templates (renderable)
├── remediate.sql.jinja   # Remediation SQL templates (renderable)
└── capabilities.md       # Stack capabilities table (static)
```

**Trade-off:** The current single-file-per-factor design is simple and agent-friendly. Splitting adds structure but increases file count. Only pursue if M7 (render contract) confirms the need.

**Deliverables:**
- [ ] Design the split structure and document in `docs/specs/factor-spec.md`
- [ ] Prototype with one factor (Factor 0: Clean)
- [ ] Evaluate: does this improve agent behavior or add unnecessary complexity?
- [ ] If validated, migrate remaining factors

---

### M7: Pluggable Render Contract + Reference Implementation
**Priority:** Low — depends on M1, M2; benefits from M6  
**Effort:** Medium  
**Gate:** Only pursue after M1-M5 validate the direction.

**What:** Define a **render contract** — a specification for how any renderer takes a context file + factor templates and produces executable assessment SQL. Then build one reference implementation as a standalone Python script.

**Why:** Today the agent does ad-hoc string substitution at runtime (`{schema}` -> `ANALYTICS`). A formal render contract lets multiple implementations coexist:

| Renderer | Who uses it | How it works |
|----------|-------------|-------------|
| **Agent-native** | Any LLM agent (Cursor, Claude Code, Cortex Code) | Agent reads the contract, performs substitution inline during conversation. Current behavior, but now against a formal spec. |
| **`scripts/render_assessment.py`** | Field teams, Cortex Code CLI users, anyone without the `aird` CLI | Standalone Python script. No agent needed. Takes `context.yaml` + templates, produces `assessment.sql`. |
| **`aird render`** | CLI users | CLI command that already exists conceptually. Implements the same contract. |
| **Future integrations** | dbt, CI/CD, custom tooling | Any tool that can read the contract and produce SQL. |

The abstraction is the **contract**, not the renderer. The contract specifies:

1. **Input:** context file (M2 schema) + factor SQL templates (existing `skills/factors/`)
2. **Output:** executable SQL, scoped to the user's tables/schemas/database
3. **Behavior:** which factors to include (from `factor_scope`), which tables to target (from `data_products` + `critical_tables` - `excluded_schemas`), which thresholds to apply (from `target_workload`)
4. **Template syntax:** placeholder format (`{database}`, `{schema}`, `{table}`, `{column}`), how to iterate over tables/columns, how to handle optional sections

Any renderer that accepts the contract inputs and produces conforming output is valid. This keeps the agent path (no script needed) and the script path (no agent needed) as equal citizens.

**Scope:**
- **Contract spec:** Document in `docs/specs/render-contract.md`
- **Reference implementation:** `scripts/render_assessment.py` — standalone Python, Jinja2-based
- **Input:** `context.yaml` (from M2) + factor SQL templates
- **Output:** `assessment.sql` — single file with all assessment queries, scoped to user's tables
- **Bonus output:** `assessment-report-template.md` — interpreted results template

**Deliverables:**
- [ ] `docs/specs/render-contract.md` — formal specification of inputs, outputs, and behavior
- [ ] `scripts/render_assessment.py` — reference implementation (standalone, no agent dependency)
- [ ] Integration with project directory structure (M5)
- [ ] Test with sample context + Factor 0 SQL
- [ ] Document in `skills/SKILL.md` as an alternative to agent-native substitution
- [ ] Verify CLI (`aird`) can implement the same contract (coordination with cli repo)

---

## Sequencing

```
M1 (Questions)  ──→  M2 (Persist Answers)  ──→  M3 (Workflow Manifest)
                           │                           │
                           ▼                           ▼
                     M5 (Projects)              M4 (Slash Commands)

                     ─── Phase 3 gate: validate Phase 1-2 first ───

                     M7 (Render Contract)  ──→  M6 (Factor Split)
```

**Phase 1 (now):** M1 + M2 — formalize and persist discovery context. Small effort, high impact.  
**Phase 2 (next):** M3 + M4 + M5 — workflow manifest, commands, project structure. Medium effort, improves UX.  
**Phase 3 (later):** M7 first (render contract + reference impl), then M6 (factor split) only if M7 confirms the need. Explicit gate: do not start Phase 3 until Phase 1-2 are shipped and validated with at least one real assessment.

Note on M6/M7 ordering: M7 (render contract) comes before M6 (factor split) because defining the contract will reveal whether the current single-file factor format is sufficient or whether splitting is actually needed. Don't refactor the factors speculatively.

---

## Decisions

### D1: Storage format by concern

**Decision:** Three concerns, three formats — each chosen for how the data is actually used.

| Concern | Format | Location | Why |
|---------|--------|----------|-----|
| **Configuration state** (discovery answers, scope, workload level) | YAML files | `projects/<name>/context.yaml` | Document problem: review it, edit it, share it, diff it, version it. Agents read/write YAML natively. This is the "answer file" equivalent from blueprint-manager. |
| **Assessment results** (factor scores, per-table metrics, pass/fail) | SQLite | `~/.snowflake/cortex/aird-results.db` | Query problem: "compare my last 5 runs", "show score trends", "what's my L2 pass rate over time." Needs JOINs, GROUP BY, aggregations. The queries in `audit/queries.md` already demonstrate this need. |
| **Audit log** (session events, commands, queries, errors) | Append-only JSONL | `~/.snowflake/cortex/aird-audit.jsonl` | Append problem: write-forward, rarely queried, mostly for debugging and compliance. One JSON object per line. Simple, durable, `tail`-able, easy to ship to another system. No schema migration needed — just add fields to new events. |

**Rationale:**

*Configuration* is a document you collaborate on. YAML.

*Results* get queried across time. The existing `queries.md` has score trends, factor breakdowns, platform comparisons, cleanup by date — all relational queries. SQLite.

*Audit events* are a sequential record of "what happened." The current schema puts these in SQLite (`events` table), but events are append-only by nature — you never UPDATE or DELETE an event, you never JOIN events to themselves, and the most common access pattern is "show me what happened in this session" (sequential scan) or "tail the last N events" (read from end). An append-only JSONL file is simpler, more portable, impossible to corrupt with a bad query, and trivially parseable by any tool. If you ever need to query events relationally, you can load the JSONL into SQLite on demand — but you almost never will.

**What changes from the current `audit/schema.sql`:**

The current schema has three tables: `sessions`, `events`, `assessments`. Under this decision:
- `assessments` stays in SQLite (moves to `aird-results.db` with a refined schema)
- `sessions` and `events` move to the JSONL audit log
- The `sessions` concept becomes an envelope in the JSONL — a `session_start` event at the beginning and a `session_end` event at the end, with a `session_id` field on every event in between

**JSONL format: Canonical summary + granular trail**

The format follows a hybrid of [CLEF](https://clef-json.org/) (Compact Log Event Format) for reserved field conventions and [Stripe's canonical log lines](https://stripe.com/blog/canonical-log-lines) for the summary pattern. The key insight from canonical log lines: emit one dense, information-rich event at the *end* of a session that rolls up everything — the "canonical summary." Agents and humans read this line first. Granular events exist for debugging and replay, not for querying.

**Reserved fields (every event):**

| Key | Name | Description |
|-----|------|-------------|
| `@t` | Timestamp | ISO 8601, always UTC. CLEF convention, widely recognized, sorts lexicographically. |
| `sid` | Session ID | Groups events into a session. Appears on every event. |
| `e` | Event type | Short type code: `start`, `q`, `err`, `end`. No log levels — these aren't application logs. |

**Granular events (compact, emitted during session):**

Short keys for high-frequency fields. Flat structure (no nesting) so `grep` and `jq` work without `.field.subfield` paths. Agents parse flat JSON trivially.

```jsonl
{"@t":"2026-02-13T14:30:01Z","sid":"a1b2c3","e":"start","platform":"snowflake","workload":"L2"}
{"@t":"2026-02-13T14:30:02Z","sid":"a1b2c3","e":"q","sql":"SHOW DATABASES","rows":12}
{"@t":"2026-02-13T14:30:05Z","sid":"a1b2c3","e":"q","sql":"SELECT COUNT_IF(email IS NULL)...","tbl":"CUSTOMERS","f":"clean","m":"null_rate","v":0.03}
{"@t":"2026-02-13T14:30:06Z","sid":"a1b2c3","e":"q","sql":"SELECT COUNT_IF(phone IS NULL)...","tbl":"CUSTOMERS","f":"clean","m":"null_rate","v":0.15}
{"@t":"2026-02-13T14:30:10Z","sid":"a1b2c3","e":"err","msg":"Connection timeout","ctx":"assess"}
{"@t":"2026-02-13T14:31:00Z","sid":"a1b2c3","e":"end","tables":15,"factors":6,"score":0.78,"l1":true,"l2":true,"l3":false,"dur_s":59}
```

**Canonical summary (the `end` event):**

The `end` event is the canonical log line for the session. It contains everything you'd want at a glance: table count, factor count, overall score, pass/fail per level, duration. An agent or human running `grep '"e":"end"' aird-audit.jsonl` gets a one-line-per-session summary of every assessment ever run. This is the fast path — drill into granular events only when debugging.

**Granular event field reference:**

| Event (`e`) | Additional fields | Description |
|-------------|-------------------|-------------|
| `start` | `platform`, `workload` | Session begins. Platform and target workload level. |
| `q` | `sql`, `rows`, `tbl`, `f`, `m`, `v` | Query executed. `tbl`=table, `f`=factor, `m`=metric key, `v`=metric value. Factor/metric fields only present on assessment queries. |
| `err` | `msg`, `ctx` | Error. `msg`=error message, `ctx`=workflow phase (discover, assess, interpret). |
| `end` | `tables`, `factors`, `score`, `l1`, `l2`, `l3`, `dur_s` | Canonical summary. Rollup of the full session. |

**Design choices:**

| Choice | Why |
|--------|-----|
| `@t` for timestamp | CLEF convention — recognized by tooling, sorts correctly |
| Short keys (`sid`, `e`, `f`, `m`, `v`, `tbl`) | Compact on disk, fast to scan. Granular events are high-volume. |
| Flat structure (no nesting) | `grep`, `jq`, and agents work without deep paths |
| Canonical `end` event | One-stop-shop for "what happened?" Agent reads `end` first, drills down only if needed. |
| No log levels | Event type (`e`) is more useful than INFO/WARN/ERROR for agent activity |
| New fields additive only | Add new keys to new event types without breaking anything. No schema migration. |

**How agents use the audit log:**

| Task | Command |
|------|---------|
| Last 5 assessments | `grep '"e":"end"' aird-audit.jsonl \| tail -5` |
| Errors in a session | `grep '"sid":"a1b2c3"' aird-audit.jsonl \| grep '"e":"err"'` |
| All Factor 0 (Clean) queries | `grep '"f":"clean"' aird-audit.jsonl` |
| Full session replay | `grep '"sid":"a1b2c3"' aird-audit.jsonl` |
| Sessions that failed L2 | `grep '"e":"end"' aird-audit.jsonl \| grep '"l2":false'` |

**Results SQLite schema (refined):**

```sql
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    platform TEXT,                -- snowflake, duckdb, postgres
    connection_sanitized TEXT,    -- credentials removed
    target_workload TEXT,         -- L1, L2, L3
    scope_json TEXT,              -- JSON array of tables assessed
    results_json TEXT,            -- full factor/requirement scores
    overall_score REAL,           -- 0.0 to 1.0
    l1_pass INTEGER,
    l2_pass INTEGER,
    l3_pass INTEGER
);

CREATE TABLE IF NOT EXISTS factor_scores (
    assessment_id TEXT NOT NULL,
    factor TEXT NOT NULL,         -- clean, contextual, consumable, current, correlated, compliant
    score REAL,
    pass_at_level TEXT,           -- highest level passed: L1, L2, L3, or NONE
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (assessment_id, factor),
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
);
```

This separates the "query scores over time" use case (SQLite) from the "what happened during the run" use case (JSONL) cleanly.

### D2: M6 and M7 sequencing

**Decision:** Phase 3, after Phase 1-2 validate. M7 (render contract) before M6 (factor split).

Defining the render contract will tell us whether the current factor file format is sufficient for template rendering or whether the split is needed. Don't refactor factors speculatively.

### D3: Audit log format — compact JSONL with canonical summaries

**Decision:** Move audit events from SQLite (`events` + `sessions` tables) to an append-only JSONL file (`~/.snowflake/cortex/aird-audit.jsonl`) using a compact format inspired by two industry patterns:

1. **[CLEF](https://clef-json.org/)** (Compact Log Event Format) — `@`-prefixed reserved fields (`@t` for timestamp). Additive-only versioning. Widely supported by log tooling.
2. **[Canonical log lines](https://stripe.com/blog/canonical-log-lines)** (Stripe) — one dense summary event per request/session, emitted at the end. The line you query first. Granular events exist for drill-down, not for primary access.

**Why not plain verbose JSONL?** Audit events are high-volume (one per SQL query during assessment). Verbose keys (`session_id`, `event_type`, `metric_value`) bloat the file and slow scanning. Short keys (`sid`, `e`, `v`) keep lines compact while staying readable. The canonical `end` event uses slightly more descriptive keys (`tables`, `score`, `dur_s`) since readability matters more there and frequency is low (one per session).

**Why not SQLite?** Events are append-only by nature — no UPDATEs, no DELETEs, no JOINs across events. The primary access patterns are `tail` (what just happened?), `grep` by session (replay), and `grep` by field (all errors, all Factor 0 queries). These are text-search problems, not relational problems. A JSONL file is simpler, more durable (can't corrupt with a bad query), and trivially pipeable to any log tool.

Assessment results stay in SQLite because they have a genuinely relational access pattern (compare across runs, aggregate by factor, trend over time).

**Format spec:** See D1 above for the full JSONL format — reserved fields, granular event types, canonical `end` event, field reference, agent usage patterns.

**Impact on `skills/audit/`:**
- `schema.sql` gets simplified: remove `sessions` and `events` tables, keep only the results schema (or move results to its own file)
- `SKILL.md` gets updated: event logging instructions change from SQL INSERT to JSONL file append
- `queries.md` gets split: result queries stay SQL, event queries become `grep`/`jq` one-liners
- New: document the JSONL event format spec (reserved fields, event types, canonical summary pattern, agent access patterns)

### D4: Pluggable renderer

**Decision:** Define the contract, not the renderer. See updated M7.

The render contract is a specification. Multiple implementations can coexist: agent-native substitution (current behavior, zero dependencies), a standalone Python script (for field teams and Cortex Code CLI users), and the `aird` CLI. All are valid implementations of the same contract. This serves the confirmed use case of field teams and Cortex Code CLI users who want assessment SQL without installing the full CLI.

---

## Resolved Questions

1. ~~**Should context files live in the repo or be user-local?**~~ **Resolved:** `.gitignore`'d `projects/` directory in the repo for local use. Users who want to version their assessments can un-ignore specific projects. The `projects/sample/` directory ships with example artifacts and is committed.

2. ~~**How much structure is too much?**~~ **Resolved:** Validate M1-M5 before touching factor file structure. M6 is explicitly gated on M7 confirming the need.

3. ~~**Render pipeline vs. agent-native substitution?**~~ **Resolved:** Both are valid. The render contract (M7) is the abstraction. Agent-native substitution is one implementation; the Python script is another; the CLI is a third. Field teams and Cortex Code CLI users are a confirmed use case for the script path.
