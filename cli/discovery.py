"""Discovery service: connect, introspect, apply filters, return inventory."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from agent.platform import get_platform
from agent.platform.executor import execute_readonly


def _discover_sqlite(conn: Any) -> dict:
    """SQLite: use sqlite_master and pragma table_info; schema is 'main' for default DB."""
    tables_rows = execute_readonly(
        conn,
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
    )
    schema_name = "main"
    schemas_seen: set[str] = set()
    tables_list: list[dict] = []
    for row in tables_rows:
        table_name = row[0] if isinstance(row, (tuple, list)) else row["name"]
        full_name = f"{schema_name}.{table_name}"
        schemas_seen.add(schema_name)
        tables_list.append({"schema": schema_name, "table": table_name, "full_name": full_name})

    columns_list: list[dict] = []
    for t in tables_list:
        # pragma table_info returns (cid, name, type, notnull, dflt_value, pk)
        rows = conn.execute(f'PRAGMA table_info("{t["table"]}")').fetchall()
        for r in rows:
            col_name = r[1]
            col_type = r[2] if len(r) > 2 else ""
            columns_list.append({
                "schema": t["schema"],
                "table": t["table"],
                "column": col_name,
                "data_type": col_type,
            })

    return {
        "schemas": sorted(schemas_seen),
        "tables": tables_list,
        "columns": columns_list,
    }


def discover(
    connection_string: str,
    *,
    schemas: Optional[List[str]] = None,
    tables: Optional[List[str]] = None,
    context: Optional[Dict] = None,
) -> dict:
    """Produce inventory (schemas, tables, columns) from connection. Applies schema/table filters."""
    name, conn, _ = get_platform(connection_string)
    if name == "sqlite":
        raw = _discover_sqlite(conn)
        # Apply filters
        if schemas or tables:
            tables_list = [t for t in raw["tables"] if (not schemas or t["schema"] in schemas) and (not tables or t["full_name"] in tables)]
            columns_list = [c for c in raw["columns"] if any(t["schema"] == c["schema"] and t["table"] == c["table"] for t in tables_list)]
            schemas_seen = {t["schema"] for t in tables_list}
            return {"schemas": sorted(schemas_seen), "tables": tables_list, "columns": columns_list}
        return raw

    try:
        # Platform-agnostic: use information_schema if available (DuckDB, Snowflake, etc.)
        tables_rows = execute_readonly(
            conn,
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_schema, table_name",
        )
    except Exception as e:
        # Known fallback: some platforms (e.g. older DuckDB) restrict system schema filtering;
        # retry without the WHERE clause exclusion
        logger.debug(
            "information_schema query with schema filter failed, retrying without filter: %s", e
        )
        tables_rows = execute_readonly(
            conn,
            "SELECT table_schema, table_name FROM information_schema.tables ORDER BY table_schema, table_name",
        )
    schemas_seen: set[str] = set()
    tables_list: list[dict] = []
    # Normalize table filters: accept both "TABLE" and "SCHEMA.TABLE" formats
    tables_upper = {t.upper() for t in (tables or [])} if tables else None
    for row in tables_rows:
        schema_name = row[0] if isinstance(row, (tuple, list)) else row["table_schema"]
        table_name = row[1] if isinstance(row, (tuple, list)) else row["table_name"]
        full_name = f"{schema_name}.{table_name}"
        if schemas and schema_name not in schemas:
            continue
        # Match by full name OR just table name (case-insensitive)
        if tables_upper:
            if full_name.upper() not in tables_upper and table_name.upper() not in tables_upper:
                continue
        schemas_seen.add(schema_name)
        tables_list.append({"schema": schema_name, "table": table_name, "full_name": full_name})

    columns_list: list[dict] = []
    for t in tables_list:
        try:
            # Use string literals instead of params for cross-platform compatibility
            # (DuckDB uses ?, Snowflake uses %s or :name - this avoids the issue)
            schema_escaped = t["schema"].replace("'", "''")
            table_escaped = t["table"].replace("'", "''")
            cols = execute_readonly(
                conn,
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{schema_escaped}' AND table_name = '{table_escaped}' ORDER BY ordinal_position",
            )
        except Exception as e:
            # Fallback: skip columns for this table if column discovery fails
            logger.warning("Could not discover columns for %s.%s: %s", t["schema"], t["table"], e)
            cols = []
        for c in cols:
            col_name = c[0] if isinstance(c, (tuple, list)) else c["column_name"]
            col_type = c[1] if isinstance(c, (tuple, list)) else c.get("data_type", "")
            columns_list.append({
                "schema": t["schema"],
                "table": t["table"],
                "column": col_name,
                "data_type": col_type,
            })

    return {
        "schemas": sorted(schemas_seen),
        "tables": tables_list,
        "columns": columns_list,
    }
