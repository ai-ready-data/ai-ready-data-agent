#!/usr/bin/env python3
"""Verify the assessment agent works with no credentials or files.

Creates temporary DuckDB and SQLite databases (in a temp dir), populates them
with sample data, runs the assessment pipeline for both, then removes the temp
dir. No credentials required, no files left behind. Run this when you first
land (e.g. after clone + pip install) to confirm everything works before the
user provides real credentials.

Usage:
  python scripts/verify_setup.py              # In-memory only; exit 0 if OK
  python scripts/verify_setup.py --write-files [dir]   # Also write sample.duckdb, sample.sqlite, connections.yaml

Exit code: 0 if all assessments succeed, 1 otherwise.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Same row data for both DBs: nulls and duplicates for meaningful Clean factor results
PRODUCTS_DATA = [
    (1, "apple", 1.5),
    (1, "apple", 1.5),   # duplicate
    (2, None, 2.0),      # null
    (2, None, 2.0),      # duplicate + null
    (3, "cherry", 3.0),
    (4, "date", 4.0),
]


def create_duckdb_in_memory():
    import duckdb
    conn = duckdb.connect(":memory:")
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


def create_sqlite_in_memory():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE products (
            id INTEGER,
            name TEXT,
            amount REAL
        )
    """)
    conn.executemany(
        "INSERT INTO products (id, name, amount) VALUES (?, ?, ?)",
        PRODUCTS_DATA,
    )
    conn.commit()
    conn.close()


def run_assess_in_process(connection_string: str) -> dict:
    """Run discover → run → build_report in this process. Returns report dict."""
    from agent.discovery import discover
    from agent.run import run_tests
    from agent.report import build_report
    from agent.pipeline import _fingerprint

    inv = discover(connection_string, schemas=None, tables=None)
    results = run_tests(connection_string, inv, suite_name="auto", dry_run=False)
    report = build_report(
        results,
        inventory=inv,
        connection_fingerprint=_fingerprint(connection_string),
    )
    return report


def verify_in_memory() -> tuple[bool, list[str]]:
    """Create in-memory DBs, run assess for each, return (all_ok, messages)."""
    messages = []
    ok = True

    # In-memory DBs can't be shared with get_platform() (new connection = new DB).
    # Use a temp dir: create and populate files, run assess, then remove the dir.
    import tempfile
    # Prefer temp dir under cwd so sandboxes/containers don't block /tmp
    try:
        tmpdir = tempfile.mkdtemp(prefix="aird_verify_", dir=Path.cwd())
        t = Path(tmpdir)
        cleanup_dir = t
    except OSError:
        tmpdir = tempfile.mkdtemp(prefix="aird_verify_")
        t = Path(tmpdir)
        cleanup_dir = t
    try:
        duckdb_path = t / "sample.duckdb"
        sqlite_path = t / "sample.sqlite"

        # Populate DuckDB
        import duckdb
        conn_d = duckdb.connect(str(duckdb_path))
        conn_d.execute("""
            CREATE TABLE main.products (
                id INTEGER,
                name VARCHAR,
                amount DOUBLE
            )
        """)
        conn_d.executemany(
            "INSERT INTO main.products (id, name, amount) VALUES (?, ?, ?)",
            PRODUCTS_DATA,
        )
        conn_d.close()

        # Populate SQLite
        conn_s = sqlite3.connect(str(sqlite_path))
        conn_s.execute("""
            CREATE TABLE products (
                id INTEGER,
                name TEXT,
                amount REAL
            )
        """)
        conn_s.executemany(
            "INSERT INTO products (id, name, amount) VALUES (?, ?, ?)",
            PRODUCTS_DATA,
        )
        conn_s.commit()
        conn_s.close()

        # Run assessment for each (use absolute paths so SQLite can open the file)
        duckdb_conn = f"duckdb://{duckdb_path.resolve()}"
        sqlite_conn = f"sqlite:///{sqlite_path.resolve()}"
        for label, conn_str in [
            ("DuckDB", duckdb_conn),
            ("SQLite", sqlite_conn),
        ]:
            try:
                report = run_assess_in_process(conn_str)
                s = report.get("summary", {})
                n = s.get("total_tests", 0)
                pct = s.get("l1_pct", 0)
                messages.append(f"  {label}: {n} tests, L1 {pct}% pass")
            except Exception as e:
                ok = False
                messages.append(f"  {label}: FAIL — {e}")
    finally:
        import shutil
        if cleanup_dir.exists():
            shutil.rmtree(cleanup_dir, ignore_errors=True)

    return ok, messages


def write_files(out_dir: Path) -> None:
    """Write sample.duckdb, sample.sqlite, and connections.yaml to out_dir."""
    import duckdb

    duckdb_path = out_dir / "sample.duckdb"
    sqlite_path = out_dir / "sample.sqlite"
    connections_path = out_dir / "connections.yaml"

    conn_d = duckdb.connect(str(duckdb_path))
    conn_d.execute("""
        CREATE OR REPLACE TABLE main.products (
            id INTEGER,
            name VARCHAR,
            amount DOUBLE
        )
    """)
    conn_d.executemany(
        "INSERT INTO main.products (id, name, amount) VALUES (?, ?, ?)",
        PRODUCTS_DATA,
    )
    conn_d.close()

    conn_s = sqlite3.connect(str(sqlite_path))
    conn_s.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER,
            name TEXT,
            amount REAL
        )
    """)
    conn_s.executemany(
        "INSERT INTO products (id, name, amount) VALUES (?, ?, ?)",
        PRODUCTS_DATA,
    )
    conn_s.commit()
    conn_s.close()

    duckdb_rel = "sample.duckdb"
    sqlite_rel = "sample.sqlite"
    connections_path.write_text(
        "# Sample connections for estate (run from repo root)\n"
        "entries:\n"
        f'  - "duckdb://{duckdb_rel}"\n'
        f'  - "sqlite://{sqlite_rel}"\n'
    )
    print(f"  Wrote {duckdb_path}, {sqlite_path}, {connections_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the assessment agent (in-memory style, no credentials). Optionally write sample files."
    )
    parser.add_argument(
        "--write-files",
        nargs="?",
        const="",
        metavar="DIR",
        help="Also write sample.duckdb, sample.sqlite, connections.yaml (default: repo root)",
    )
    args = parser.parse_args()

    print("Verifying assessment agent (DuckDB + SQLite, no credentials required)...")
    ok, messages = verify_in_memory()
    for m in messages:
        print(m)
    if not ok:
        print("Verification failed.")
        return 1

    write_files_requested = getattr(args, "write_files", None) is not None
    if write_files_requested:
        root = Path(__file__).resolve().parent.parent
        out_dir = root if (args.write_files == "") else Path(args.write_files).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        print("\nWriting sample files for CLI/estate use:")
        write_files(out_dir)
        print("  Then: aird assess -c \"duckdb://sample.duckdb\" -o markdown")
        print("        aird assess --connections-file connections.yaml -o markdown")

    print("\nOK — agent is ready. You can now run assess with user-provided credentials.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
