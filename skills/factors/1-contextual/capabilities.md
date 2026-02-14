# Factor 1: Contextual — Stack Capabilities

Platform features that support documenting and querying data semantics.

## Capabilities

| Capability | What it enables | Snowflake feature |
|------------|----------------|-------------------|
| **Column comments** | Attach descriptions to columns, queryable via SQL | `COMMENT ON COLUMN` |
| **Table comments** | Attach descriptions to tables, queryable via SQL | `COMMENT ON TABLE` |
| **AI-generated descriptions** | Auto-generate table/column descriptions from data | `SNOWFLAKE.CORTEX.AI_GENERATE_TABLE_DESC` |
| **Constraint declarations** | Declare PKs and FKs as machine-readable relationship metadata | `PRIMARY KEY`, `FOREIGN KEY` |
| **Metadata views** | Query all metadata (types, constraints, comments) via SQL | `information_schema.columns`, `information_schema.table_constraints` |
