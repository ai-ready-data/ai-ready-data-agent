"""Assess pipeline: discover → run → report → [save] → output. Optional compare and interactive."""

from pathlib import Path

from agent.config import Config
from agent.discovery import discover
from agent.run import run_tests
from agent.report import build_report, report_to_markdown
from agent import storage
from agent.audit import AuditSink


def run_assess(config: Config) -> dict:
    """Run full pipeline. Returns report dict; caller handles output and save."""
    if not config.connection:
        raise ValueError("connection required for assess")

    audit = AuditSink(config.db_path, config.audit)

    inv = discover(
        config.connection,
        schemas=config.schemas or None,
        tables=config.tables or None,
    )

    if config.interactive and config.audit:
        audit.log_conversation("Discovery complete. Proceeding to run tests.", phase="post_discover")

    results = run_tests(
        config.connection,
        inv,
        suite_name=config.suite,
        dry_run=config.dry_run,
        audit=audit if config.audit else None,
    )

    if config.dry_run:
        return {"dry_run": True, "preview": results.get("preview", []), "test_count": results.get("test_count", 0)}

    report = build_report(
        results,
        inventory=inv,
        connection_fingerprint=_fingerprint(config.connection),
    )

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
            previous = storage.list_assessments(conn, connection_filter=_fingerprint(config.connection), limit=2)
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
