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
]


def _register() -> None:
    register_suite("common", CLEAN_SUITE)


_register()
