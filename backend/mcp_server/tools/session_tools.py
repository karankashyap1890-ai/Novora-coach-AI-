"""
Novora — MCP Tools: Session Tools
Log, retrieve, and manage Pomodoro sessions via MCP.
"""
from datetime import datetime, timezone
from typing import Optional


def register_session_tools(mcp):
    """Register session management MCP tools."""

    # In-memory session store (the DB is the persistent source — this is the MCP layer)
    _sessions: dict = {}

    @mcp.tool()
    def log_session(
        user_id: str,
        task_title: str,
        session_number: int,
        work_minutes: int = 25,
        focus_score: Optional[float] = None,
        reflection_note: Optional[str] = None,
    ) -> dict:
        """
        Log a completed Pomodoro session to the in-memory store.

        Args:
            user_id: Authenticated user's ID
            task_title: Task worked on
            session_number: Session sequence number
            work_minutes: Duration of work in minutes
            focus_score: Focus quality rating (1.0-5.0)
            reflection_note: User's reflection text

        Returns:
            Logged session record
        """
        session_id = f"{user_id}_{session_number}_{int(datetime.now(timezone.utc).timestamp())}"
        record = {
            "id": session_id,
            "user_id": user_id,
            "task_title": task_title,
            "session_number": session_number,
            "work_minutes": work_minutes,
            "focus_score": focus_score,
            "reflection_note": reflection_note,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        _sessions.setdefault(user_id, []).append(record)
        return record

    @mcp.tool()
    def get_sessions(user_id: str, limit: int = 50) -> list:
        """
        Retrieve recent sessions for a user.

        Args:
            user_id: Authenticated user's ID
            limit: Maximum number of sessions to return

        Returns:
            List of session records (newest first)
        """
        user_sessions = _sessions.get(user_id, [])
        return user_sessions[-limit:][::-1]

    @mcp.tool()
    def get_session_by_id(user_id: str, session_id: str) -> Optional[dict]:
        """
        Retrieve a specific session by ID.

        Args:
            user_id: Authenticated user's ID
            session_id: Session identifier

        Returns:
            Session record or None
        """
        for s in _sessions.get(user_id, []):
            if s["id"] == session_id:
                return s
        return None

    @mcp.tool()
    def clear_sessions(user_id: str) -> dict:
        """
        Clear all sessions for a user (use with caution).

        Args:
            user_id: Authenticated user's ID

        Returns:
            Confirmation with count of cleared sessions
        """
        count = len(_sessions.pop(user_id, []))
        return {"cleared": count, "user_id": user_id}
