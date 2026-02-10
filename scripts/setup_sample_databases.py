#!/usr/bin/env python3
"""Set up sample DuckDB and SQLite databases for E2E and estate testing.

Creates:
  - sample.duckdb (DuckDB, main.products with nulls/duplicates)
  - sample.sqlite (SQLite, main.products with same schema and data)
  - connections.txt (one connection string per line for estate runs)

Usage:
  python scripts/setup_sample_databases.py [output_dir]
  Default output_dir: repo root (parent of scripts/).

Then run:
  # Single database
  aird assess -c "duckdb://sample.duckdb" -o markdown
  aird assess -c "sqlite://sample.sqlite" -o markdown

  # Estate (both in one report)
  aird assess --connections-file connections.txt -o markdown
  # Or: aird assess -c "duckdb://sample.duckdb" -c "sqlite://sample.sqlite" -o markdown
"""

import sqlite3
import sys
from pathlib import Path

# Same row data for both DBs: nulls and duplicates for meaningful Clean factor results
PRODUCTS_DATA = [
    (1, "apple", 1.5),
    (1, "apple", 1.5),   # duplicate
    (2, None, 2.0),     # null
    (2, None, 2.0),     # duplicate + null
    (3, "cherry", 3.0),
    (4, "date", 4.0),
]


def create_duckdb(path: Path) -> None:
    import duckdb
    conn = duckdb.connect(str(path))
    conn.execute("""
        CREATE OR REPLACE TABLE main.products (
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


def create_sqlite(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
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


def write_connections_file(out_dir: Path, connections_path: Path) -> None:
    # Use paths relative to cwd when running from repo root
    duckdb_rel = "sample.duckdb" if (out_dir / "sample.duckdb").exists() else str(out_dir / "sample.duckdb")
    sqlite_rel = "sample.sqlite" if (out_dir / "sample.sqlite").exists() else str(out_dir / "sample.sqlite")
    lines = [
        "# Sample connections for estate E2E (run from repo root)",
        f"duckdb://{duckdb_rel}",
        f"sqlite://{sqlite_rel}",
        "",
    ]
    connections_path.write_text("\n".join(lines))


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root

    duckdb_path = out_dir / "sample.duckdb"
    sqlite_path = out_dir / "sample.sqlite"
    connections_path = out_dir / "connections.txt"

    print(f"Creating sample databases in {out_dir} ...")
    create_duckdb(duckdb_path)
    print(f"  Created {duckdb_path}")
    create_sqlite(sqlite_path)
    print(f"  Created {sqlite_path}")
    write_connections_file(out_dir, connections_path)
    print(f"  Created {connections_path}")

    print("\nRun from repo root:")
    print("  # Single database")
    print('  aird assess -c "duckdb://sample.duckdb" -o markdown')
    print('  aird assess -c "sqlite://sample.sqlite" -o markdown')
    print("  # Estate (both)")
    print("  aird assess --connections-file connections.txt -o markdown")


if __name__ == "__main__":
    main()
