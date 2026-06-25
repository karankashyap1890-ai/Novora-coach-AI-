"""
Novora — Offline Multi-Agent Framework
=======================================
A lightweight, self-contained agent orchestration system that runs
100% locally — no API keys, no internet connection required.

Architecture:
  - AgentMessage: typed message passed between agents
  - BaseAgent: abstract agent with a process() method
  - AgentBus: in-process message bus for agent-to-agent communication
  - OrchestratorAgent: routes messages to the correct sub-agent
"""
from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# ─────────────────────────────────────────────
# Message Types
# ─────────────────────────────────────────────

class MessageType(str, Enum):
    USER_CHAT     = "user_chat"
    START_TIMER   = "start_timer"
    PAUSE_TIMER   = "pause_timer"
    RESUME_TIMER  = "resume_timer"
    TIMER_DONE    = "timer_done"
    BREAK_DONE    = "break_done"
    REFLECT       = "reflect"
    ENCOURAGE     = "encourage"
    ANALYTICS     = "analytics"
    STATUS        = "status"
    AGENT_REPLY   = "agent_reply"
    ERROR         = "error"


@dataclass
class AgentMessage:
    type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    sender: str = "user"
    recipient: str = "orchestrator"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ─────────────────────────────────────────────
# Agent Bus (in-process pub/sub)
# ─────────────────────────────────────────────

class AgentBus:
    """Simple in-process message bus — no external broker needed."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[AgentMessage] = []

    def register(self, agent_name: str, handler: Callable):
        self._handlers.setdefault(agent_name, []).append(handler)

    async def send(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Route a message to the target agent and return its response."""
        self._history.append(message)
        handlers = self._handlers.get(message.recipient, [])
        if not handlers:
            return AgentMessage(
                type=MessageType.ERROR,
                payload={"error": f"No agent registered for '{message.recipient}'"},
                sender="bus",
                recipient=message.sender,
            )
        # Call the first registered handler (one agent per name)
        response = await handlers[0](message)
        if response:
            self._history.append(response)
        return response

    def get_history(self, limit: int = 50) -> List[dict]:
        return [
            {"type": m.type, "sender": m.sender, "payload": m.payload}
            for m in self._history[-limit:]
        ]


# ─────────────────────────────────────────────
# Base Agent
# ─────────────────────────────────────────────

class BaseAgent(ABC):
    """All Novora agents inherit from this base class."""

    def __init__(self, name: str, bus: AgentBus):
        self.name = name
        self.bus = bus
        bus.register(name, self.handle)

    async def handle(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Entry point — subclasses should call process()."""
        try:
            return await self.process(message)
        except Exception as exc:
            return AgentMessage(
                type=MessageType.ERROR,
                payload={"error": str(exc), "agent": self.name},
                sender=self.name,
                recipient=message.sender,
            )

    @abstractmethod
    async def process(self, message: AgentMessage) -> Optional[AgentMessage]:
        ...

    def reply(self, original: AgentMessage, content: str, extra: dict = None) -> AgentMessage:
        payload = {"content": content, "agent": self.name}
        if extra:
            payload.update(extra)
        return AgentMessage(
            type=MessageType.AGENT_REPLY,
            payload=payload,
            sender=self.name,
            recipient=original.sender,
        )


# ─────────────────────────────────────────────
# Global bus singleton
# ─────────────────────────────────────────────
_bus = AgentBus()


def get_bus() -> AgentBus:
    return _bus
