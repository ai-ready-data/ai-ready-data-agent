"""Clean factor suite for DuckDB: requirement keys from factor-00-clean with query templates."""

from agent.platform.registry import register_suite


def _quote(s: str) -> str:
    """Quote identifier for DuckDB (double quotes; escape " as "")."""
    return '"' + str(s).replace('"', '""') + '"'


# Placeholders: {schema_q}, {table_q}, {column_q} — expander substitutes quoted identifiers.
NULL_RATE_TEMPLATE = (
    "SELECT COUNT(*) FILTER (WHERE {column_q} IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
DUPLICATE_RATE_TEMPLATE = (
    "SELECT 1.0 - (SELECT COUNT(*)::DOUBLE FROM (SELECT DISTINCT * FROM {schema_q}.{table_q}) _) / "
    "NULLIF((SELECT COUNT(*)::DOUBLE FROM {schema_q}.{table_q}), 0) AS v"
)
# Numeric columns: fraction of values <= 0 (quantities/amounts should be positive)
ZERO_NEGATIVE_RATE_TEMPLATE = (
    "SELECT COUNT(*) FILTER (WHERE {column_q} <= 0) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
# Numeric columns: fraction of non-null values that fail to cast to DOUBLE (type inconsistency)
TYPE_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT COUNT(*) FILTER (WHERE {column_q} IS NOT NULL AND TRY_CAST({column_q} AS DOUBLE) IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
# String columns that look like dates: fraction of non-null that don't parse as DATE (format inconsistency)
FORMAT_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT COUNT(*) FILTER (WHERE {column_q} IS NOT NULL AND TRY_CAST({column_q} AS DATE) IS NULL) * 1.0 / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)

CLEAN_SUITE = [
    {
        "id": "clean_table_count",
        "factor": "clean",
        "requirement": "table_discovery",
        "query": "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')",
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
    register_suite("common", CLEAN_SUITE)


_register()
