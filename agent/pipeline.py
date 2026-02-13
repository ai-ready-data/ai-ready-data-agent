"""Assess pipeline: discover → run → report → [save] → output. Optional compare and interactive."""

import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

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
    # Fallback: return None if context file is malformed or unreadable
    try:
        import yaml
        raw = yaml.safe_load(path.read_text())
        return raw if isinstance(raw, dict) else None
    except Exception as e:
        logger.warning("Failed to load context from %s: %s", path, e)
        return None


def _load_survey_answers(path: Optional[Path]) -> dict:
    """Load optional survey answers YAML. Returns dict mapping requirement or 'factor.requirement' to answer string."""
    if not path or not path.exists():
        return {}
    # Fallback: return empty dict if survey answers file is malformed or unreadable
    try:
        import yaml
        raw = yaml.safe_load(path.read_text())
        if not isinstance(raw, dict):
            return {}
        return {str(k): str(v) for k, v in raw.items()}
    except Exception as e:
        logger.warning("Failed to load survey answers from %s: %s", path, e)
        return {}


def run_assess(config: Config, *, progress_callback: Optional[Callable[[int, int, dict], None]] = None) -> dict:
    """Run full pipeline. Returns report dict; caller handles output and save.
    progress_callback: optional callable(current_index, total, test_result) forwarded to run_tests()."""
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

    if config.interactive:
        from agent.ui.console import is_interactive
        if is_interactive():
            from agent.ui.discovery import show_discovery_tree, select_tables, filter_inventory
            show_discovery_tree(inv)
            selected = select_tables(inv)
            if selected:
                inv = filter_inventory(inv, selected)

    if config.interactive and config.audit:
        audit.log_conversation("Discovery complete. Proceeding to run tests.", phase="post_discover")

    results = run_tests(
        connection,
        inv,
        suite_name=config.suite,
        dry_run=config.dry_run,
        audit=audit if config.audit else None,
        thresholds=thresholds,
        progress_callback=progress_callback,
        factor_filter=config.factor_filter,
    )

    if config.dry_run:
        return {
            "dry_run": True,
            "preview": results.get("preview", []),
            "test_count": results.get("test_count", 0),
            "connection": connection,
        }

    question_results = None
    if config.survey:
        default_suite = get_default_suite(connection)
        resolved_suite = config.suite if config.suite != "auto" else default_suite
        questions = get_suite_questions(resolved_suite)
        answers = _load_survey_answers(config.survey_answers_path)
        question_results = run_survey(questions=questions, answers=answers, interactive=config.interactive)

    target_workload = config.target_workload or (context or {}).get("target_level") or None

    # Resolve data products from context
    data_products = None
    product_name = None
    if context and context.get("data_products"):
        all_products = context["data_products"]
        if config.product:
            # Filter to a single product
            matched = [p for p in all_products if p.get("name") == config.product]
            if not matched:
                available = [p.get("name", "?") for p in all_products]
                raise ValueError(
                    f"Data product {config.product!r} not found in context. "
                    f"Available: {', '.join(available)}"
                )
            data_products = matched
            product_name = config.product
        else:
            data_products = all_products

    report = build_report(
        results,
        inventory=inv,
        connection_fingerprint=_fingerprint(connection),
        question_results=question_results,
        target_workload=target_workload,
        data_products=data_products,
    )
    if context:
        report["user_context"] = context

    if not config.no_save:
        conn = storage.get_connection(config.db_path)
        try:
            aid = storage.save_report(conn, report, data_product=product_name)
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
