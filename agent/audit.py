"""Audit sink: receives query and conversation events, writes to storage when audit is enabled."""

from pathlib import Path
from typing import Optional

from agent import storage


class AuditSink:
    """When enabled, appends query and conversation events to the same SQLite DB via storage."""

    def __init__(self, db_path: Path, enabled: bool, assessment_id: Optional[str] = None):
        self.db_path = db_path
        self.enabled = enabled
        self.assessment_id = assessment_id
        self._session_id: Optional[str] = None

    def log_query(
        self,
        query_text: str,
        *,
        target: Optional[str] = None,
        factor: Optional[str] = None,
        requirement: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        conn = storage.get_connection(self.db_path)
        try:
            storage.write_audit_query(
                conn,
                query_text,
                assessment_id=self.assessment_id,
                session_id=self._session_id,
                target=target,
                factor=factor,
                requirement=requirement,
            )
        finally:
            conn.close()

    def log_conversation(
        self,
        content: str,
        *,
        role: str = "agent",
        phase: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        conn = storage.get_connection(self.db_path)
        try:
            storage.write_audit_conversation(
                conn,
                content,
                role=role,
                assessment_id=self.assessment_id,
                session_id=self._session_id,
                phase=phase,
            )
        finally:
            conn.close()
