# Review: Agent and skills layer

**Date:** 2026-02-10  
**Scope:** AGENTS.md, skills/ (parent + connect, discover, assess, interpret, interview, remediate, compare), skills/references/platforms.md.  
**Purpose:** Identify gaps, duplication, and areas to strengthen.

---

## 1. Duplication (acceptable or to trim)

| Area | Where | Note |
|------|--------|------|
| **Forbidden actions** | AGENTS.md, parent SKILL.md, every sub-skill | Repeated on purpose so the agent sees constraints in context when loading a single skill. **Keep.** |
| **Stopping points** | AGENTS.md § Stopping points; parent SKILL.md § Stopping Points | Nearly same content. AGENTS is short; parent is in workflow order. **Optional:** Add "See skills/SKILL.md for full list" in AGENTS to avoid drift. |
| **Workflow (7 steps)** | AGENTS.md § Workflow; parent SKILL.md § Workflow | AGENTS = one line per step; parent = Load X, STOP, Output. Different granularity. **Keep both.** |
| **Install / setup** | AGENTS Quick start, parent Setup, connect Prerequisites | "pip install -e .", DuckDB included. Repeated so each doc stands alone. **Keep.** |
| **Intent routing** | AGENTS Quick start step 3; parent Intent Detection table | AGENTS = short list; parent = full table. Parent is canonical. **Keep.** |

**Verdict:** Duplication is mostly intentional. No need to remove; optional cross-link from AGENTS stopping points to parent.

---

## 2. Gaps

| Gap | Where | Recommendation |
|-----|--------|------------------|
| **CONTRIBUTING.md missing** | connect: "see CONTRIBUTING for adding platforms"; discover: "when the CLI supports it" | CONTRIBUTING doesn't exist yet. **Option A:** Add a stub CONTRIBUTING.md that says "Platform addition TBD; see docs/specs." **Option B:** Change connect to "See repo docs for adding platforms when available." |
| **Context file format** | Multiple skills mention `--context` / AIRD_CONTEXT; no schema or location doc | CLI already supports --context. **Add:** Either a short "Context file" subsection in CLI spec or a docs note (path, optional keys: scope, exclusions, target_level). Remediation templates location is TBD in spec; document when added. |
| **not_assessed in report** | interpret Step 4: "If the report includes a not_assessed section" | Current report has no `not_assessed`. **Clarify:** Add "(when present)" or "Report may include a not_assessed section in future; if so, explain …". |
| **Remediation templates location** | remediate: "e.g. under agent/remediation/ or remediation/" | No such dirs yet. **Keep** the "when present" wording; add one line: "Templates are optional; when added, location will be documented in the spec or README." |
| **Failure handling** | discover, assess | No guidance if `aird discover` or `aird assess` fails (e.g. connection refused). **Add:** One line in discover and assess: "If the command fails, report the error to the user and do not proceed; suggest checking connection string, driver, or network." |
| **Using connection in commands** | discover, assess | Examples use `-c "<connection>"` but don't say to substitute or use env. **Add:** "Use the connection string from the connect step, or ensure AIRD_CONNECTION_STRING is set so -c can be omitted." (CLI spec already says connection required unless env set.) |
| **aird vs python -m agent.cli** | Sub-skills show `aird` only | If the user didn't install the script, they need `python -m agent.cli`. **Add:** In connect (or references/platforms) one line: "If `aird` is not on PATH, use `python -m agent.cli` instead." AGENTS and README already mention both. |

---

## 3. Strengthen

| Area | Suggestion |
|------|------------|
| **Progressive disclosure** | interview Phase 1 says "use progressive disclosure" but not how. Add: "Ask 1–2 questions at a time; expand based on answers so the user isn't overwhelmed." |
| **Re-assess after fixes** | remediate Output mentions "re-assess with --compare after they apply fixes." Make the loop explicit in parent or assess: e.g. "After the user applies fixes, run assess again with --compare (and optionally same --context) to show progress." |
| **Interpret: report source** | interpret Prerequisites say "report (file or from last run)" and "load by id." Clarify: "If the user has a report file from a previous run, use that; otherwise use `aird report --id <id>` to load from history, or use the report path from the last assess step." |
| **Compare: history output format** | compare Step 1 describes "id, timestamp, scores, connection fingerprint." CLI outputs tab-separated. Add: "Output is tab-separated: id, created_at, L1%, L2%, L3%, connection_fingerprint." so the agent parses correctly. |
| **CLI quick reference** | Optional: Add `skills/references/cli-commands.md` with a one-line summary per command and main flags, and point skills to it. Would reduce repeated flag lists; not required for v0. |

---

## 4. Consistency check

- **CLI spec vs skills:** Flags and env vars in skills match CLI spec (assess: --no-save, --compare, --context, --suite, --interactive; discover: -o, --schema, --tables; report: --id, -o; history: --connection, -n/--limit; diff: positional ids, --left/--right). **OK.**
- **Report shape:** summary (total_tests, l1_pass, l2_pass, l3_pass, l1_pct, l2_pct, l3_pct), results (list with test_id, factor, requirement, measured_value, l1_pass, l2_pass, l3_pass), user_context (empty for now). Interpret and remediate assume this. **OK.**
- **Six factors:** AGENTS, parent, and interpret use "six factors" and list Clean + five TBD. **OK.**
- **Paths:** All skill-to-skill and skill-to-reference links use relative paths (e.g. `../interview/SKILL.md`, `../../factors/factor-00-clean.md`). **OK.**

---

## 5. Summary

- **Duplication:** Mostly by design; optional small cross-link from AGENTS to parent for stopping points.
- **Gaps to fix:** (1) CONTRIBUTING or softer wording in connect/discover, (2) one-line failure handling in discover and assess, (3) connection string / env reminder in discover and assess, (4) "if aird not on PATH use python -m agent.cli" in connect or references, (5) interpret "not_assessed (when present)" and report source clarification, (6) compare history output format.
- **Strengthen:** Progressive disclosure in interview; explicit re-assess-after-fixes loop; interpret report source; compare output format.
- **Optional:** Context file doc, remediation location note, CLI quick reference in references.

Implementing the fixes and strengthen items above will make the layer more robust without changing the overall structure.
