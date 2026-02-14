# Factor 0: Clean — Stack Capabilities

Platform features that support data cleanliness assessment and enforcement.

## Capabilities

| Capability | What it enables | Snowflake feature |
|------------|----------------|-------------------|
| **NOT NULL constraints** | Prevent null insertion at the schema level | `ALTER COLUMN SET NOT NULL` |
| **Column defaults** | Auto-fill missing values on insert | `ALTER COLUMN SET DEFAULT` |
| **Data profiling** | Inspect value distributions, null rates, distinct counts | `information_schema.columns`, `COUNT_IF`, `TABLESAMPLE` |
| **Row-level sampling** | Estimate metrics on large tables without full scans | `TABLESAMPLE (N ROWS)` |
| **Streams + tasks** | Trigger quality checks on new data automatically | `CREATE STREAM`, `CREATE TASK` |
| **Alerts** | Notify when a quality metric crosses a threshold | `CREATE ALERT` |