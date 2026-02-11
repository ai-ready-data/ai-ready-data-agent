"""Clean factor suite for Snowflake: requirement keys from factor-00-clean, Snowflake-native SQL.

All queries use Snowflake idioms: COUNT_IF (not FILTER), TRY_CAST, quoted identifiers.
Discovery scopes to the connection's database/schema; tests run only on the inventory.
"""

from agent.platform.registry import register_suite


# Placeholders: {schema_q}, {table_q}, {column_q} — expander substitutes double-quoted identifiers.
# Snowflake: COUNT_IF(condition), TRY_CAST for safe conversion.
NULL_RATE_TEMPLATE = (
    "SELECT COUNT_IF({column_q} IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
DUPLICATE_RATE_TEMPLATE = (
    "WITH total AS (SELECT COUNT(*) AS cnt FROM {schema_q}.{table_q}), "
    "distinct_cnt AS (SELECT COUNT(*) AS cnt FROM (SELECT DISTINCT * FROM {schema_q}.{table_q})) "
    "SELECT 1.0 - distinct_cnt.cnt::FLOAT / NULLIF(total.cnt::FLOAT, 0) AS v "
    "FROM total, distinct_cnt"
)
ZERO_NEGATIVE_RATE_TEMPLATE = (
    "SELECT COUNT_IF({column_q} <= 0) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
TYPE_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT COUNT_IF({column_q} IS NOT NULL AND TRY_CAST({column_q} AS DOUBLE) IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
FORMAT_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT COUNT_IF({column_q} IS NOT NULL AND TRY_CAST({column_q} AS DATE) IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)

# Exclude system schemas (Snowflake returns uppercase; UPPER() for robustness).
CLEAN_TABLE_COUNT_QUERY = (
    "SELECT COUNT(*) AS cnt FROM information_schema.tables "
    "WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG')"
)

CLEAN_SNOWFLAKE_SUITE = [
    {
        "id": "clean_table_count",
        "factor": "clean",
        "requirement": "table_discovery",
        "query": CLEAN_TABLE_COUNT_QUERY,
        "target_type": "platform",
    },
    {
        "id": "null_rate",
        "factor": "clean",
        "requirement": "null_rate",
        "query_template": NULL_RATE_TEMPLATE,
        "target_type": "column",
    },
    {
        "id": "duplicate_rate",
        "factor": "clean",
        "requirement": "duplicate_rate",
        "query_template": DUPLICATE_RATE_TEMPLATE,
        "target_type": "table",
    },
    {
        "id": "zero_negative_rate",
        "factor": "clean",
        "requirement": "zero_negative_rate",
        "query_template": ZERO_NEGATIVE_RATE_TEMPLATE,
        "target_type": "column",
    },
    {
        "id": "type_inconsistency_rate",
        "factor": "clean",
        "requirement": "type_inconsistency_rate",
        "query_template": TYPE_INCONSISTENCY_RATE_TEMPLATE,
        "target_type": "column",
    },
    {
        "id": "format_inconsistency_rate",
        "factor": "clean",
        "requirement": "format_inconsistency_rate",
        "query_template": FORMAT_INCONSISTENCY_RATE_TEMPLATE,
        "target_type": "column",
    },
]


def _register() -> None:
    register_suite("common_snowflake", CLEAN_SNOWFLAKE_SUITE)


_register()
