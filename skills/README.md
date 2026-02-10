# Skills

Step-by-step guidance for the AI-Ready Data assessment workflow. Each skill is a **SKILL.md** that tells the agent when to load it, what to do, and what is forbidden.

**Spec:** [docs/specs/agentic-system-spec.md](../docs/specs/agentic-system-spec.md) defines the skill model, AGENTS.md, and boundaries.

## Layout

- **SKILL.md** (this directory) — Parent workflow: assess-data. Intent routing and when to load each sub-skill.
- **connect/** — Establish connection; help user with connection string and drivers.
- **discover/** — Run discovery, present scope, confirm with user.
- **assess/** — Run assessment (assess or composable discover/run/report/save).
- **interpret/** — Walk through report, triage failures.
- **interview/** — Phases 1–3: questions before connect, after discover, after results.
- **remediate/** — Generate fix suggestions from factor docs and remediation templates; never execute.
- **compare/** — History and diff between runs.
- **references/** — Shared reference docs: [platforms.md](references/platforms.md) (connection strings, drivers), [cli-commands.md](references/cli-commands.md) (command and flag quick reference), [context-file.md](references/context-file.md) (context YAML usage).

## How to use

1. **As an agent:** Start at [AGENTS.md](../AGENTS.md) at repo root, then load [SKILL.md](SKILL.md) and the sub-skill for the current step.
2. **Adding a skill:** Create a directory (e.g. `skills/my-skill/`), add `SKILL.md` with: when to load, prerequisites, steps, forbidden actions. Optionally add `.env.example`. Update the parent [SKILL.md](SKILL.md) intent table if it’s a new entry point.
3. **References:** Put shared content (e.g. platform connection formats) in `references/` and point to it from skills so there’s a single source of truth.
