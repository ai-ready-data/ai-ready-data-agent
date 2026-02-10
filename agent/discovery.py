"""Discovery service: connect, introspect, apply filters, return inventory."""

from typing import Any, Dict, List, Optional

from agent.platform import get_platform
from agent.platform.executor import execute_readonly


def discover(
    connection_string: str,
    *,
    schemas: Optional[List[str]] = None,
    tables: Optional[List[str]] = None,
    context: Optional[Dict] = None,
) -> dict:
    """Produce inventory (schemas, tables, columns) from connection. Applies schema/table filters."""
    _, conn, _ = get_platform(connection_string)
    try:
        # Platform-agnostic: use information_schema if available (DuckDB, Snowflake, etc.)
        tables_rows = execute_readonly(
            conn,
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_schema, table_name",
        )
    except Exception:
        tables_rows = execute_readonly(
            conn,
            "SELECT table_schema, table_name FROM information_schema.tables ORDER BY table_schema, table_name",
        )
    schemas_seen: set[str] = set()
    tables_list: list[dict] = []
    for row in tables_rows:
        schema_name = row[0] if isinstance(row, (tuple, list)) else row["table_schema"]
        table_name = row[1] if isinstance(row, (tuple, list)) else row["table_name"]
        full_name = f"{schema_name}.{table_name}"
        if schemas and schema_name not in schemas:
            continue
        if tables and full_name not in tables:
            continue
        schemas_seen.add(schema_name)
        tables_list.append({"schema": schema_name, "table": table_name, "full_name": full_name})

    columns_list: list[dict] = []
    for t in tables_list:
        try:
            cols = execute_readonly(
                conn,
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
                (t["schema"], t["table"]),
            )
        except Exception:
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
