"""Assess pipeline: discover → run → report → [save] → output. Optional compare and interactive."""

from pathlib import Path
from typing import Optional

from agent.config import Config
from agent.discovery import discover
from agent.platform.registry import get_default_suite
from agent.questions_loader import get_suite_questions
from agent.run import run_tests
from agent.report import build_report, build_estate_report, report_to_markdown
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
    targets = config.get_targets()
    if not targets:
        raise ValueError("connection(s) required for assess (use -c, --connections-file, or AIRD_CONNECTION_STRING)")

    context = _load_context(config.context_path)
    thresholds = load_thresholds(config.thresholds_path)

    if len(targets) == 1:
        return _run_assess_single(config, targets[0], context=context, thresholds=thresholds)
    return _run_assess_estate(config, targets, context=context, thresholds=thresholds)


def _run_assess_single(
    config: Config,
    target: dict,
    *,
    context: Optional[dict] = None,
    thresholds: Optional[dict] = None,
) -> dict:
    """Single-target assess: discover → run → report → [save] → return."""
    connection = target["connection"]
    # Scope: per-target > context file > global config
    schemas = target.get("schemas") or (context or {}).get("schemas") or config.schemas or None
    tables = target.get("tables") or (context or {}).get("tables") or config.tables or None
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

    report = build_report(
        results,
        inventory=inv,
        connection_fingerprint=_fingerprint(connection),
        question_results=question_results,
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


def _run_assess_estate(
    config: Config,
    targets: list[dict],
    *,
    context: Optional[dict] = None,
    thresholds: Optional[dict] = None,
) -> dict:
    """Estate assess: for each target discover → run, then build estate report and save."""
    platforms: list[dict] = []
    dry_run_previews: list[dict] = []
    for target in targets:
        connection = target["connection"]
        fp = _fingerprint(connection)
        schemas = target.get("schemas") or (context or {}).get("schemas") or config.schemas or None
        tables = target.get("tables") or (context or {}).get("tables") or config.tables or None
        try:
            inv = discover(
                connection,
                schemas=schemas,
                tables=tables,
            )
        except Exception as e:
            platforms.append({
                "connection_fingerprint": fp,
                "summary": {},
                "results": [],
                "inventory": None,
                "error": str(e),
            })
            continue
        try:
            results = run_tests(
                connection,
                inv,
                suite_name=config.suite,
                dry_run=config.dry_run,
                audit=None,  # estate: no per-connection audit for now
                thresholds=thresholds,
            )
        except Exception as e:
            platforms.append({
                "connection_fingerprint": fp,
                "summary": {},
                "results": [],
                "inventory": inv,
                "error": str(e),
            })
            continue
        if config.dry_run:
            dry_run_previews.append({
                "connection_fingerprint": fp,
                "test_count": results.get("test_count", 0),
                "preview": results.get("preview", []),
            })
            continue
        report = build_report(results, inventory=inv, connection_fingerprint=fp)
        platforms.append({
            "connection_fingerprint": fp,
            "summary": report["summary"],
            "results": report["results"],
            "inventory": inv,
        })
    if config.dry_run:
        total = sum(p["test_count"] for p in dry_run_previews)
        return {"dry_run": True, "preview": dry_run_previews, "test_count": total}
    estate_report = build_estate_report(platforms)
    if context:
        estate_report["user_context"] = context
    if not config.no_save:
        conn = storage.get_connection(config.db_path)
        try:
            aid = storage.save_report(conn, estate_report)
            estate_report["assessment_id"] = aid
        finally:
            conn.close()
    if config.compare and not config.no_save and estate_report.get("assessment_id"):
        conn = storage.get_connection(config.db_path)
        try:
            previous = storage.list_assessments(conn, connection_filter=None, limit=2)
            ids = [a["id"] for a in previous if a["id"] != estate_report.get("assessment_id")]
            if ids:
                estate_report["_diff_previous_id"] = ids[0]
        finally:
            conn.close()
    return estate_report


def _fingerprint(connection: str) -> str:
    """Redacted connection for storage (no credentials)."""
    if "://" not in connection:
        return connection[:50]
    scheme = connection.split("://", 1)[0]
    rest = connection.split("://", 1)[1]
    if "@" in rest:
        rest = "***@" + rest.split("@", 1)[1]
    return f"{scheme}://{rest}"[:80]
