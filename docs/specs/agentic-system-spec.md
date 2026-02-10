# Agentic system specification

This document specifies the **agent and skills layer** for the AI-Ready Data assessment system. It defines how a coding agent (or human) discovers and runs the assessment workflow, the role of AGENTS.md and skills, and the boundaries between the CLI (which runs tests and produces artifacts) and the agentic layer (which orchestrates and guides). It complements the [CLI spec](cli-spec.md) and the [project spec](project-spec.md) Layer 2.

---

## 1. Scope and role

**Scope:**

- **In scope:** Agent responsibilities; skill model (parent and sub-skills, SKILL.md contract); AGENTS.md as the playbook; how a coding agent discovers and runs the workflow; repo layout for skills and references; boundaries (read-only, no remediation execution, config via env/connection).
- **Out of scope:** Implementation of a specific agent runtime or UI; the content of factor or remediation docs (those are defined by the factor spec and remediation templates).

**Role of the agentic system:**

An **agent** (in this spec: a coding agent such as Cortex Code CLI, Cursor, Windsurf, Claude Code, or a human following the same playbook) orchestrates:

1. **CLI** — Runs assessment commands (`aird` or `python -m agent.cli`), consumes and produces artifacts (inventory, results, report).
2. **Skills** — Markdown-based guidance that says when to run which step, what to ask the user, and what is forbidden.
3. **User interaction** — Interview phases (pre-connect, post-discover, post-results), scope confirmation, and remediation presentation.
4. **Framework and remediation** — Reads factor docs and remediation templates to interpret results and suggest fixes.

The CLI does not drive the conversation; the agent does. The agent uses the CLI as a tool and follows the playbook and skills so that assessments are consistent, safe, and useful.

---

## 2. Agent responsibilities

The agent (human or coding agent) is expected to:

- **Follow the playbook** — Use AGENTS.md as the primary entry and follow the defined steps and stopping points.
- **Load skills when appropriate** — Use sub-skills (connect, discover, assess, interpret, interview, remediate, compare) as specified in the parent workflow and in each SKILL.md’s “When to load.”
- **Remain read-only** — Never run SQL or commands that create, modify, or delete data in the user’s data source. Never execute remediation; only suggest it for the user to review and run.
- **Honor STOP points** — When the playbook or a skill says STOP, wait for explicit user confirmation or input before proceeding.
- **Use configuration correctly** — Obtain connection strings and secrets from the user or from environment (e.g. `AIRD_CONNECTION_STRING`); never log or store credentials in plain text except where the user explicitly requests it (e.g. a context file they control).
- **Use the CLI for execution** — Invoke `aird` (or `python -m agent.cli`) for discover, run, report, save, history, diff, suites. Do not reimplement assessment logic; use the CLI’s artifacts (inventory, results, report) as the source of truth.

The agent is **not** required to implement any of the assessment logic itself; it only orchestrates and interprets.

---

## 3. Skill model

### 3.1 Overview

**Skills** are first-class guidance units. Each skill is a directory (or a single file) that contains at least a **SKILL.md** describing when to load the skill, prerequisites, steps, and forbidden actions. Skills do not implement assessment logic; they tell the agent what to do and what not to do, and which CLI commands to run.

- **Parent skill** — One top-level workflow (e.g. assess-data) that covers the full flow: gather context → connect → discover → assess → interpret → remediate/compare. It defines intent routing (e.g. “user has connection string → skip to connect”) and when to load which sub-skill.
- **Sub-skills** — connect, discover, assess, interpret, interview, remediate, compare. Each has a SKILL.md with:
  - **When to load** — User situation or trigger.
  - **Prerequisites** — e.g. agent package installed, connection string available.
  - **Steps** — What to do (ask user, run CLI command, load another skill).
  - **Forbidden actions** — e.g. never log credentials, never run write SQL.
  - Optional: **parent_skill** (e.g. assess-data) for hierarchy.

Skills may reference shared docs (e.g. connection string formats, platform support) from a **references** area so that platform details live in one place.

### 3.2 SKILL.md contract

Each SKILL.md should contain, in any order but clearly present:

| Element | Description |
|--------|-------------|
| **Identity** | Skill name and short description (in frontmatter: `name`, `description`, `parent_skill`). |
| **When to load** | Conditions or user intents that indicate this skill should be used. |
| **Prerequisites** | What must be true before starting (e.g. package installed, connection string obtained). |
| **Steps** | Numbered or ordered steps. Each step may say “Load X/SKILL.md”, “Run CLI command …”, “Ask user …”, or “STOP: wait for …”. |
| **Forbidden actions** | List of things the agent must never do (e.g. never execute remediation SQL, never store credentials in plain text). |

Steps may reference the CLI by example (e.g. `aird discover -c "<connection>" -o inventory.json`). The CLI spec is the authority for flags and behavior.

### 3.3 References

A **references** area (e.g. `skills/references/`) holds shared reference docs that skills point to, for example:

- **Platforms / connection strings** — Supported platforms, connection string format per platform, driver install commands, env var names. Referenced by connect and assess skills so the agent can help the user construct a connection.

Skills reference these by path (e.g. “Load `references/platforms.md`”) so the agent knows where to read. No duplicate platform docs inside individual skills.

### 3.4 Discovery

How an agent discovers “what to do”:

1. **Entry** — User or docs point to **AGENTS.md** at repo root. AGENTS.md is the playbook: “You are an AI-ready data assessment agent …” and outlines the full workflow.
2. **Workflow** — From AGENTS.md, the agent follows the steps. When a step says “Load skill X”, the agent reads the corresponding SKILL.md (e.g. `skills/connect/SKILL.md`).
3. **Intent routing** — The parent skill (e.g. assess-data) may define a table or list: “If user situation A → load connect; if B → load assess; …”. The agent uses that to jump to the right sub-skill when appropriate.

No separate “skill registry” or runtime is required; discovery is by path and by following the playbook.

---

## 4. AGENTS.md

**AGENTS.md** lives at the **repository root**. It is the single playbook for coding agents.

It must:

- **Identify the agent’s role** — e.g. “You are an AI-ready data assessment agent. You assess and advise; you never create, modify, or delete data in the user’s database.”
- **State the high-level workflow** — e.g. understand data estate (interview) → connect → discover and confirm scope → assess → interpret results → suggest remediation (user executes) → compare runs when needed.
- **Define stopping points** — Where the agent must wait for user confirmation or input (e.g. after interview phase, after discovery, before running tests).
- **Point to artifacts and docs** — Where to find the framework (factors), remediation templates, and how to run the CLI (e.g. `aird` or `python -m agent.cli`). Reference the skills directory and references (e.g. platforms) by path.
- **Remind of constraints** — Read-only, no credentials in logs, use env/connection string for config.

AGENTS.md does not replace the CLI spec; it tells the agent *when* and *why* to run CLI commands and *how* to interact with the user. The CLI spec defines the commands and flags.

---

## 5. Boundaries

| Boundary | Rule |
|----------|------|
| **CLI vs skills** | The CLI runs assessments and produces artifacts. Skills describe when and how to call the CLI and what to ask the user. Skills do not implement test logic or scoring. |
| **Remediation** | Tests produce failures; remediation templates (and factor docs) explain how to fix. The agent **suggests** remediation (e.g. by combining report output with template content). The **user** reviews and executes. The agent never runs remediation SQL or write commands. |
| **Config** | Connection strings and secrets come from the user or from environment (e.g. `AIRD_CONNECTION_STRING`). The agent does not invent credentials. Optional context file (e.g. YAML) is supplied by the user or written with user consent; credentials are not stored in plain text in code or logs. |
| **Data source** | The agent and CLI never create, modify, or delete data in the user’s data source. Read-only only. |

---

## 6. Repository layout

Target layout for the agentic layer:

- **AGENTS.md** — At repo root. Playbook for coding agents.
- **skills/** — At repo root (sibling to `agent/`, `factors/`, `docs/`).
  - **skills/SKILL.md** — Parent workflow (e.g. assess-data): intent routing, workflow steps, when to load sub-skills.
  - **skills/connect/SKILL.md**, **skills/discover/SKILL.md**, **skills/assess/SKILL.md**, **skills/interpret/SKILL.md**, **skills/interview/SKILL.md**, **skills/remediate/SKILL.md**, **skills/compare/SKILL.md** — Sub-skills as needed.
  - **skills/references/** — Shared reference docs (e.g. `platforms.md` for connection strings and drivers).
  - **skills/README.md** — How to add or reference skills; points to this spec.
- **docs/specs/agentic-system-spec.md** — This spec.

The **agent** package (CLI and core) remains separate from **skills**; skills reference the CLI and the framework but do not live inside the agent package. The README and AGENTS.md tell users and agents where to find “how to install” and “how to run.”

---

## 7. Alignment with CLI

The agentic layer uses the CLI as follows:

| Agent step | CLI usage |
|------------|-----------|
| Connect | No CLI command; agent helps user construct connection string and set env (e.g. `AIRD_CONNECTION_STRING`). Optional future: `aird connect` to test connection. |
| Discover | `aird discover -c "<connection>"` with optional `-o inventory.json`, `--schema`, `--tables`, `--context`. |
| Assess | `aird assess -c "<connection>"` with optional `--output`, `--no-save`, `--compare`, `--context`, `--suite`, `--interactive`, etc. Or composable: discover → run → report → save. |
| Interpret | Agent reads report (from file or from last run) and factor docs; no CLI required except possibly `aird report --id <id>` to re-output a saved report. |
| Remediate | Agent reads report + remediation templates; suggests edits; user runs them. No CLI for remediation execution. |
| Compare | `aird diff <id1> <id2>` or `aird diff --left <path> --right <path>`; optionally `aird history` to list ids. |

Flags, env vars, and artifact shapes are defined by the [CLI spec](cli-spec.md). This spec does not duplicate them; it only states how the agent uses the CLI in the workflow.

---

## 8. Implementation notes

- The current repo may not yet contain AGENTS.md or a full `skills/` tree. This spec defines the target. Implementation can be incremental (e.g. AGENTS.md first, then parent skill, then sub-skills).
- Skills are markdown and optional support files (e.g. `.env.example`); no separate skill runtime or interpreter is required. The agent (e.g. Cursor) reads the markdown and follows it.
- Remediation templates may live under `agent/remediation/`, `factors/`, or a dedicated `remediation/` directory; the factor spec and project spec define their role. This spec only requires that the agent use them for suggestions and never execute them.
