import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.inputs import BoardMessage, DocumentInput, FounderRequest
from models.outputs import BoardBrief, BoardCritique, ExecutiveBoardSummary, InvestorReview


def get_db_path() -> str:
    return os.getenv("DB_PATH", "data/advisory_board.db")


def _connection() -> sqlite3.Connection:
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            phase TEXT NOT NULL,
            startup_name TEXT,
            ask_preview TEXT,
            document_count INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(val) for key, val in value.items()}
    return value


def _deserialize_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    founder_request = data.get("founder_request")
    documents = data.get("documents") or []
    messages = data.get("messages") or []
    latest_reviews = data.get("latest_reviews") or {}
    critique_history = data.get("critique_history") or []
    board_brief = data.get("board_brief")
    executive_summary = data.get("executive_summary")

    return {
        "phase": data.get("phase", "idle"),
        "founder_request": FounderRequest(**founder_request) if founder_request else None,
        "documents": [DocumentInput(**doc) for doc in documents],
        "document_warnings": data.get("document_warnings") or [],
        "messages": [BoardMessage(**msg) for msg in messages],
        "latest_reviews": {key: InvestorReview(**val) for key, val in latest_reviews.items()},
        "critique_history": [BoardCritique(**item) for item in critique_history],
        "revision_map": data.get("revision_map") or {},
        "board_brief": BoardBrief(**board_brief) if board_brief else None,
        "executive_summary": ExecutiveBoardSummary(**executive_summary) if executive_summary else None,
        "status_log": data.get("status_log") or [],
        "error_message": data.get("error_message"),
    }


def persist_session_snapshot(session_id: str, state: dict[str, Any]) -> None:
    phase = state.get("phase", "idle")
    founder_request = state.get("founder_request")
    startup_name = founder_request.startup_name if founder_request else None
    ask_preview = founder_request.ask[:180] if founder_request and founder_request.ask else ""
    document_count = len(state.get("documents") or [])

    payload = {
        "phase": phase,
        "founder_request": _serialize(founder_request),
        "documents": _serialize(state.get("documents") or []),
        "document_warnings": state.get("document_warnings") or [],
        "messages": _serialize(state.get("messages") or []),
        "latest_reviews": _serialize(state.get("latest_reviews") or {}),
        "critique_history": _serialize(state.get("critique_history") or []),
        "revision_map": state.get("revision_map") or {},
        "board_brief": _serialize(state.get("board_brief")),
        "executive_summary": _serialize(state.get("executive_summary")),
        "status_log": state.get("status_log") or [],
        "error_message": state.get("error_message"),
    }

    conn = _connection()
    try:
        _ensure_schema(conn)
        now = _now_iso()
        existing = conn.execute("SELECT session_id, created_at FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        created_at = existing["created_at"] if existing else now

        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (
                session_id, created_at, updated_at, phase,
                startup_name, ask_preview, document_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                now,
                phase,
                startup_name,
                ask_preview,
                document_count,
                json.dumps(payload),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_recent_sessions(limit: int = 20) -> list[dict[str, Any]]:
    conn = _connection()
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT session_id, created_at, updated_at, phase, startup_name, ask_preview, document_count
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def load_session_snapshot(session_id: str) -> dict[str, Any] | None:
    conn = _connection()
    try:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT payload_json FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        return _deserialize_snapshot(payload)
    finally:
        conn.close()
