# Roadmap

## Completed (Phases 1–4)

- Declarative YAML suite definitions with composition
- Requirements registry (single source of truth for thresholds)
- Interactive setup wizard (`aird init`)
- Rich terminal UI (colored tables, progress bars, TTY-gated)
- Interactive assessment mode (`aird assess -i`)
- `aird compare` — side-by-side table comparison
- `aird rerun` — re-run failed tests with delta
- `aird benchmark` — N-way dataset comparison
- `--factor` filtering, `--dry-run` preview, `--survey` questions

## Deferred / Future

- Cross-platform benchmark (e.g., DuckDB vs Snowflake in same benchmark run)
- Plugin system for custom test suites
- Auto-detection from dbt `profiles.yml`
- Full TUI/dashboard mode
- JSON/YAML machine output for benchmark
- Additional factors beyond Clean (Contextual, Consumable, Current, Correlated, Compliant — partially implemented for Snowflake)
- Remediation templates (auto-generated fix suggestions)
- Profile/config management (`aird profile`)

## Removed

- **Multi-connection estate mode** — removed in Phase 1 in favor of simpler single-connection `aird assess` + `aird benchmark` for N-way comparison
