# Context file

Optional YAML file used to pass scope, exclusions, and overrides into the CLI. Via `--context` or `AIRD_CONTEXT`.

**Purpose:** Scope (schemas/tables to include or exclude), target workload level, and optional overrides (e.g. nullable-by-design columns, PII, freshness SLAs) so the agent and CLI don't re-ask on every run.

**Canonical definition:** [docs/specs/cli-spec.md](../../docs/specs/cli-spec.md) § Configuration — "Optional YAML file (scope, exclusions, target level, nullable-by-design, PII overrides, freshness SLAs)."

**Persistence:** The CLI may save context per connection under `~/.aird/contexts/` so users don't re-enter on re-run. Path and schema details may be extended in a future spec.

**Usage:** When the user has confirmed scope or overrides in the interview, you can write a YAML file (or use an existing one) and pass it with `--context <path>` on discover, run, or assess.
