"""Reporter: build report from results (and inventory), or load saved report by id and re-output.

Report shape conforms to docs/specs/report-spec.md.
"""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent import storage
from agent.constants import WorkloadLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_factor_summary(results_list: list[dict]) -> list[dict]:
    """Build per-factor roll-up from a flat results list.

    Returns a list of dicts sorted by factor name, each with:
      factor, total_tests, l1_pass, l2_pass, l3_pass, l1_pct, l2_pct, l3_pct
    """
    by_factor: dict[str, list[dict]] = defaultdict(list)
    for r in results_list:
        by_factor[r.get("factor", "unknown")].append(r)

    out: list[dict] = []
    for factor in sorted(by_factor):
        tests = by_factor[factor]
        total = len(tests) or 1
        l1 = sum(1 for r in tests if r.get("l1_pass"))
        l2 = sum(1 for r in tests if r.get("l2_pass"))
        l3 = sum(1 for r in tests if r.get("l3_pass"))
        out.append({
            "factor": factor,
            "total_tests": len(tests),
            "l1_pass": l1,
            "l2_pass": l2,
            "l3_pass": l3,
            "l1_pct": round(100 * l1 / total, 1),
            "l2_pct": round(100 * l2 / total, 1),
            "l3_pct": round(100 * l3 / total, 1),
        })
    return out


def _build_summary(results_list: list[dict]) -> dict:
    """Build aggregate summary from a flat results list."""
    l1_pass = sum(1 for r in results_list if r.get("l1_pass"))
    l2_pass = sum(1 for r in results_list if r.get("l2_pass"))
    l3_pass = sum(1 for r in results_list if r.get("l3_pass"))
    total = len(results_list) or 1
    return {
        "total_tests": len(results_list),
        "l1_pass": l1_pass,
        "l2_pass": l2_pass,
        "l3_pass": l3_pass,
        "l1_pct": round(100 * l1_pass / total, 1),
        "l2_pct": round(100 * l2_pass / total, 1),
        "l3_pct": round(100 * l3_pass / total, 1),
    }


def _result_belongs_to_product(result: dict, product: dict) -> bool:
    """Check if a test result belongs to a data product based on its test_id.

    test_id format is e.g. "null_rate|schema|table|column" or "dup_rate|schema|table".
    Product assets are table identifiers like "schema.table" or schema names.
    """
    test_id = result.get("test_id", "")
    parts = test_id.split("|")
    if len(parts) < 3:
        return False
    result_schema = parts[1]
    result_table = parts[2]
    result_fqn = f"{result_schema}.{result_table}"

    # Check against explicit tables
    for table in product.get("tables", []):
        if result_fqn == table or result_table == table:
            return True

    # Check against schemas (all tables in the schema belong to the product)
    for schema in product.get("schemas", []):
        if result_schema == schema:
            return True

    return False


def _build_data_product_reports(results_list: list[dict], data_products: list[dict]) -> list[dict]:
    """Build per-data-product report objects from results and product definitions."""
    product_reports: list[dict] = []
    for product in data_products:
        product_results = [r for r in results_list if _result_belongs_to_product(r, product)]
        product_reports.append({
            "name": product.get("name", ""),
            "owner": product.get("owner"),
            "target_workload": product.get("workload"),
            "assets": product.get("tables", []) + [f"{s}.*" for s in product.get("schemas", [])],
            "summary": _build_summary(product_results),
            "factor_summary": _build_factor_summary(product_results),
        })
    return product_reports


# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------


def build_report(
    results: dict,
    *,
    inventory: Optional[dict] = None,
    connection_fingerprint: str = "",
    question_results: Optional[list] = None,
    target_workload: Optional[str] = None,
    data_products: Optional[List[dict]] = None,
) -> dict:
    """Build full report dict from results. Conforms to report-spec.md.

    When data_products is provided (list of product definitions from context YAML),
    the report includes per-product summaries and factor breakdowns. The top-level
    summary and factor_summary are the aggregate across all products.
    """
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    results_list = results.get("results", [])
    summary = _build_summary(results_list)
    out: dict[str, Any] = {
        "created_at": created,
        "connection_fingerprint": connection_fingerprint,
        "target_workload": target_workload,
        "summary": summary,
        "factor_summary": _build_factor_summary(results_list),
        "results": results_list,
        "not_assessed": [],
        "inventory": inventory,
        "environment": {},
        "user_context": {},
    }
    if question_results is not None:
        out["question_results"] = question_results
    if data_products:
        out["data_products"] = _build_data_product_reports(results_list, data_products)
    return out



# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

# Build label lookups from WorkloadLevel enum.  The dict keeps the same
# shape/values as before so existing callers are unaffected.
# Short keys ("l1") use the canonical label; descriptive keys ("analytics")
# use the enum member name for the human-readable part.
_WORKLOAD_LABELS = {
    wl.short: wl.label for wl in WorkloadLevel
}
_WORKLOAD_LABELS.update({
    wl.value: f"{wl.name.capitalize() if len(wl.name) > 3 else wl.name} ({wl.short.upper()})"
    for wl in WorkloadLevel
})

# Map descriptive workload names to level keys (e.g. "rag" -> "l2")
_WORKLOAD_TO_LEVEL = {
    wl.value: wl.short for wl in WorkloadLevel
}


def _fmt_measured(value: Any) -> str:
    """Format a measured value for display."""
    if value is None:
        return "—"
    try:
        v = float(value)
        # Show as percentage if 0-1, else as number
        if 0 <= v <= 1:
            return f"{v:.2%}"
        return f"{v:.4g}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_threshold(thresh: dict) -> str:
    """Format threshold as L1/L2/L3 string."""
    if not thresh:
        return "—"
    return f"{thresh.get('l1', '—')} / {thresh.get('l2', '—')} / {thresh.get('l3', '—')}"


def _pass_icon(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _render_factor_section(factor_name: str, factor_results: List[dict], factor_sum: dict, target_level: Optional[str] = None, heading_level: int = 2) -> List[str]:
    """Render a single factor section with summary line and results table.
    
    If target_level is specified (l1, l2, l3), shows focused single-column output.
    Otherwise shows all three levels. heading_level controls the markdown heading
    depth (2 = ##, 3 = ###) to support nesting under data product sections.
    """
    lines: list[str] = []
    display_name = factor_name.capitalize()
    prefix = "#" * heading_level
    lines.append(f"{prefix} Factor: {display_name}")
    lines.append("")

    t = factor_sum.get("total_tests", 0)
    
    if target_level:
        # Focused output for target workload
        level_pass = factor_sum.get(f"{target_level}_pass", 0)
        level_pct = factor_sum.get(f"{target_level}_pct", 0)
        level_label = {"l1": "Analytics", "l2": "RAG", "l3": "Training"}.get(target_level, target_level.upper())
        verdict = "✓ READY" if level_pass == t else f"✗ {t - level_pass} blocking"
        lines.append(f"**{level_label}:** {level_pass}/{t} ({level_pct}%) — {verdict}")
        lines.append("")
        
        # Simplified table with single Pass column
        lines.append("| Test | Measured | Threshold | Result |")
        lines.append("|------|----------|-----------|--------|")
        for r in factor_results:
            test_id = r.get("test_id", "?")
            if "|" in test_id:
                parts = test_id.split("|")
                test_id = parts[0] if len(parts) <= 1 else f"{parts[0]}|...{parts[-1]}"
            thresh = r.get("threshold", {})
            level_thresh = thresh.get(target_level, "—")
            passed = r.get(f"{target_level}_pass", False)
            lines.append(
                f"| {test_id} "
                f"| {_fmt_measured(r.get('measured_value'))} "
                f"| {level_thresh} "
                f"| {_pass_icon(passed)} |"
            )
            if r.get("error"):
                lines.append(f"| | **Error:** {r['error']} | | |")
    else:
        # Full output with all levels
        lines.append(
            f"L1: {factor_sum.get('l1_pass', 0)}/{t} ({factor_sum.get('l1_pct', 0)}%) "
            f"| L2: {factor_sum.get('l2_pass', 0)}/{t} ({factor_sum.get('l2_pct', 0)}%) "
            f"| L3: {factor_sum.get('l3_pass', 0)}/{t} ({factor_sum.get('l3_pct', 0)}%)"
        )
        lines.append("")

        lines.append("| Test | Requirement | Measured | Threshold (L1/L2/L3) | Dir | L1 | L2 | L3 |")
        lines.append("|------|-------------|----------|----------------------|-----|----|----|-----|")
        for r in factor_results:
            test_id = r.get("test_id", "?")
            if "|" in test_id:
                parts = test_id.split("|")
                test_id = parts[0] if len(parts) <= 1 else f"{parts[0]}|...{parts[-1]}"
            lines.append(
                f"| {test_id} "
                f"| {r.get('requirement', '?')} "
                f"| {_fmt_measured(r.get('measured_value'))} "
                f"| {_fmt_threshold(r.get('threshold', {}))} "
                f"| {r.get('direction', 'lte')} "
                f"| {_pass_icon(r.get('l1_pass', False))} "
                f"| {_pass_icon(r.get('l2_pass', False))} "
                f"| {_pass_icon(r.get('l3_pass', False))} |"
            )
            if r.get("error"):
                lines.append(f"| | | **Error:** {r['error']} | | | | | |")
    lines.append("")
    return lines


def _render_summary_lines(s: dict, target_level: Optional[str] = None) -> List[str]:
    """Render summary lines for aggregate or per-product summary."""
    lines: list[str] = []
    total = s.get('total_tests', 0)
    if target_level:
        level_pass = s.get(f'{target_level}_pass', 0)
        level_pct = s.get(f'{target_level}_pct', 0)
        level_label = {"l1": "Analytics", "l2": "RAG", "l3": "Training"}.get(target_level, target_level.upper())
        verdict = "✓ READY" if level_pass == total else f"✗ {total - level_pass} tests need attention"
        lines.append(f"**{level_label} Readiness:** {level_pass}/{total} ({level_pct}%) — {verdict}")
        lines.append("")
    else:
        lines.extend([
            f"- Total tests: {total}",
            f"- L1 pass: {s.get('l1_pass', 0)}/{total} ({s.get('l1_pct', 0)}%)",
            f"- L2 pass: {s.get('l2_pass', 0)}/{total} ({s.get('l2_pct', 0)}%)",
            f"- L3 pass: {s.get('l3_pass', 0)}/{total} ({s.get('l3_pct', 0)}%)",
            "",
        ])
    return lines


def _render_data_product_section(product: dict, all_results: List[dict], global_target_level: Optional[str] = None) -> List[str]:
    """Render a data product section with its own summary and factor breakdown."""
    lines: list[str] = []
    name = product.get("name", "Unnamed")
    owner = product.get("owner")
    workload = product.get("target_workload")
    assets = product.get("assets", [])

    lines.append(f"## Data Product: {name}")
    lines.append("")

    meta_parts: list[str] = []
    if owner:
        meta_parts.append(f"**Owner:** {owner}")
    if workload:
        wl_label = _WORKLOAD_LABELS.get(workload, workload)
        meta_parts.append(f"**Workload:** {wl_label}")
    if meta_parts:
        lines.append(" | ".join(meta_parts))
    if assets:
        lines.append(f"**Assets:** {', '.join(assets)}")
    lines.append("")

    # Use per-product workload override if set, else fall back to global
    product_target_level = _WORKLOAD_TO_LEVEL.get(workload) if workload else global_target_level

    # Per-product summary
    ps = product.get("summary", {})
    lines.extend(_render_summary_lines(ps, product_target_level))

    # Per-product factor breakdown
    factor_summaries = {fs["factor"]: fs for fs in product.get("factor_summary", [])}

    # Filter all_results to this product's results for rendering
    product_results_by_factor: dict[str, list[dict]] = defaultdict(list)
    for r in all_results:
        if _result_belongs_to_product_report(r, product):
            product_results_by_factor[r.get("factor", "unknown")].append(r)

    for factor in sorted(product_results_by_factor):
        fs = factor_summaries.get(factor, {})
        lines.extend(_render_factor_section(factor, product_results_by_factor[factor], fs, product_target_level, heading_level=3))

    return lines


def _result_belongs_to_product_report(result: dict, product_report: dict) -> bool:
    """Check if a result belongs to a product report object (from the report, not the context).

    Uses the product's assets list which contains entries like "schema.table" or "schema.*".
    """
    test_id = result.get("test_id", "")
    parts = test_id.split("|")
    if len(parts) < 3:
        return False
    result_schema = parts[1]
    result_table = parts[2]
    result_fqn = f"{result_schema}.{result_table}"

    for asset in product_report.get("assets", []):
        if asset.endswith(".*"):
            # Schema wildcard: "events.*" matches all tables in schema "events"
            schema = asset[:-2]
            if result_schema == schema:
                return True
        elif result_fqn == asset or result_table == asset:
            return True
    return False


def report_to_markdown(report: dict) -> str:
    """Render report as markdown.

    Rendering follows the canonical section order defined in report-spec.md.
    When data_products are present, renders per-product sections with an
    aggregate summary. Otherwise renders the flat factor-by-factor view.
    """
    s = report.get("summary", {})
    tw = report.get("target_workload")
    tw_label = _WORKLOAD_LABELS.get(tw, "Not specified") if tw else "Not specified"
    # Convert workload name to level (e.g., "rag" -> "l2")
    target_level = _WORKLOAD_TO_LEVEL.get(tw) if tw else None
    data_products = report.get("data_products")
    has_products = bool(data_products)

    lines = [
        "# AI-Ready Data Assessment Report",
        "",
        f"**Created:** {report.get('created_at', '')}",
        f"**Connection:** {report.get('connection_fingerprint', '')}",
        f"**Target workload:** {tw_label}",
    ]
    if has_products:
        lines.append(f"**Data products:** {len(data_products)}")
    lines.extend(["", f"## Summary{' (Aggregate)' if has_products else ''}", ""])

    lines.extend(_render_summary_lines(s, target_level))

    if has_products:
        # Render per-product sections
        all_results = report.get("results", [])
        for product in data_products:
            lines.extend(_render_data_product_section(product, all_results, target_level))
    else:
        # Flat factor-by-factor breakdown (original behavior)
        factor_summaries = {fs["factor"]: fs for fs in report.get("factor_summary", [])}
        results_by_factor: dict[str, list[dict]] = defaultdict(list)
        for r in report.get("results", []):
            results_by_factor[r.get("factor", "unknown")].append(r)

        for factor in sorted(results_by_factor):
            fs = factor_summaries.get(factor, {})
            lines.extend(_render_factor_section(factor, results_by_factor[factor], fs, target_level))

    # Survey results
    qr = report.get("question_results")
    if qr:
        lines.append("## Survey Results")
        lines.append("")
        for r in qr:
            status = _pass_icon(r.get("l1_pass", False))
            lines.append(f"- **{r.get('factor')} / {r.get('requirement')}**: {status}")
            lines.append(f"  - {r.get('question_text', '')}")
            lines.append(f"  - Answer: {r.get('answer', '—')}")
            lines.append("")

    # Not assessed
    not_assessed = report.get("not_assessed", [])
    if not_assessed:
        lines.append("## Not Assessed")
        lines.append("")
        for na in not_assessed:
            lines.append(f"- **{na.get('factor', '?')} / {na.get('requirement', '?')}**: {na.get('reason', 'Unknown')}")
        lines.append("")

    # Appendix: inventory summary
    inv = report.get("inventory")
    if inv:
        lines.append("## Appendix: Inventory")
        lines.append("")
        lines.append(f"- Schemas: {len(inv.get('schemas', []))}")
        lines.append(f"- Tables: {len(inv.get('tables', []))}")
        lines.append(f"- Columns: {len(inv.get('columns', []))}")
        lines.append("")

    return "\n".join(lines)



# ---------------------------------------------------------------------------
# Load from storage
# ---------------------------------------------------------------------------


def load_report_from_storage(db_path: Path, assessment_id: str) -> Optional[dict]:
    """Load report JSON by assessment id."""
    conn = storage.get_connection(db_path)
    try:
        return storage.get_report(conn, assessment_id)
    finally:
        conn.close()
