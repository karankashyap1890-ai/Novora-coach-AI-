"""
Novora — MCP Tools: Analytics Tools
Expose productivity analytics computations via MCP.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict


def register_analytics_tools(mcp):
    """Register analytics MCP tools."""

    @mcp.tool()
    def get_analytics_summary(sessions: List[dict]) -> dict:
        """
        Compute a productivity summary from session data.

        Args:
            sessions: List of completed session records

        Returns:
            Summary statistics dict
        """
        if not sessions:
            return {
                "total_sessions": 0,
                "total_focus_minutes": 0,
                "total_focus_hours": 0,
                "avg_focus_score": 0,
                "best_score": 0,
                "today_sessions": 0,
                "streak_days": 0,
            }

        today = datetime.now(timezone.utc).date()
        total_focus = sum(s.get("work_minutes", 25) for s in sessions)
        scores = [s["focus_score"] for s in sessions if s.get("focus_score") is not None]
        today_sessions = sum(
            1 for s in sessions
            if s.get("completed_at") and
            _parse_date(s["completed_at"]) == today
        )

        return {
            "total_sessions": len(sessions),
            "total_focus_minutes": total_focus,
            "total_focus_hours": round(total_focus / 60, 1),
            "avg_focus_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "best_score": max(scores, default=0),
            "today_sessions": today_sessions,
            "streak_days": _compute_streak(sessions),
        }

    @mcp.tool()
    def get_daily_trend(sessions: List[dict], days: int = 7) -> Dict[str, int]:
        """
        Compute daily session counts for the past N days.

        Args:
            sessions: List of completed session records
            days: Number of days to look back (1-30)

        Returns:
            Dict mapping date strings to session counts
        """
        days = max(1, min(30, days))
        today = datetime.now(timezone.utc).date()
        daily: Dict[str, int] = {}
        for i in range(days):
            d = today - timedelta(days=i)
            daily[d.isoformat()] = 0

        for s in sessions:
            ts = s.get("completed_at")
            if ts:
                d = _parse_date(ts)
                if d:
                    key = d.isoformat()
                    if key in daily:
                        daily[key] += 1

        return dict(sorted(daily.items()))

    @mcp.tool()
    def get_focus_score_trend(sessions: List[dict]) -> List[dict]:
        """
        Get focus scores over time for charting.

        Args:
            sessions: List of completed session records

        Returns:
            List of {date, score} dicts
        """
        result = []
        for s in sessions:
            if s.get("focus_score") is not None and s.get("completed_at"):
                result.append({
                    "date": s["completed_at"][:10],
                    "score": s["focus_score"],
                    "task": s.get("task_title", ""),
                })
        return sorted(result, key=lambda x: x["date"])


def _parse_date(ts: str):
    try:
        return datetime.fromisoformat(ts.replace("Z", "")).date()
    except Exception:
        return None


def _compute_streak(sessions: List[dict]) -> int:
    dates = set()
    for s in sessions:
        d = _parse_date(s.get("completed_at", ""))
        if d:
            dates.add(d)
    if not dates:
        return 0
    streak = 0
    day = datetime.now(timezone.utc).date()
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak
