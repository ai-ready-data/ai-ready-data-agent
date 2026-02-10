"""Create a sample DuckDB file for E2E testing of the Clean factor suite.

Usage:
  python scripts/create_sample_duckdb.py [path]
  Default path: sample.duckdb in repo root (or cwd).

The DB has one table, main.products, with intentional nulls and duplicates
so null_rate and duplicate_rate tests produce meaningful pass/fail results.
"""

import sys
from pathlib import Path

import duckdb

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "sample.duckdb"
    path = path.resolve()

    conn = duckdb.connect(str(path))
    conn.execute("""
        CREATE OR REPLACE TABLE main.products (
            id INTEGER,
            name VARCHAR,
            amount DOUBLE
        )
    """)
    # Insert rows: some nulls in name, some duplicate rows (id=1 twice, id=2 twice)
    conn.executemany(
        "INSERT INTO main.products (id, name, amount) VALUES (?, ?, ?)",
        [
            (1, "apple", 1.5),
            (1, "apple", 1.5),   # duplicate
            (2, None, 2.0),      # null
            (2, None, 2.0),     # duplicate + null
            (3, "cherry", 3.0),
            (4, "date", 4.0),
        ],
    )
    conn.close()
    print(f"Created {path} with main.products (6 rows, nulls and duplicates).")


if __name__ == "__main__":
    main()
