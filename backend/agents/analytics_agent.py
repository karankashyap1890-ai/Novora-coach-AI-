"""
Novora — AnalyticsAgent
Computes productivity statistics from session history.
Runs 100% offline — pure Python math, no external dependencies.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from agents import BaseAgent, AgentBus, AgentMessage, MessageType
from skills.pomodoro_skill import pomodoro_skill


class AnalyticsAgent(BaseAgent):
    """
    Responsible for:
    - Computing daily / weekly focus statistics
    - Tracking streaks and personal bests
    - Generating trend analysis and productivity scores
    - Providing actionable insights from session data
    """

    def __init__(self, bus: AgentBus):
        super().__init__("analytics", bus)

    async def process(self, message: AgentMessage) -> AgentMessage:
        user_id = message.payload.get("user_id", "default")
        sessions_data = message.payload.get("sessions", [])
        sub_type = message.payload.get("sub_type", "summary")

        if sub_type == "summary":
            stats = self._compute_summary(sessions_data)
            content = self._format_summary(stats)
        elif sub_type == "trend":
            stats = self._compute_trend(sessions_data)
            content = self._format_trend(stats)
        elif sub_type == "streak":
            streak = self._compute_streak(sessions_data)
            content = f"🔥 **Current Streak:** {streak} consecutive days of Pomodoros!"
        else:
            stats = self._compute_summary(sessions_data)
            content = self._format_summary(stats)

        return self.reply(message, content, {"analytics": stats if "stats" in dir() else {}})

    def _compute_summary(self, sessions: List[Dict]) -> Dict[str, Any]:
        if not sessions:
            return {
                "total_sessions": 0,
                "total_focus_minutes": 0,
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
            datetime.fromisoformat(s["completed_at"].replace("Z","")).date() == today
        )

        return {
            "total_sessions": len(sessions),
            "total_focus_minutes": total_focus,
            "total_focus_hours": round(total_focus / 60, 1),
            "avg_focus_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "best_score": max(scores, default=0),
            "today_sessions": today_sessions,
            "streak_days": self._compute_streak(sessions),
        }

    def _compute_streak(self, sessions: List[Dict]) -> int:
        """Count consecutive days with at least one completed session."""
        if not sessions:
            return 0
        dates = set()
        for s in sessions:
            ts = s.get("completed_at")
            if ts:
                try:
                    dates.add(datetime.fromisoformat(ts.replace("Z","")).date())
                except Exception:
                    pass

        if not dates:
            return 0

        streak = 0
        day = datetime.now(timezone.utc).date()
        while day in dates:
            streak += 1
            day -= timedelta(days=1)
        return streak

    def _compute_trend(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Compute last-7-day daily session counts."""
        today = datetime.now(timezone.utc).date()
        daily: Dict[str, int] = {}
        for i in range(7):
            d = today - timedelta(days=i)
            daily[d.isoformat()] = 0

        for s in sessions:
            ts = s.get("completed_at")
            if ts:
                try:
                    d = datetime.fromisoformat(ts.replace("Z","")).date()
                    key = d.isoformat()
                    if key in daily:
                        daily[key] += 1
                except Exception:
                    pass

        return {"daily_counts": daily}

    def _format_summary(self, stats: Dict) -> str:
        if stats["total_sessions"] == 0:
            return (
                "📊 **Your Analytics Dashboard**\n\n"
                "No sessions recorded yet! Start your first Pomodoro to see your stats here. 🚀"
            )

        lines = [
            "📊 **Your Productivity Summary**",
            "",
            f"🍅 **Total Sessions:** {stats['total_sessions']}",
            f"⏱️ **Total Focus Time:** {stats['total_focus_hours']}h ({stats['total_focus_minutes']} min)",
            f"📅 **Today:** {stats['today_sessions']} sessions",
            f"🔥 **Streak:** {stats['streak_days']} consecutive days",
            f"⭐ **Avg Focus Score:** {stats['avg_focus_score']}/5",
            f"🏆 **Best Score:** {stats['best_score']}/5",
            "",
        ]
        # Motivational insight
        if stats["total_sessions"] >= 100:
            lines.append("🎖️ **Century Club!** 100+ sessions — you're a Pomodoro legend!")
        elif stats["total_sessions"] >= 50:
            lines.append("🥇 **50 sessions!** You've built a powerful focus habit!")
        elif stats["total_sessions"] >= 10:
            lines.append("📈 Great momentum! You're building a real productivity habit.")
        else:
            lines.append("🌱 Every journey begins with a single session. You're off to a great start!")

        return "\n".join(lines)

    def _format_trend(self, trend: Dict) -> str:
        lines = ["📈 **7-Day Focus Trend**", ""]
        for date_str, count in sorted(trend["daily_counts"].items()):
            bar = "🍅" * count if count > 0 else "—"
            lines.append(f"`{date_str}` {bar} ({count} sessions)")
        return "\n".join(lines)
