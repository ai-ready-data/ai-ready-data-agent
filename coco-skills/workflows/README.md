# Workflow Sub-Skills

Step-by-step guides for each phase of AI-ready data assessment.

## Workflows

| Workflow | Purpose | When to Use |
|----------|---------|-------------|
| [discover.md](discover.md) | Find and scope data assets | Start of assessment |
| [assess.md](assess.md) | Execute measurement queries | After scope confirmed |
| [interpret.md](interpret.md) | Apply thresholds, score results | After queries complete |
| [remediate.md](remediate.md) | Generate fix recommendations | After failures identified |

## Typical Flow

```
1. discover  → Confirm database, schema, tables, workload level
2. assess    → Run SQL queries for each factor requirement
3. interpret → Compare to thresholds, calculate scores
4. remediate → Generate SQL fixes for failures (with user approval)
```

## Usage

Load the appropriate workflow when entering that phase:
- User says "assess my data" → Start with `discover.md`
- User says "what failed?" → Use `interpret.md`
- User says "fix the issues" → Use `remediate.md`
