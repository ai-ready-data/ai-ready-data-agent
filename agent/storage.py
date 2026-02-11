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
    """)
    conn.execute("INSERT OR IGNORE INTO _schema (version) VALUES (?)", (SCHEMA_VERSION,))


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def save_report(conn: sqlite3.Connection, report: dict) -> str:
    """Persist report JSON; return assessment id (UUID)."""
    aid = str(uuid.uuid4())
    created_at = report.get("created_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    fingerprint = report.get("connection_fingerprint") or ""
    conn.execute(
        "INSERT INTO assessments (id, created_at, connection_fingerprint, report_json) VALUES (?, ?, ?, ?)",
        (aid, created_at, fingerprint, json.dumps(report, cls=DecimalEncoder)),
    )
    conn.commit()
    return aid


def list_assessments(
    conn: sqlite3.Connection,
    connection_filter: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """List saved assessments; optional filter by connection fingerprint."""
    if connection_filter:
        rows = conn.execute(
            "SELECT id, created_at, connection_fingerprint, report_json FROM assessments WHERE connection_fingerprint = ? ORDER BY created_at DESC LIMIT ?",
            (connection_filter, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, created_at, connection_fingerprint, report_json FROM assessments ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for row in rows:
        r = json.loads(row["report_json"])
        out.append({
            "id": row["id"],
            "created_at": row["created_at"],
            "connection_fingerprint": row["connection_fingerprint"],
            "summary": r.get("summary", {}),
        })
    return out


def get_report(conn: sqlite3.Connection, assessment_id: str) -> Optional[dict]:
    """Load full report JSON by id."""
    row = conn.execute("SELECT report_json FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if not row:
        return None
    return json.loads(row["report_json"])


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
