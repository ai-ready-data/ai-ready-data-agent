"""Assess pipeline: discover → run → report → [save] → output. Optional compare and interactive."""

from pathlib import Path

from agent.config import Config
from agent.discovery import discover
from agent.run import run_tests
from agent.report import build_report, build_estate_report, report_to_markdown
from agent import storage
from agent.audit import AuditSink


def run_assess(config: Config) -> dict:
    """Run full pipeline. Returns report dict; caller handles output and save."""
    connections = config.get_connections()
    if not connections:
        raise ValueError("connection(s) required for assess (use -c, --connections-file, or AIRD_CONNECTION_STRING)")

    if len(connections) == 1:
        return _run_assess_single(config, connections[0])
    return _run_assess_estate(config, connections)


def _run_assess_single(config: Config, connection: str) -> dict:
    """Single-connection assess: discover → run → report → [save] → return."""
    audit = AuditSink(config.db_path, config.audit)

    inv = discover(
        connection,
        schemas=config.schemas or None,
        tables=config.tables or None,
    )

    if config.interactive and config.audit:
        audit.log_conversation("Discovery complete. Proceeding to run tests.", phase="post_discover")

    results = run_tests(
        connection,
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
        connection_fingerprint=_fingerprint(connection),
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
            previous = storage.list_assessments(conn, connection_filter=_fingerprint(connection), limit=2)
            ids = [a["id"] for a in previous if a["id"] != report.get("assessment_id")]
            if ids:
                report["_diff_previous_id"] = ids[0]
        finally:
            conn.close()

    return report


def _run_assess_estate(config: Config, connections: list[str]) -> dict:
    """Estate assess: for each connection discover → run, then build estate report and save."""
    platforms: list[dict] = []
    dry_run_previews: list[dict] = []
    for connection in connections:
        fp = _fingerprint(connection)
        try:
            inv = discover(
                connection,
                schemas=config.schemas or None,
                tables=config.tables or None,
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
