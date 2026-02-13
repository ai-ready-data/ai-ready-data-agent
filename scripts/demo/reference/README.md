# Reference Fix Scripts

These scripts show what fixes look like for each factor. They are **not** part of the main demo flow.

**Intended use:** Reference material for understanding Snowflake-specific syntax (masking policies, streams, tags, etc.) or for quickly demonstrating before/after without waiting for AI suggestions.

**Main demo flow:** Let Coco read `docs/remediation/*.md` and suggest fixes based on assessment results.

| Script | Factor |
|--------|--------|
| `snowflake_fix_clean.sql` | Clean (nulls, duplicates, constraints) |
| `snowflake_fix_contextual.sql` | Contextual (PKs, FKs, comments) |
| `snowflake_fix_consumable.sql` | Consumable (clustering, search optimization) |
| `snowflake_fix_current.sql` | Current (streams, change tracking, dynamic tables) |
| `snowflake_fix_correlated.sql` | Correlated (tags, lineage) |
| `snowflake_fix_compliant.sql` | Compliant (masking, row access, sensitivity tags) |
