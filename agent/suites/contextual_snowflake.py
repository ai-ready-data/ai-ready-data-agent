"""Contextual factor suite for Snowflake: requirement keys from factor-01-contextual.

Four requirements across four semantic dimensions:
- Structural: primary_key_defined (fraction of tables with a declared PK)
- Business:   semantic_model_coverage (fraction of tables represented in a semantic view)
- Entity:     foreign_key_coverage (fraction of tables with at least one FK)
- Contextual: temporal_scope_present (fraction of tables with temporal columns)

All queries use Snowflake system views (information_schema, SHOW). Results are coverage
fractions (0–1); threshold direction is "gte" (pass when measured >= threshold).

These tests register into common_snowflake (appending to Clean tests).
"""

from agent.platform.registry import register_suite


# --- Structural: primary_key_defined ---
# Fraction of user tables (non-system schemas) that have at least one PRIMARY KEY constraint.
# Uses information_schema.table_constraints which is scoped to the current database.
PRIMARY_KEY_DEFINED_QUERY = (
    "SELECT COUNT(DISTINCT pk.table_name) * 1.0 / NULLIF(COUNT(DISTINCT t.table_name), 0) AS v "
    "FROM information_schema.tables t "
    "LEFT JOIN information_schema.table_constraints pk "
    "  ON t.table_schema = pk.table_schema "
    "  AND t.table_name = pk.table_name "
    "  AND pk.constraint_type = 'PRIMARY KEY' "
    "WHERE UPPER(t.table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG') "
    "  AND t.table_type = 'BASE TABLE'"
)


# --- Business: semantic_model_coverage ---
# Fraction of user tables that are referenced as base tables in at least one semantic view.
# Uses information_schema.semantic_views to detect presence; DESCRIBE SEMANTIC VIEW for
# base-table mapping is not available via SELECT, so we measure "semantic views exist and
# cover this schema" as a ratio of (tables in schemas with semantic views) / (all tables).
# Simpler v1: just check whether any semantic views exist for the assessed schemas.
# Returns fraction: 0.0 if no semantic views exist, or count of semantic views / count of tables
# as a proxy for coverage. This is a starting heuristic; can be refined with DESCRIBE later.
SEMANTIC_MODEL_COVERAGE_QUERY = (
    "SELECT COALESCE("
    "  (SELECT COUNT(*) FROM information_schema.semantic_views), 0"
    ") * 1.0 / NULLIF("
    "  (SELECT COUNT(*) FROM information_schema.tables "
    "   WHERE UPPER(table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG') "
    "   AND table_type = 'BASE TABLE'), 0"
    ") AS v"
)


# --- Entity: foreign_key_coverage ---
# Fraction of user tables that have at least one FOREIGN KEY constraint.
FOREIGN_KEY_COVERAGE_QUERY = (
    "SELECT COUNT(DISTINCT fk.table_name) * 1.0 / NULLIF(COUNT(DISTINCT t.table_name), 0) AS v "
    "FROM information_schema.tables t "
    "LEFT JOIN information_schema.table_constraints fk "
    "  ON t.table_schema = fk.table_schema "
    "  AND t.table_name = fk.table_name "
    "  AND fk.constraint_type = 'FOREIGN KEY' "
    "WHERE UPPER(t.table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG') "
    "  AND t.table_type = 'BASE TABLE'"
)


# --- Contextual: temporal_scope_present ---
# Fraction of user tables that have at least one column with a temporal data type
# (DATE, TIMESTAMP, TIMESTAMP_LTZ, TIMESTAMP_NTZ, TIMESTAMP_TZ, DATETIME)
# or a column name matching temporal patterns (created_at, updated_at, valid_from, etc.).
TEMPORAL_SCOPE_PRESENT_QUERY = (
    "SELECT COUNT(DISTINCT tc.table_name) * 1.0 / NULLIF(COUNT(DISTINCT t.table_name), 0) AS v "
    "FROM information_schema.tables t "
    "LEFT JOIN information_schema.columns tc "
    "  ON t.table_schema = tc.table_schema "
    "  AND t.table_name = tc.table_name "
    "  AND ("
    "    UPPER(tc.data_type) IN ('DATE', 'DATETIME', 'TIMESTAMP', "
    "      'TIMESTAMP_LTZ', 'TIMESTAMP_NTZ', 'TIMESTAMP_TZ') "
    "    OR LOWER(tc.column_name) LIKE '%created_at%' "
    "    OR LOWER(tc.column_name) LIKE '%updated_at%' "
    "    OR LOWER(tc.column_name) LIKE '%valid_from%' "
    "    OR LOWER(tc.column_name) LIKE '%valid_to%' "
    "    OR LOWER(tc.column_name) LIKE '%effective_date%' "
    "    OR LOWER(tc.column_name) LIKE '%expiry_date%' "
    "  ) "
    "WHERE UPPER(t.table_schema) NOT IN ('INFORMATION_SCHEMA', 'PG_CATALOG') "
    "  AND t.table_type = 'BASE TABLE'"
)


CONTEXTUAL_SNOWFLAKE_SUITE = [
    {
        "id": "primary_key_defined",
        "factor": "contextual",
        "requirement": "primary_key_defined",
        "query": PRIMARY_KEY_DEFINED_QUERY,
        "target_type": "platform",
    },
    {
        "id": "semantic_model_coverage",
        "factor": "contextual",
        "requirement": "semantic_model_coverage",
        "query": SEMANTIC_MODEL_COVERAGE_QUERY,
        "target_type": "platform",
    },
    {
        "id": "foreign_key_coverage",
        "factor": "contextual",
        "requirement": "foreign_key_coverage",
        "query": FOREIGN_KEY_COVERAGE_QUERY,
        "target_type": "platform",
    },
    {
        "id": "temporal_scope_present",
        "factor": "contextual",
        "requirement": "temporal_scope_present",
        "query": TEMPORAL_SCOPE_PRESENT_QUERY,
        "target_type": "platform",
    },
]


def _register() -> None:
    register_suite("common_snowflake", CONTEXTUAL_SNOWFLAKE_SUITE)


_register()
