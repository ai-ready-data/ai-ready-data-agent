# Suite-level questions

Questions are loaded **per suite**. When the survey runs, the pipeline resolves the suite (e.g. `common_snowflake` for Snowflake, `common` for DuckDB) and loads questions for that suite.

**Resolution order:**
1. `{suite_name}.yaml` in this directory (e.g. `common_snowflake.yaml`) if it exists
2. Otherwise `default.yaml`

**Adding platform-specific questions:** Create `common_snowflake.yaml` (or the suite name you use) with your list of questions (same YAML shape as `default.yaml`). That suite will then use that file instead of `default.yaml`.
