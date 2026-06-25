"""
Novora — Agent Skills: Core Pomodoro Logic
Reusable skill module shared across all agents.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class PomodoroState(str, Enum):
    IDLE = "idle"
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class PomodoroContext:
    """Holds the live state of a running Pomodoro session."""
    task_title: str = "Unnamed Task"
    state: PomodoroState = PomodoroState.IDLE
    session_number: int = 0
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    elapsed_seconds: int = 0
    completed_sessions: List[dict] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.state in (PomodoroState.WORK, PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK)

    @property
    def current_duration_minutes(self) -> int:
        if self.state == PomodoroState.WORK:
            return self.work_minutes
        if self.state == PomodoroState.SHORT_BREAK:
            return self.short_break_minutes
        if self.state == PomodoroState.LONG_BREAK:
            return self.long_break_minutes
        return 0

    @property
    def remaining_seconds(self) -> int:
        if not self.is_active or self.started_at is None:
            return self.current_duration_minutes * 60
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        elapsed = (now - self.started_at).total_seconds() + self.elapsed_seconds
        remaining = self.current_duration_minutes * 60 - elapsed
        return max(0, int(remaining))

    def start_work(self, task_title: str = None):
        if task_title:
            self.task_title = task_title
        self.session_number += 1
        self.state = PomodoroState.WORK
        self.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.elapsed_seconds = 0

    def start_break(self):
        is_long = (self.session_number % self.sessions_before_long_break == 0)
        self.state = PomodoroState.LONG_BREAK if is_long else PomodoroState.SHORT_BREAK
        self.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.elapsed_seconds = 0

    def pause(self):
        if self.state in (PomodoroState.WORK, PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            self.elapsed_seconds += int((now - self.started_at).total_seconds())
            self.paused_at = now
            self.state = PomodoroState.PAUSED

    def resume(self):
        if self.state == PomodoroState.PAUSED:
            self.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.state = PomodoroState.WORK

    def complete_session(self, focus_score: float = None, note: str = None):
        self.completed_sessions.append({
            "session_number": self.session_number,
            "task": self.task_title,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "focus_score": focus_score,
            "note": note,
        })

    def to_dict(self) -> dict:
        return {
            "task_title": self.task_title,
            "state": self.state.value,
            "session_number": self.session_number,
            "work_minutes": self.work_minutes,
            "remaining_seconds": self.remaining_seconds,
            "completed_sessions": len(self.completed_sessions),
            "is_active": self.is_active,
        }


class PomodoroSkill:
    """
    Reusable skill that encapsulates Pomodoro logic.
    Agents invoke methods on this class via the MCP server tools.
    """

    def __init__(self):
        self._contexts: dict[str, PomodoroContext] = {}

    def get_or_create(self, user_id: str) -> PomodoroContext:
        if user_id not in self._contexts:
            self._contexts[user_id] = PomodoroContext()
        return self._contexts[user_id]

    def start_session(self, user_id: str, task_title: str, work_minutes: int = 25) -> dict:
        ctx = self.get_or_create(user_id)
        ctx.work_minutes = work_minutes
        ctx.start_work(task_title)
        return ctx.to_dict()

    def pause_session(self, user_id: str) -> dict:
        ctx = self.get_or_create(user_id)
        ctx.pause()
        return ctx.to_dict()

    def resume_session(self, user_id: str) -> dict:
        ctx = self.get_or_create(user_id)
        ctx.resume()
        return ctx.to_dict()

    def get_status(self, user_id: str) -> dict:
        ctx = self.get_or_create(user_id)
        return ctx.to_dict()

    def begin_break(self, user_id: str) -> dict:
        ctx = self.get_or_create(user_id)
        ctx.start_break()
        return ctx.to_dict()

    def complete_work_session(self, user_id: str, focus_score: float = None, note: str = None) -> dict:
        ctx = self.get_or_create(user_id)
        ctx.complete_session(focus_score, note)
        ctx.start_break()
        return ctx.to_dict()


# Global singleton shared across the app
pomodoro_skill = PomodoroSkill()
