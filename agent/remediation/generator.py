"""Generate remediation suggestions from failed assessment results."""

from typing import Any, Dict, List, Optional, Tuple

from agent.remediation.templates import REMEDIATION_TEMPLATES


def _parse_test_id(test_id: str) -> Tuple[str, str, Optional[str]]:
    """Parse test_id into (schema, table, column). Column is None for table/platform tests."""
    parts = test_id.split("|")
    if len(parts) >= 4:
        return parts[1], parts[2], parts[3]
    if len(parts) >= 3:
        return parts[1], parts[2], None
    return "", "", None


def _get_template(requirement: str) -> Optional[Tuple[str, str]]:
    """Return (description, sql_template) for requirement, or None if not found."""
    return REMEDIATION_TEMPLATES.get(requirement)


def _substitute(template: str, schema: str, table: str, column: Optional[str]) -> str:
    """Substitute placeholders. Use empty string for missing column."""
    return template.format(
        schema=schema or "schema",
        table=table or "table",
        column=column or "column",
    )


def _is_failed(result: dict) -> bool:
    """True if the test failed at any workload level."""
    return (
        not result.get("l1_pass", True)
        or not result.get("l2_pass", True)
        or not result.get("l3_pass", True)
    )


def generate_fix_suggestions(report: dict) -> List[Dict[str, Any]]:
    """Generate remediation suggestions for all failed results in a report.

    Returns a list of dicts: {test_id, factor, requirement, schema, table, column,
    description, sql, measured_value, threshold}.
    """
    suggestions = []
    results = report.get("results", [])

    for r in results:
        if not _is_failed(r):
            continue

        requirement = r.get("requirement", "")
        template = _get_template(requirement)
        schema, table, column = _parse_test_id(r.get("test_id", ""))

        if not template:
            # No template: generic suggestion
            desc = f"Requirement '{requirement}' failed. See factor docs for guidance."
            sql = "-- No template available. Check factor documentation."
        else:
            desc, sql_tmpl = template
            sql = _substitute(sql_tmpl, schema, table, column)

        suggestions.append({
            "test_id": r.get("test_id", ""),
            "factor": r.get("factor", ""),
            "requirement": requirement,
            "schema": schema,
            "table": table,
            "column": column,
            "description": desc,
            "sql": sql,
            "measured_value": r.get("measured_value"),
            "threshold": r.get("threshold"),
        })

    return suggestions
