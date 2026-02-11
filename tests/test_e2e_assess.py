"""E2E test: create temp DuckDB with known data, run full assess pipeline, assert report shape and failures."""

import json
import shutil
import tempfile
from pathlib import Path

# Sample data: nulls and duplicates so we get Clean factor failures
PRODUCTS_DATA = [
    (1, "apple", 1.5),
    (1, "apple", 1.5),   # duplicate
    (2, None, 2.0),     # null
    (2, None, 2.0),     # duplicate + null
    (3, "cherry", 3.0),
    (4, "date", 4.0),
]


def _make_duckdb(tmpdir: Path) -> str:
    import duckdb
    path = tmpdir / "sample.duckdb"
    conn = duckdb.connect(str(path))
    conn.execute("""
        CREATE TABLE main.products (
            id INTEGER,
            name VARCHAR,
            amount DOUBLE
        )
    """)
    conn.executemany(
        "INSERT INTO main.products (id, name, amount) VALUES (?, ?, ?)",
        PRODUCTS_DATA,
    )
    conn.close()
    return f"duckdb://{path.resolve()}"


def test_e2e_assess_report_structure_and_failures():
    """Run full pipeline against a temp DuckDB; assert report has expected keys and at least one failure."""
    from agent.config import Config
    from agent.pipeline import run_assess

    tmpdir = Path(tempfile.mkdtemp(prefix="aird_e2e_"))
    try:
        connection = _make_duckdb(tmpdir)
        config = Config(connection=connection, no_save=True)
        config = config.with_args(assessment_targets=[{"connection": connection}])

        report = run_assess(config)

        assert "summary" in report
        assert "results" in report
        assert "connection_fingerprint" in report
        summary = report["summary"]
        assert "total_tests" in summary
        assert summary["total_tests"] >= 1
        results = report["results"]
        assert len(results) >= 1
        failures = [r for r in results if r.get("l1_pass") is False]
        assert len(failures) >= 1, "Expected at least one L1 failure (null_rate or duplicate_rate)"
    finally:
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_e2e_assess_with_threshold_override():
    """Run assess with custom thresholds JSON; stricter null_rate should produce more failures."""
    from agent.config import Config
    from agent.pipeline import run_assess

    tmpdir = Path(tempfile.mkdtemp(prefix="aird_e2e_"))
    try:
        connection = _make_duckdb(tmpdir)
        (tmpdir / "thresholds.json").write_text(json.dumps({
            "null_rate": {"l1": 0.01, "l2": 0.01, "l3": 0.01},
        }))
        config = Config(
            connection=connection,
            no_save=True,
            thresholds_path=tmpdir / "thresholds.json",
        )
        config = config.with_args(assessment_targets=[{"connection": connection}])

        report = run_assess(config)

        assert "results" in report
        null_failures = [
            r for r in report["results"]
            if r.get("requirement") == "null_rate" and r.get("l1_pass") is False
        ]
        assert len(null_failures) >= 1
    finally:
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_e2e_assess_with_context_scope():
    """Run assess with context YAML restricting schemas; report should include user_context."""
    import yaml
    from agent.config import Config
    from agent.pipeline import run_assess

    tmpdir = Path(tempfile.mkdtemp(prefix="aird_e2e_"))
    try:
        connection = _make_duckdb(tmpdir)
        (tmpdir / "context.yaml").write_text(yaml.dump({"schemas": ["main"]}))
        config = Config(
            connection=connection,
            no_save=True,
            context_path=tmpdir / "context.yaml",
        )
        config = config.with_args(assessment_targets=[{"connection": connection}])

        report = run_assess(config)

        assert "user_context" in report
        assert report["user_context"].get("schemas") == ["main"]
        assert report["summary"]["total_tests"] >= 1
    finally:
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_e2e_assess_with_survey():
    """Run full pipeline with --survey; report must have question_results with one entry per factor (6)."""
    from agent.config import Config
    from agent.pipeline import run_assess

    tmpdir = Path(tempfile.mkdtemp(prefix="aird_e2e_"))
    try:
        connection = _make_duckdb(tmpdir)
        config = Config(connection=connection, no_save=True, survey=True)
        config = config.with_args(assessment_targets=[{"connection": connection}])

        report = run_assess(config)

        assert "question_results" in report
        qr = report["question_results"]
        assert len(qr) >= 6, "Survey should return at least 6 questions (one per factor)"
        factors = {r["factor"] for r in qr}
        assert "clean" in factors
        assert "contextual" in factors
        assert "compliant" in factors
        for r in qr:
            assert "question_text" in r
            assert "answer" in r
    finally:
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)
