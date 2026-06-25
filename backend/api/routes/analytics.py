"""
Novora — FastAPI Routes: Analytics
Provides productivity statistics and trend data.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import PomodoroSession, SessionState
from security import get_current_user_id
from agents import get_bus, AgentMessage, MessageType

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _session_to_dict(s: PomodoroSession) -> dict:
    return {
        "id": s.id,
        "session_number": s.session_number,
        "work_minutes": s.work_minutes,
        "focus_score": s.focus_score,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "task_title": "",  # joined separately if needed
    }


@router.get("/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get full productivity summary via the AnalyticsAgent."""
    result = await db.execute(
        select(PomodoroSession)
        .where(
            PomodoroSession.user_id == user_id,
            PomodoroSession.state == SessionState.COMPLETED,
        )
        .order_by(desc(PomodoroSession.created_at))
        .limit(200)
    )
    sessions = result.scalars().all()
    sessions_data = [_session_to_dict(s) for s in sessions]

    bus = get_bus()
    msg = AgentMessage(
        type=MessageType.ANALYTICS,
        payload={"user_id": user_id, "sessions": sessions_data, "sub_type": "summary"},
        sender=user_id,
        recipient="analytics",
    )
    response = await bus.send(msg)
    return {
        "analytics": response.payload.get("analytics", {}),
        "message": response.payload.get("content", ""),
        "total_sessions": len(sessions_data),
    }


@router.get("/trend")
async def get_trend(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get 7-day daily session trend."""
    result = await db.execute(
        select(PomodoroSession)
        .where(
            PomodoroSession.user_id == user_id,
            PomodoroSession.state == SessionState.COMPLETED,
        )
    )
    sessions = result.scalars().all()
    sessions_data = [_session_to_dict(s) for s in sessions]

    bus = get_bus()
    msg = AgentMessage(
        type=MessageType.ANALYTICS,
        payload={"user_id": user_id, "sessions": sessions_data, "sub_type": "trend"},
        sender=user_id,
        recipient="analytics",
    )
    response = await bus.send(msg)
    return {"trend": response.payload.get("analytics", {}), "days": days}
