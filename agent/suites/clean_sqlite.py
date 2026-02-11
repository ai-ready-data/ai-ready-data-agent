"""Clean factor suite for SQLite: requirement keys from factor-00-clean with SQLite-compatible query templates."""

from agent.platform.registry import register_suite


# Placeholders: {schema_q}, {table_q}, {column_q} — expander substitutes quoted identifiers.
# SQLite: CAST for float division; no FILTER (use CASE/SUM for null rate).
NULL_RATE_TEMPLATE = (
    "SELECT CAST(SUM(CASE WHEN {column_q} IS NULL THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
DUPLICATE_RATE_TEMPLATE = (
    "SELECT 1.0 - 1.0 * (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM {schema_q}.{table_q})) / "
    "NULLIF((SELECT COUNT(*) FROM {schema_q}.{table_q}), 0) AS v"
)
# Numeric columns: fraction of values <= 0
ZERO_NEGATIVE_RATE_TEMPLATE = (
    "SELECT CAST(SUM(CASE WHEN {column_q} <= 0 THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
# Numeric columns: fraction of non-null that fail TRY_CAST to REAL (SQLite 3.35+)
TYPE_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT CAST(SUM(CASE WHEN {column_q} IS NOT NULL AND TRY_CAST({column_q} AS REAL) IS NULL THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)
# String columns that look like dates: fraction of non-null that don't parse as date (date() returns NULL on invalid)
FORMAT_INCONSISTENCY_RATE_TEMPLATE = (
    "SELECT CAST(SUM(CASE WHEN {column_q} IS NOT NULL AND date({column_q}) IS NULL THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(*), 0) AS v "
    "FROM {schema_q}.{table_q}"
)

CLEAN_SQLITE_SUITE = [
    {
        "id": "clean_table_count",
        "factor": "clean",
        "requirement": "table_discovery",
        "query": "SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'",
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
    register_suite("common_sqlite", CLEAN_SQLITE_SUITE)


_register()
