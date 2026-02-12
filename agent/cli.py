"""CLI entry point: subcommands, arg parse, config resolve, dispatch. Machine output to stdout only."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from agent.config import Config
from agent.constants import OutputFormat
from agent.exceptions import UsageError, AssessmentRuntimeError
from agent import storage
from agent.discovery import discover
from agent.run import run_tests
from agent.report import build_report, report_to_markdown, load_report_from_storage
from agent.pipeline import run_assess
from agent.audit import AuditSink
from agent.platform.registry import get_suite
from agent.platform import get_platform
from agent.manifest_loader import load_manifest

logger = logging.getLogger("aird")


def _default_manifest_path() -> Path:
    """Default connections manifest (YAML)."""
    return Path.home() / ".aird" / "connections.yaml"


def _resolve_connection(args: argparse.Namespace, cfg: Config):
    """Resolve single connection from -c arg, env, or default manifest (first entry)."""
    conn_arg = getattr(args, "connection", None)
    if conn_arg:
        if conn_arg.lower().strip().startswith("env:"):
            var_name = conn_arg[4:].strip()
            return os.environ.get(var_name, "").strip() or None
        return conn_arg
    if cfg.connection:
        return cfg.connection
    # Fall back to first entry in default manifest
    manifest_path = _default_manifest_path()
    if manifest_path.exists():
        # Fallback: silently skip manifest if it cannot be loaded (soft default)
        try:
            targets = load_manifest(manifest_path)
            if targets:
                return targets[0].get("connection")
        except Exception as e:
            logger.debug("Failed to load manifest: %s", e)
    return None


def _config_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Config:
    cfg = Config.from_env()
    connection_arg = getattr(args, "connection", None) or cfg.connection
    if getattr(args, "command", None) == "assess" and not connection_arg:
        connection_arg = _resolve_connection(args, cfg)
    cfg = cfg.with_args(
        connection=connection_arg or cfg.connection,
        schemas=getattr(args, "schema", None) or cfg.schemas,
        tables=getattr(args, "tables", None) or cfg.tables,
        context_path=Path(args.context) if getattr(args, "context", None) else cfg.context_path,
        suite=getattr(args, "suite", None) or cfg.suite,
        thresholds_path=Path(args.thresholds) if getattr(args, "thresholds", None) else cfg.thresholds_path,
        output=getattr(args, "output", None) or cfg.output,
        no_save=getattr(args, "no_save", None) or cfg.no_save,
        compare=getattr(args, "compare", None) or cfg.compare,
        dry_run=getattr(args, "dry_run", None) or cfg.dry_run,
        interactive=getattr(args, "interactive", None) or cfg.interactive,
        audit=getattr(args, "audit", None) or cfg.audit,
        survey=getattr(args, "survey", None) or cfg.survey,
        survey_answers_path=Path(args.survey_answers) if getattr(args, "survey_answers", None) else cfg.survey_answers_path,
        target_workload=getattr(args, "workload", None) or cfg.target_workload,
        db_path=Path(args.db_path) if getattr(args, "db_path", None) else cfg.db_path,
        log_level=getattr(args, "log_level", None) or cfg.log_level,
        inventory_path=getattr(args, "inventory", None),
        results_path=getattr(args, "results", None),
        report_path=getattr(args, "report", None),
        report_id=getattr(args, "id", None),
        history_connection_filter=getattr(args, "connection_filter", None),
        history_limit=getattr(args, "limit", None) or cfg.history_limit,
        diff_left=getattr(args, "left", None) or (args.left_id if hasattr(args, "left_id") else None),
        diff_right=getattr(args, "right", None) or (args.right_id if hasattr(args, "right_id") else None),
    )
    return cfg


def _read_stdin() -> str:
    return sys.stdin.read()


def _write_stdout(data: str) -> None:
    sys.stdout.write(data)
    if not data.endswith("\n"):
        sys.stdout.write("\n")


def _write_output(data: dict, output_format: str, markdown_fn=None, json_indent=None) -> None:
    """Route *data* to the correct output sink based on *output_format*.

    Handles four cases:
    - ``stdout`` / ``json``: JSON dump to stdout
    - ``markdown``: call *markdown_fn* (falls back to JSON when *markdown_fn* is None)
    - ``json:<path>``: write pretty-printed JSON to the given file path
    - anything else: falls back to markdown rendering (or JSON if no renderer)

    *json_indent* controls indentation for JSON written to stdout (default ``None``
    for compact output).  File output always uses ``indent=2``.
    """
    if output_format == OutputFormat.STDOUT or output_format == OutputFormat.JSON:
        _write_stdout(json.dumps(data, indent=json_indent))
    elif OutputFormat.is_json_path(output_format):
        path = OutputFormat.parse_json_path(output_format)
        Path(path).write_text(json.dumps(data, indent=2))
    elif markdown_fn is not None:
        _write_stdout(markdown_fn(data))
    else:
        # Fallback: JSON dump when no markdown renderer is provided
        _write_stdout(json.dumps(data, indent=json_indent))



def _format_dry_run_preview(report: dict) -> str:
    """Format dry-run preview as a human-readable table."""
    connection = report.get("connection", "unknown")
    preview = report.get("preview", [])
    test_count = report.get("test_count", 0)

    lines: list[str] = []
    lines.append(f"Dry-run preview for: {connection}")
    lines.append("=" * max(40, len(lines[0])))
    lines.append("")

    # Group by factor
    factor_data: dict[str, dict[str, set]] = {}
    for t in preview:
        factor = t.get("factor") or "unknown"
        req = t.get("requirement") or "unknown"
        if factor not in factor_data:
            factor_data[factor] = {"requirements": set(), "count": 0}
        factor_data[factor]["requirements"].add(req)
        factor_data[factor]["count"] = factor_data[factor].get("count", 0) + 1

    # Compute column widths
    factor_col = max(len("Factor"), max((len(f) for f in factor_data), default=6))
    tests_col = max(len("Tests"), len(str(test_count)))

    header = f"{'Factor':<{factor_col}}  {'Tests':>{tests_col}}   Requirement Keys"
    sep = f"{'─' * factor_col}  {'─' * tests_col}   {'─' * 16}"
    lines.append(header)
    lines.append(sep)

    for factor in sorted(factor_data):
        info = factor_data[factor]
        count = info["count"]
        reqs = ", ".join(sorted(info["requirements"]))
        lines.append(f"{factor:<{factor_col}}  {count:>{tests_col}}   {reqs}")

    lines.append(sep)
    lines.append(f"{'Total':<{factor_col}}  {test_count:>{tests_col}}")
    lines.append("")

    # Sample tests (up to 5)
    if preview:
        lines.append("Sample tests:")
        for t in preview[:5]:
            tid = t.get("id", "?")
            factor = t.get("factor", "?")
            req = t.get("requirement", "?")
            target = t.get("target_type", "?")
            lines.append(f"  • {tid} ({factor}/{req}) — {target}")
        if len(preview) > 5:
            lines.append(f"  ... and {len(preview) - 5} more")
        lines.append("")

    lines.append("No queries will be executed. Run without --dry-run to assess.")
    return "\n".join(lines)


def cmd_assess(cfg: Config) -> None:
    report = run_assess(cfg)
    if report.get("dry_run"):
        out = cfg.output
        if out == OutputFormat.STDOUT or OutputFormat.is_json_path(out):
            _write_stdout(json.dumps(report))
        else:
            _write_stdout(_format_dry_run_preview(report))
        return
    _write_output(report, cfg.output, markdown_fn=report_to_markdown)
    if report.get("_diff_previous_id"):
        _write_stdout(f"\n(Diff vs previous: {report['_diff_previous_id']})")


def cmd_discover(cfg: Config) -> None:
    if not cfg.connection:
        raise UsageError("--connection or AIRD_CONNECTION_STRING required")
    inv = discover(cfg.connection, schemas=cfg.schemas or None, tables=cfg.tables or None)
    out = cfg.output
    if out == OutputFormat.STDOUT or not out or out == "-":
        _write_stdout(json.dumps(inv, indent=2))
    elif OutputFormat.is_json_path(out):
        path = OutputFormat.parse_json_path(out)
        Path(path).write_text(json.dumps(inv, indent=2))
    else:
        # Treat any other value (e.g. a bare file path) as a write target
        Path(out).write_text(json.dumps(inv, indent=2))


def cmd_run(cfg: Config) -> None:
    if not cfg.connection:
        raise UsageError("--connection or AIRD_CONNECTION_STRING required")
    inv_raw = _read_stdin() if cfg.inventory_path == "-" else Path(cfg.inventory_path or "").read_text()
    inv = json.loads(inv_raw)
    audit = AuditSink(cfg.db_path, cfg.audit) if cfg.audit else None
    results = run_tests(cfg.connection, inv, suite_name=cfg.suite, dry_run=cfg.dry_run, audit=audit)
    if cfg.results_path and cfg.results_path != "-":
        Path(cfg.results_path).write_text(json.dumps(results, indent=2))
    else:
        _write_stdout(json.dumps(results, indent=2))


def cmd_report(cfg: Config) -> None:
    if cfg.report_id:
        report = load_report_from_storage(cfg.db_path, cfg.report_id)
        if not report:
            raise AssessmentRuntimeError(f"Assessment not found: {cfg.report_id}")
    else:
        if not cfg.results_path:
            raise UsageError("--results or --id required")
        results_raw = _read_stdin() if cfg.results_path == "-" else Path(cfg.results_path).read_text()
        results = json.loads(results_raw)
        report = build_report(results, connection_fingerprint="")
    _write_output(report, cfg.output, markdown_fn=report_to_markdown, json_indent=2)


def cmd_save(cfg: Config) -> None:
    report_raw = _read_stdin() if (cfg.report_path == "-" or not cfg.report_path) else Path(cfg.report_path).read_text()
    report = json.loads(report_raw)
    conn = storage.get_connection(cfg.db_path)
    try:
        aid = storage.save_report(conn, report)
        _write_stdout(aid)
    finally:
        conn.close()


def cmd_history(cfg: Config) -> None:
    conn = storage.get_connection(cfg.db_path)
    try:
        items = storage.list_assessments(
            conn,
            connection_filter=cfg.history_connection_filter,
            limit=cfg.history_limit,
        )
    finally:
        conn.close()
    for a in items:
        s = a.get("summary", {})
        _write_stdout(f"{a['id']}\t{a['created_at']}\tL1:{s.get('l1_pct', 0)}%\tL2:{s.get('l2_pct', 0)}%\tL3:{s.get('l3_pct', 0)}%\t{a.get('connection_fingerprint', '')}")


def cmd_diff(cfg: Config) -> None:
    conn = storage.get_connection(cfg.db_path)
    try:
        left = storage.get_report(conn, cfg.diff_left) if cfg.diff_left and len(cfg.diff_left) == 36 else None
        if not left and cfg.diff_left:
            left = json.loads(Path(cfg.diff_left).read_text())
        right = storage.get_report(conn, cfg.diff_right) if cfg.diff_right and len(cfg.diff_right) == 36 else None
        if not right and cfg.diff_right:
            right = json.loads(Path(cfg.diff_right).read_text())
    finally:
        conn.close()
    if not left or not right:
        raise UsageError("diff requires two assessment ids or --left/--right paths")
    l_s = left.get("summary", {})
    r_s = right.get("summary", {})
    _write_stdout(f"Left:  L1={l_s.get('l1_pct')}% L2={l_s.get('l2_pct')}% L3={l_s.get('l3_pct')}%")
    _write_stdout(f"Right: L1={r_s.get('l1_pct')}% L2={r_s.get('l2_pct')}% L3={r_s.get('l3_pct')}%")


def cmd_suites(_cfg: Config) -> None:
    import agent.platform.duckdb_adapter  # noqa: F401
    from agent.platform.registry import get_all_suites, get_suite_names
    from agent.suites.loader import get_suite_extends
    all_suites = get_all_suites()
    suite_extends = get_suite_extends()
    for name in get_suite_names():
        tests = all_suites[name]
        count_str = f"{len(tests)} tests"
        if name in suite_extends:
            parents = ", ".join(suite_extends[name])
            _write_stdout(f"{name}\t{count_str}  (extends: {parents})")
        else:
            _write_stdout(f"{name}\t{count_str}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="aird", description="AI-Ready Data assessment CLI")
    parser.add_argument("--log-level", default=None, help="Log level")
    parser.add_argument("--db-path", default=None, help="SQLite DB path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # assess
    p_assess = subparsers.add_parser("assess", help="Full pipeline: discover → run → report → save")
    p_assess.add_argument("-c", "--connection", default=None, dest="connection")
    p_assess.add_argument("-s", "--schema", action="append", default=[], dest="schema")
    p_assess.add_argument("-t", "--tables", action="append", default=[], dest="tables")
    p_assess.add_argument("--suite", default="auto")
    p_assess.add_argument("-o", "--output", default="markdown")
    p_assess.add_argument("--thresholds", default=None)
    p_assess.add_argument("--context", default=None)
    p_assess.add_argument("--workload", default=None, choices=["analytics", "rag", "training"],
                          help="Target workload level: analytics (L1), rag (L2), training (L3)")
    p_assess.add_argument("--no-save", action="store_true")
    p_assess.add_argument("--compare", action="store_true")
    p_assess.add_argument("--dry-run", action="store_true")
    p_assess.add_argument("-i", "--interactive", action="store_true")
    p_assess.add_argument("--audit", action="store_true")
    p_assess.add_argument("--survey", action="store_true", help="Run question-based survey and include in report")
    p_assess.add_argument("--survey-answers", default=None, help="Path to YAML of pre-filled answers (for non-interactive demo)")

    # discover
    p_disc = subparsers.add_parser("discover", help="Connect and output inventory")
    p_disc.add_argument("-c", "--connection", default=None)
    p_disc.add_argument("-s", "--schema", action="append", default=[], dest="schema")
    p_disc.add_argument("-t", "--tables", action="append", default=[], dest="tables")
    p_disc.add_argument("--context", default=None)
    p_disc.add_argument("-o", "--output", default="stdout")
    p_disc.add_argument("--inventory", default=None, help="Write inventory to file (default stdout)")

    # run
    p_run = subparsers.add_parser("run", help="Run tests from inventory")
    p_run.add_argument("-c", "--connection", default=None)
    p_run.add_argument("--inventory", default="-")
    p_run.add_argument("--suite", default="auto")
    p_run.add_argument("--thresholds", default=None)
    p_run.add_argument("--context", default=None)
    p_run.add_argument("-o", "--output", default="stdout")
    p_run.add_argument("--results", default=None)
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--audit", action="store_true")

    # report
    p_rep = subparsers.add_parser("report", help="Build report from results or load by id")
    p_rep.add_argument("--results", default=None)
    p_rep.add_argument("--inventory", default=None)
    p_rep.add_argument("--thresholds", default=None)
    p_rep.add_argument("--context", default=None)
    p_rep.add_argument("--id", default=None, dest="id")
    p_rep.add_argument("-o", "--output", default="markdown")

    # save
    p_save = subparsers.add_parser("save", help="Persist report to history")
    p_save.add_argument("--report", default="-")

    # history
    p_hist = subparsers.add_parser("history", help="List saved assessments")
    p_hist.add_argument("--connection", default=None, dest="connection_filter")
    p_hist.add_argument("-n", "--limit", type=int, default=20)

    # diff
    p_diff = subparsers.add_parser("diff", help="Compare two reports")
    p_diff.add_argument("left_id", nargs="?", default=None)
    p_diff.add_argument("right_id", nargs="?", default=None)
    p_diff.add_argument("--left", default=None)
    p_diff.add_argument("--right", default=None)

    # suites
    subparsers.add_parser("suites", help="List test suites")

    # init
    subparsers.add_parser("init", help="Interactive setup wizard for first-time users")

    args = parser.parse_args()

    # Configure logging before anything else
    log_level_str = (getattr(args, "log_level", None) or "warning").upper()
    logging.basicConfig(level=getattr(logging, log_level_str, logging.WARNING),
                        format="%(levelname)s: %(message)s")

    # init is handled before config resolution (it collects config interactively)
    if args.command == "init":
        from agent.commands.init import run_init
        run_init()
        return

    cfg = _config_from_args(parser, args)

    try:
        if args.command == "assess":
            cmd_assess(cfg)
        elif args.command == "discover":
            cmd_discover(cfg)
        elif args.command == "run":
            cmd_run(cfg)
        elif args.command == "report":
            cmd_report(cfg)
        elif args.command == "save":
            cmd_save(cfg)
        elif args.command == "history":
            cmd_history(cfg)
        elif args.command == "diff":
            if getattr(args, "left_id", None):
                cfg = cfg.with_args(diff_left=args.left_id, diff_right=args.right_id)
            elif getattr(args, "left", None):
                cfg = cfg.with_args(diff_left=args.left, diff_right=args.right)
            cmd_diff(cfg)
        elif args.command == "suites":
            cmd_suites(cfg)
    except UsageError as e:
        logger.error(str(e))
        sys.exit(2)
    except (AssessmentRuntimeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
