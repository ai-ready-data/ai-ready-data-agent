# Agentic system specification

This document specifies the **agent and skills layer** for the AI-Ready Data assessment system. It defines how a coding agent (or human) discovers and runs the assessment workflow, the role of AGENTS.md and skills, and the boundaries between the CLI (which runs tests and produces artifacts) and the agentic layer (which orchestrates and guides). It complements the [project spec](project-spec.md).

> **Note:** The `aird` CLI and its specifications live in the separate [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repository.

---

## 1. Scope and role

**Scope:**

- **In scope:** Agent responsibilities; skill model (parent and sub-skills, SKILL.md contract); AGENTS.md as the playbook; how a coding agent discovers and runs the workflow; repo layout for skills and references; boundaries (read-only, no remediation execution, config via env/connection).
- **Out of scope:** Implementation of a specific agent runtime or UI; the content of factor or remediation docs (those are defined by the factor spec and remediation templates); CLI implementation details (see the ai-ready-data-cli repo).

**Role of the agentic system:**

An **agent** (in this spec: a coding agent such as Cortex Code CLI, Cursor, Windsurf, Claude Code, or a human following the same playbook) orchestrates:

1. **Assessment** — Runs assessment SQL from factor skills, or invokes the `aird` CLI (if available) to run tests and produce artifacts.
2. **Skills** — Markdown-based guidance that says when to run which step, what to ask the user, and what is forbidden.
3. **User interaction** — Interview phases (pre-connect, post-discover, post-results), scope confirmation, and remediation presentation.
4. **Framework and remediation** — Reads factor docs and remediation patterns to interpret results and suggest fixes.

The agent uses skills as its playbook. If the CLI is available, it can be used as a tool for automated test execution. Without the CLI, the agent can still perform assessments by running SQL directly.

---

## 2. Agent responsibilities

The agent (human or coding agent) is expected to:

- **Follow the playbook** — Use AGENTS.md as the primary entry and follow the defined steps and stopping points.
- **Load skills when appropriate** — Use workflow skills (discover, assess, interpret, remediate) and factor skills as specified in the parent workflow and in each SKILL.md's "When to load."
- **Remain read-only** — Never run SQL or commands that create, modify, or delete data in the user's data source. Never execute remediation; only suggest it for the user to review and run.
- **Honor STOP points** — When the playbook or a skill says STOP, wait for explicit user confirmation or input before proceeding.
- **Use configuration correctly** — Obtain connection strings and secrets from the user or from environment (e.g. `AIRD_CONNECTION_STRING`); never log or store credentials in plain text except where the user explicitly requests it (e.g. a context file they control).

The agent is **not** required to implement any of the assessment logic itself; it only orchestrates and interprets.

---

## 3. Skill model

### 3.1 Overview

**Skills** are first-class guidance units containing portable knowledge. Factor definitions, assessment SQL, thresholds, remediation patterns, and workflow guides — everything an agent needs to assess data. Each skill is a markdown file describing when to load, prerequisites, steps, and forbidden actions. Skills do not implement assessment logic; they tell the agent what to do and what not to do.

- **Parent skill** — One top-level workflow (e.g. assess-data) that covers the full flow: gather context → connect → discover → assess → interpret → remediate. It defines intent routing (e.g. "user has connection string → skip to connect") and when to load which sub-skill.
- **Workflow skills** — discover, assess, interpret, remediate. Each has a markdown file with:
  - **When to load** — User situation or trigger.
  - **Prerequisites** — e.g. connection available, schema enumerated.
  - **Steps** — What to do (ask user, run SQL, load another skill).
  - **Forbidden actions** — e.g. never log credentials, never run write SQL.

Skills may reference shared platform docs from `skills/platforms/` so that platform details live in one place.

### 3.2 SKILL.md contract

Each SKILL.md should contain, in any order but clearly present:

| Element | Description |
|--------|-------------|
| **Identity** | Skill name and short description. |
| **When to load** | Conditions or user intents that indicate this skill should be used. |
| **Prerequisites** | What must be true before starting (e.g. connection available, scope confirmed). |
| **Steps** | Numbered or ordered steps. Each step may say "Load factors/X.md", "Run SQL …", "Ask user …", or "STOP: wait for …". |
| **Forbidden actions** | List of things the agent must never do (e.g. never execute remediation SQL, never store credentials in plain text). |

### 3.3 Discovery

How an agent discovers "what to do":

1. **Entry** — User or docs point to **AGENTS.md** at repo root. AGENTS.md is the playbook: "You are an AI-ready data assessment agent …" and outlines the full workflow.
2. **Workflow** — From AGENTS.md, the agent follows the steps. When a step says "Load skill X", the agent reads the corresponding markdown file (e.g. `skills/workflows/discover.md`).
3. **Intent routing** — The parent skill may define a table or list: "If user situation A → load discover; if B → load assess; …". The agent uses that to jump to the right workflow step when appropriate.

No separate "skill registry" or runtime is required; discovery is by path and by following the playbook.

---

## 4. AGENTS.md

**AGENTS.md** lives at the **repository root**. It is the single playbook for coding agents.

It must:

- **Identify the agent's role** — e.g. "You are an AI-ready data assessment agent. You assess and advise; you never create, modify, or delete data in the user's database."
- **State the high-level workflow** — e.g. understand data estate → discover and confirm scope → assess → interpret results → suggest remediation (user executes).
- **Define stopping points** — Where the agent must wait for user confirmation or input (e.g. after discovery, before running tests).
- **Point to artifacts and docs** — Where to find the framework (factors), platform SQL, and workflow guides.
- **Remind of constraints** — Read-only, no credentials in logs, use env/connection string for config.

AGENTS.md tells the agent *when* and *why* to run assessment steps and *how* to interact with the user.

---

## 5. Boundaries

| Boundary | Rule |
|----------|------|
| **Assessment vs skills** | Factor skills define what to check and how to check it. Workflow skills describe the sequence and user interaction. Skills do not implement scoring logic. |
| **Remediation** | Factor skills include remediation patterns. The agent **suggests** remediation (e.g. by presenting SQL from factor docs). The **user** reviews and executes. The agent never runs remediation SQL or write commands. |
| **Config** | Connection strings and secrets come from the user or from environment (e.g. `AIRD_CONNECTION_STRING`). The agent does not invent credentials. Optional context file (e.g. YAML) is supplied by the user or written with user consent; credentials are not stored in plain text in code or logs. |
| **Data source** | The agent never creates, modifies, or deletes data in the user's data source. Read-only only. |

---

## 6. Repository layout

Target layout for the agentic layer:

- **AGENTS.md** — At repo root. Playbook for coding agents.
- **skills/** — At repo root. Portable knowledge:
  - **skills/SKILL.md** — Universal entry point: intent routing, workflow steps, when to load sub-skills.
  - **skills/factors/** — Single source of truth for factor definitions. Each file (e.g. `0-clean.md`) contains requirements, thresholds, assessment SQL, interpretation, remediation, and stack capabilities.
  - **skills/platforms/** — Platform-specific SQL patterns and connection details (e.g. `snowflake.md`).
  - **skills/workflows/** — Step-by-step workflow guides: discover, assess, interpret, remediate.
  - **skills/audit/** — Optional audit logging skill.
  - **skills/README.md** — Architecture explanation, how to add a platform, how to fork for a new domain.
- **docs/specs/agentic-system-spec.md** — This spec.

The **aird CLI** (test execution, reporting, storage) lives in the separate [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repository. That repo contains its own CLI-specific agent skills that reference this repo's factor and workflow skills for domain knowledge.

---

## 7. Implementation notes

- Skills are markdown and optional support files (e.g. `.sql`); no separate skill runtime or interpreter is required. The agent (e.g. Cursor) reads the markdown and follows it.
- Remediation patterns live in `skills/factors/` as part of each factor's documentation. The agent uses them for suggestions and never executes them.
- The `aird` CLI (in the ai-ready-data-cli repo) can be used as a tool by agents for automated test execution, but is not required. Any agent that can execute SQL can perform assessments directly using the factor skills.
