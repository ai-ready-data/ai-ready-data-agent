"""Assess pipeline: discover → run → report → [save] → output. Optional compare and interactive."""

from pathlib import Path
from typing import Optional

from agent.config import Config
from agent.discovery import discover
from agent.platform.registry import get_default_suite
from agent.questions_loader import get_suite_questions
from agent.run import run_tests
from agent.report import build_report, report_to_markdown
from agent.survey import run_survey
from agent import storage
from agent.audit import AuditSink
from agent.thresholds import load_thresholds


def _load_context(path: Optional[Path]) -> Optional[dict]:
    """Load optional context YAML. Returns dict with keys e.g. schemas, tables, target_level; or None."""
    if not path or not path.exists():
        return None
    try:
        import yaml
        raw = yaml.safe_load(path.read_text())
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def _load_survey_answers(path: Optional[Path]) -> dict:
    """Load optional survey answers YAML. Returns dict mapping requirement or 'factor.requirement' to answer string."""
    if not path or not path.exists():
        return {}
    try:
        import yaml
        raw = yaml.safe_load(path.read_text())
        if not isinstance(raw, dict):
            return {}
        return {str(k): str(v) for k, v in raw.items()}
    except Exception:
        return {}


def run_assess(config: Config) -> dict:
    """Run full pipeline. Returns report dict; caller handles output and save."""
    if not config.connection:
        raise ValueError("connection required for assess (use -c or AIRD_CONNECTION_STRING)")

    connection = config.connection
    context = _load_context(config.context_path)
    thresholds = load_thresholds(config.thresholds_path)
    schemas = (context or {}).get("schemas") or config.schemas or None
    tables = (context or {}).get("tables") or config.tables or None
    audit = AuditSink(config.db_path, config.audit)

    inv = discover(
        connection,
        schemas=schemas,
        tables=tables,
    )

    if config.interactive and config.audit:
        audit.log_conversation("Discovery complete. Proceeding to run tests.", phase="post_discover")

    results = run_tests(
        connection,
        inv,
        suite_name=config.suite,
        dry_run=config.dry_run,
        audit=audit if config.audit else None,
        thresholds=thresholds,
    )

    if config.dry_run:
        return {"dry_run": True, "preview": results.get("preview", []), "test_count": results.get("test_count", 0)}

    question_results = None
    if config.survey:
        default_suite = get_default_suite(connection)
        resolved_suite = config.suite if config.suite != "auto" else default_suite
        questions = get_suite_questions(resolved_suite)
        answers = _load_survey_answers(config.survey_answers_path)
        question_results = run_survey(questions=questions, answers=answers)

    target_workload = config.target_workload or (context or {}).get("target_level") or None
    report = build_report(
        results,
        inventory=inv,
        connection_fingerprint=_fingerprint(connection),
        question_results=question_results,
        target_workload=target_workload,
    )
    if context:
        report["user_context"] = context

    if not config.no_save:
        conn = storage.get_connection(config.db_path)
        try:
            aid = storage.save_report(conn, report)
            report["assessment_id"] = aid
            if config.audit:
                audit.assessment_id = aid
        finally:
            conn.close()

    if config.compare and not config.no_save and report.get("assessment_id"):
        conn = storage.get_connection(config.db_path)
        try:
            previous = storage.list_assessments(conn, connection_filter=_fingerprint(connection), limit=2)
            ids = [a["id"] for a in previous if a["id"] != report.get("assessment_id")]
            if ids:
                report["_diff_previous_id"] = ids[0]
        finally:
            conn.close()

    return report


def _fingerprint(connection: str) -> str:
    """Redacted connection for storage (no credentials)."""
    if "://" not in connection:
        return connection[:50]
    scheme = connection.split("://", 1)[0]
    rest = connection.split("://", 1)[1]
    if "@" in rest:
        rest = "***@" + rest.split("@", 1)[1]
    return f"{scheme}://{rest}"[:80]
