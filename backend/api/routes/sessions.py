"""
Novora — FastAPI Routes: Sessions
CRUD for Pomodoro session management.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import PomodoroSession, Task, SessionState
from security import SessionStart, SessionReflection, get_current_user_id
from skills.pomodoro_skill import pomodoro_skill

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_session(
    body: SessionStart,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Start a new Pomodoro work session."""
    # Get task title if task_id provided
    task_title = "My Task"
    if body.task_id:
        result = await db.execute(
            select(Task).where(Task.id == body.task_id, Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task_title = task.title

    # Count existing sessions to get next session number
    result = await db.execute(
        select(PomodoroSession).where(PomodoroSession.user_id == user_id)
    )
    all_sessions = result.scalars().all()
    session_num = len(all_sessions) + 1

    session = PomodoroSession(
        user_id=user_id,
        task_id=body.task_id,
        state=SessionState.WORK,
        session_number=session_num,
        work_minutes=body.work_minutes,
        break_minutes=body.break_minutes,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(session)
    await db.flush()

    # Sync with skill
    pomodoro_skill.start_session(user_id, task_title, body.work_minutes)

    return {
        "id": session.id,
        "session_number": session_num,
        "state": session.state.value,
        "work_minutes": session.work_minutes,
        "task_title": task_title,
        "started_at": session.started_at.isoformat(),
    }


@router.patch("/{session_id}/complete")
async def complete_session(
    session_id: str,
    body: SessionReflection,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mark a session as complete and record reflection."""
    result = await db.execute(
        select(PomodoroSession).where(
            PomodoroSession.id == session_id,
            PomodoroSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.state = SessionState.COMPLETED
    session.focus_score = body.focus_score
    session.reflection_note = body.reflection_note
    session.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    return {
        "id": session.id,
        "state": "completed",
        "focus_score": session.focus_score,
        "completed_at": session.completed_at.isoformat(),
    }


@router.get("/")
async def list_sessions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all sessions for the current user."""
    result = await db.execute(
        select(PomodoroSession)
        .where(PomodoroSession.user_id == user_id)
        .order_by(desc(PomodoroSession.created_at))
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "session_number": s.session_number,
            "state": s.state.value,
            "work_minutes": s.work_minutes,
            "focus_score": s.focus_score,
            "reflection_note": s.reflection_note,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/status")
async def get_session_status(user_id: str = Depends(get_current_user_id)):
    """Get the current live timer status."""
    state = pomodoro_skill.get_status(user_id)
    return state
