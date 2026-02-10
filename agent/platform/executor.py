"""Read-only query execution. Validates SQL before execution; only SELECT, DESCRIBE, SHOW, EXPLAIN, WITH allowed."""

import re
from typing import Any, List, Optional, Tuple

from agent.exceptions import AssessmentRuntimeError

_ALLOWED_PREFIXES = re.compile(
    r"^\s*(SELECT|DESCRIBE|SHOW|EXPLAIN|WITH)\s+",
    re.IGNORECASE | re.DOTALL,
)


def validate_readonly(sql: str) -> None:
    """Raise AssessmentRuntimeError if sql is not read-only (SELECT/DESCRIBE/SHOW/EXPLAIN/WITH)."""
    if not _ALLOWED_PREFIXES.match(sql.strip()):
        raise AssessmentRuntimeError(
            "Only read-only statements are allowed: SELECT, DESCRIBE, SHOW, EXPLAIN, WITH"
        )


def execute_readonly(connection: Any, sql: str, params: Optional[Tuple] = None) -> List[tuple]:
    """Execute sql against connection after validation. Returns list of rows (tuples)."""
    validate_readonly(sql)
    if params is not None:
        cur = connection.execute(sql, params)
    else:
        cur = connection.execute(sql)
    return cur.fetchall() if hasattr(cur, "fetchall") else list(cur)
