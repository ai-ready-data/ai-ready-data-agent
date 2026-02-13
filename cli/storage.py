"""SQLite storage: assessments history, audit log. Single DB; path from config."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from database results."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


SCHEMA_VERSION = 1


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS _schema (version INTEGER);
        INSERT OR IGNORE INTO _schema (version) VALUES (?);

        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            connection_fingerprint TEXT,
            data_product TEXT,
            report_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT,
            session_id TEXT,
            query_text TEXT NOT NULL,
            target TEXT,
            factor TEXT,
            requirement TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT,
            session_id TEXT,
            phase TEXT,
            role TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS benchmarks (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            labels_json TEXT NOT NULL,
            connections_json TEXT NOT NULL,
            assessment_ids_json TEXT NOT NULL
        );
    """)
    conn.execute("INSERT OR IGNORE INTO _schema (version) VALUES (?)", (SCHEMA_VERSION,))
    # Migration: add data_product column if missing (for databases created before this column existed)
    try:
        conn.execute("SELECT data_product FROM assessments LIMIT 0")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE assessments ADD COLUMN data_product TEXT")


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def save_report(conn: sqlite3.Connection, report: dict, *, data_product: Optional[str] = None) -> str:
    """Persist report JSON; return assessment id (UUID).

    When data_product is provided, the assessment is tagged with that product name
    so it can be filtered in history and used for product-level diffing.
    """
    aid = str(uuid.uuid4())
    created_at = report.get("created_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    fingerprint = report.get("connection_fingerprint") or ""
    conn.execute(
        "INSERT INTO assessments (id, created_at, connection_fingerprint, data_product, report_json) VALUES (?, ?, ?, ?, ?)",
        (aid, created_at, fingerprint, data_product, json.dumps(report, cls=DecimalEncoder)),
    )
    conn.commit()
    return aid


def list_assessments(
    conn: sqlite3.Connection,
    connection_filter: Optional[str] = None,
    data_product_filter: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """List saved assessments; optional filter by connection fingerprint and/or data product."""
    conditions: list[str] = []
    params: list = []
    if connection_filter:
        conditions.append("connection_fingerprint = ?")
        params.append(connection_filter)
    if data_product_filter:
        conditions.append("data_product = ?")
        params.append(data_product_filter)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    rows = conn.execute(
        f"SELECT id, created_at, connection_fingerprint, data_product, report_json FROM assessments{where} ORDER BY created_at DESC LIMIT ?",
        params,
    ).fetchall()
    out = []
    for row in rows:
        r = json.loads(row["report_json"])
        entry: dict = {
            "id": row["id"],
            "created_at": row["created_at"],
            "connection_fingerprint": row["connection_fingerprint"],
            "summary": r.get("summary", {}),
        }
        if row["data_product"]:
            entry["data_product"] = row["data_product"]
        out.append(entry)
    return out


def get_report(conn: sqlite3.Connection, assessment_id: str) -> Optional[dict]:
    """Load full report JSON by id."""
    row = conn.execute("SELECT report_json FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if not row:
        return None
    return json.loads(row["report_json"])


# ---------------------------------------------------------------------------
# Benchmark storage
# ---------------------------------------------------------------------------


def save_benchmark(
    conn: sqlite3.Connection,
    labels: list,
    connections: list,
    assessment_ids: list,
) -> str:
    """Persist a benchmark group record linking individual assessment reports.

    Returns the benchmark id (UUID).
    """
    bid = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn.execute(
        "INSERT INTO benchmarks (id, created_at, labels_json, connections_json, assessment_ids_json) VALUES (?, ?, ?, ?, ?)",
        (
            bid,
            created_at,
            json.dumps(labels),
            json.dumps(connections),
            json.dumps(assessment_ids),
        ),
    )
    conn.commit()
    return bid


def list_benchmarks(conn: sqlite3.Connection, limit: int = 20) -> list:
    """List saved benchmark groups, most recent first."""
    rows = conn.execute(
        "SELECT id, created_at, labels_json, connections_json, assessment_ids_json "
        "FROM benchmarks ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    out = []
    for row in rows:
        out.append({
            "id": row["id"],
            "created_at": row["created_at"],
            "labels": json.loads(row["labels_json"]),
            "connections": json.loads(row["connections_json"]),
            "assessment_ids": json.loads(row["assessment_ids_json"]),
        })
    return out


def get_benchmark(conn: sqlite3.Connection, benchmark_id: str) -> Optional[dict]:
    """Load a benchmark group record by id."""
    row = conn.execute(
        "SELECT id, created_at, labels_json, connections_json, assessment_ids_json "
        "FROM benchmarks WHERE id = ?",
        (benchmark_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "labels": json.loads(row["labels_json"]),
        "connections": json.loads(row["connections_json"]),
        "assessment_ids": json.loads(row["assessment_ids_json"]),
    }


def write_audit_query(
    conn: sqlite3.Connection,
    query_text: str,
    *,
    assessment_id: Optional[str] = None,
    session_id: Optional[str] = None,
    target: Optional[str] = None,
    factor: Optional[str] = None,
    requirement: Optional[str] = None,
) -> None:
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn.execute(
        "INSERT INTO audit_queries (assessment_id, session_id, query_text, target, factor, requirement, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (assessment_id, session_id, query_text, target, factor, requirement, created),
    )
    conn.commit()


def write_audit_conversation(
    conn: sqlite3.Connection,
    content: str,
    *,
    role: str = "agent",
    assessment_id: Optional[str] = None,
    session_id: Optional[str] = None,
    phase: Optional[str] = None,
) -> None:
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn.execute(
        "INSERT INTO audit_conversation (assessment_id, session_id, phase, role, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (assessment_id, session_id, phase, role, content, created),
    )
    conn.commit()


class Storage:
    """Facade over SQLite for assessments and audit. Caller opens/closes connection or uses context."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        return get_connection(self.db_path)
