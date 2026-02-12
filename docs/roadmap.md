# Roadmap

## Planned Features

### Multi-connection / Data Estate Assessment

Assess multiple database connections in a single `aird assess` run, producing a combined report with per-connection sections and an aggregate summary.

**Design:** [docs/log/design-multi-connection-estate.md](log/design-multi-connection-estate.md)

**Key capabilities (when implemented):**

- Repeatable `-c` / `--connection` flag to supply multiple connections
- `--connections-file` flag pointing to a manifest with multiple entries
- Per-connection discover → run, then merged estate report
- Aggregate L1/L2/L3 summary across connections
- Continue-on-error: failed connections recorded in report without aborting the run

