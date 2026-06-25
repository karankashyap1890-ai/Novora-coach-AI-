"""
Novora — FastAPI Routes: Chat (WebSocket + REST)
The main interface for communicating with the multi-agent system.
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import ChatMessage, PomodoroSession
from security import ChatRequest, get_current_user_id, sanitize_agent_output, sanitize_user_input
from agents import get_bus, AgentMessage, MessageType
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/chat", tags=["Chat"])

# Active WebSocket connections per user
_connections: dict[str, WebSocket] = {}


async def _get_agent_response(user_id: str, text: str, sessions: list = None) -> str:
    """Route a user message through the multi-agent system."""
    bus = get_bus()
    message = AgentMessage(
        type=MessageType.USER_CHAT,
        payload={
            "user_id": user_id,
            "text": text,
            "sessions": sessions or [],
        },
        sender=user_id,
        recipient="orchestrator",
    )
    # Simulate a small delay to feel natural
    await asyncio.sleep(settings.agent_response_delay_ms / 1000)
    response = await bus.send(message)
    if response:
        return sanitize_agent_output(response.payload.get("content", "I'm here! How can I help?"))
    return "I'm here to help! What are you working on today? 🚀"


@router.post("/message")
async def send_message(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Send a message and get an agent response (REST endpoint)."""
    clean_text = sanitize_user_input(body.message)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Store user message
    user_msg = ChatMessage(
        user_id=user_id,
        session_id=body.session_id,
        role="user",
        content=clean_text,
    )
    db.add(user_msg)

    # Get agent response
    agent_text = await _get_agent_response(user_id, clean_text)

    # Store agent response
    agent_msg = ChatMessage(
        user_id=user_id,
        session_id=body.session_id,
        role="assistant",
        content=agent_text,
    )
    db.add(agent_msg)
    await db.flush()

    return {
        "user_message": {"id": user_msg.id, "content": clean_text, "role": "user"},
        "agent_message": {"id": agent_msg.id, "content": agent_text, "role": "assistant"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve recent chat messages for the current user."""
    from sqlalchemy import select, desc
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in reversed(messages)
    ]


@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time bidirectional chat.
    Sends agent responses as streaming tokens.
    """
    await websocket.accept()
    _connections[user_id] = websocket

    # Send welcome message
    await websocket.send_json({
        "type": "agent_message",
        "content": "👋 Hello! I'm Coach Novora — your personal Pomodoro productivity coach!\n\nTell me, what are you working on today? I'll guide you through focused 25-minute sessions! 🍅",
        "agent": "orchestrator",
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                text = sanitize_user_input(payload.get("message", ""))
            except (json.JSONDecodeError, KeyError):
                text = sanitize_user_input(data)

            if not text:
                continue

            # Echo user message back
            await websocket.send_json({
                "type": "user_message",
                "content": text,
            })

            # Typing indicator
            await websocket.send_json({"type": "typing", "agent": "Coach Novora"})

            # Get agent response
            agent_text = await _get_agent_response(user_id, text)

            # Stream words for a natural feel
            words = agent_text.split(" ")
            accumulated = ""
            for i, word in enumerate(words):
                accumulated += ("" if i == 0 else " ") + word
                if i % 5 == 4 or i == len(words) - 1:
                    await websocket.send_json({
                        "type": "agent_stream",
                        "content": accumulated,
                        "done": i == len(words) - 1,
                        "agent": "Coach Novora",
                    })
                    await asyncio.sleep(0.03)

    except WebSocketDisconnect:
        _connections.pop(user_id, None)
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})
        _connections.pop(user_id, None)


async def broadcast_timer_event(user_id: str, event_type: str, payload: dict):
    """Send timer events to the user's WebSocket connection."""
    ws = _connections.get(user_id)
    if ws:
        try:
            await ws.send_json({"type": event_type, **payload})
        except Exception:
            _connections.pop(user_id, None)
