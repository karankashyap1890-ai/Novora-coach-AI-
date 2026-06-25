"""
Novora — OrchestratorAgent
The root "Coach Novora" agent. Understands user intent via keyword
pattern matching and routes to the appropriate sub-agent.
Runs 100% offline — no LLM, no API key required.
"""
import re
from typing import Optional

from agents import BaseAgent, AgentBus, AgentMessage, MessageType
from skills.pomodoro_skill import pomodoro_skill
from skills.encouragement_skill import encouragement_skill, EncouragementMoment


# ─────────────────────────────────────────────
# Intent Detection (offline NLP via regex)
# ─────────────────────────────────────────────

INTENT_PATTERNS = {
    "start": re.compile(
        r"\b(start|begin|go|let'?s go|kick off|launch|ready|let me|i want to work on|focus on)\b",
        re.IGNORECASE,
    ),
    "pause": re.compile(
        r"\b(pause|hold|wait|stop|freeze|take a break early)\b",
        re.IGNORECASE,
    ),
    "resume": re.compile(
        r"\b(resume|continue|unpause|restart|back|ready again|let'?s go again)\b",
        re.IGNORECASE,
    ),
    "status": re.compile(
        r"\b(status|how (long|much|many)|time left|remaining|progress|where am i)\b",
        re.IGNORECASE,
    ),
    "reflect": re.compile(
        r"\b(reflect|done|finished|completed|session over|how did i do|rate|score)\b",
        re.IGNORECASE,
    ),
    "analytics": re.compile(
        r"\b(stats|statistics|analytics|history|trend|streak|total|how many sessions)\b",
        re.IGNORECASE,
    ),
    "help": re.compile(
        r"\b(help|what can you do|how does this work|explain|guide|tutorial)\b",
        re.IGNORECASE,
    ),
    "greeting": re.compile(
        r"\b(hello|hi|hey|good morning|good evening|howdy|what'?s up)\b",
        re.IGNORECASE,
    ),
}

TASK_EXTRACT_RE = re.compile(
    r"(?:work(?:ing)? on|focus(?:ing)? on|task[:\s]+|doing|tackle|start)\s+[\"']?(.+?)[\"']?(?:\s+for\s+\d+|$)",
    re.IGNORECASE,
)


class OrchestratorAgent(BaseAgent):
    """
    Coach Novora — the warm, encouraging root agent.
    Routes user messages to specialized sub-agents and
    synthesizes their responses into a cohesive reply.
    """

    HELP_TEXT = """👋 **I'm Coach Novora — your personal Pomodoro productivity coach!**

Here's what I can help you with:

🍅 **Starting a Session**
> *"Let's start! I'm working on my report"*
> *"Focus on Python homework for 25 minutes"*

⏸️ **Pausing / Resuming**
> *"Pause"* — *"Resume"*

📊 **Checking Status**
> *"How much time is left?"*
> *"What's my status?"*

📝 **Reflecting After a Session**
> *"I'm done, my score is 4"*
> *"Session complete, I got distracted a bit"*

📈 **Viewing Your Stats**
> *"Show me my stats"*
> *"What's my streak?"*

💡 **Tips for best results:**
- Use 25-minute sessions for deep work
- Take breaks seriously — they make the next session better
- Rate your focus honestly to get better insights

Ready to start? Tell me what you're working on! 🚀"""

    GREETING_RESPONSES = [
        "👋 Hey there! Great to see you! Ready to have a productive session? What are you working on today?",
        "🌟 Hello! Coach Novora at your service! Tell me — what task shall we tackle together today?",
        "😊 Hi! I'm so glad you're here. Let's make today incredibly productive! What's on your to-do list?",
        "🚀 Welcome back! Ready to focus? Tell me what you're working on and let's get started!",
    ]

    def __init__(self, bus: AgentBus):
        super().__init__("orchestrator", bus)
        self._greeting_idx = 0

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Main routing logic:
        1. Detect intent from user message
        2. Build a sub-agent message and send via bus
        3. Combine sub-agent response with encouragement if needed
        """
        user_id = message.payload.get("user_id", "default")
        text = message.payload.get("text", "")

        # Handle internal lifecycle events from TimerAgent
        if message.type == MessageType.TIMER_DONE:
            return await self._handle_timer_done(message, user_id)
        if message.type == MessageType.BREAK_DONE:
            return await self._handle_break_done(message, user_id)

        # Detect intent
        intent = self._detect_intent(text)

        if intent == "greeting":
            return self._greeting_reply(message)

        if intent == "help":
            return self.reply(message, self.HELP_TEXT)

        if intent == "start":
            return await self._handle_start(message, user_id, text)

        if intent == "pause":
            sub_msg = AgentMessage(
                type=MessageType.PAUSE_TIMER,
                payload={"user_id": user_id},
                sender="orchestrator", recipient="timer",
            )
            timer_resp = await self.bus.send(sub_msg)
            content = (timer_resp.payload.get("content", "Timer paused.") if timer_resp else "Timer paused.")
            return self.reply(message, content, timer_resp.payload if timer_resp else {})

        if intent == "resume":
            sub_msg = AgentMessage(
                type=MessageType.RESUME_TIMER,
                payload={"user_id": user_id},
                sender="orchestrator", recipient="timer",
            )
            timer_resp = await self.bus.send(sub_msg)
            enc_msg = self.get_message(EncouragementMoment.BREAK_END)
            content = f"{timer_resp.payload.get('content', '')}\n\n{enc_msg}" if timer_resp else enc_msg
            return self.reply(message, content)

        if intent == "status":
            sub_msg = AgentMessage(
                type=MessageType.STATUS,
                payload={"user_id": user_id},
                sender="orchestrator", recipient="timer",
            )
            resp = await self.bus.send(sub_msg)
            state = resp.payload.get("state", {}) if resp else {}
            return self.reply(message, self._format_status(state), {"state": state})

        if intent == "reflect":
            score = self._extract_score(text)
            sub_msg = AgentMessage(
                type=MessageType.REFLECT,
                payload={"user_id": user_id, "focus_score": score},
                sender="orchestrator", recipient="reflection",
            )
            resp = await self.bus.send(sub_msg)
            content = resp.payload.get("content", "Great work reflecting!") if resp else "Great work reflecting!"
            return self.reply(message, content)

        if intent == "analytics":
            # Delegate to analytics — sessions are passed from the API layer
            sessions = message.payload.get("sessions", [])
            sub_msg = AgentMessage(
                type=MessageType.ANALYTICS,
                payload={"user_id": user_id, "sessions": sessions, "sub_type": "summary"},
                sender="orchestrator", recipient="analytics",
            )
            resp = await self.bus.send(sub_msg)
            content = resp.payload.get("content", "") if resp else ""
            return self.reply(message, content)

        # Default: treat as general chat — context-aware response
        return await self._handle_general_chat(message, user_id, text)

    # ─── Private helpers ───

    def _detect_intent(self, text: str) -> Optional[str]:
        for intent, pattern in INTENT_PATTERNS.items():
            if pattern.search(text):
                return intent
        return "general"

    def _extract_task(self, text: str) -> str:
        m = TASK_EXTRACT_RE.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
        # Fallback: take the text after common triggers
        for trigger in ["on ", "doing ", "tackle ", "start "]:
            idx = text.lower().find(trigger)
            if idx != -1:
                candidate = text[idx + len(trigger):].strip()
                if 2 < len(candidate) < 150:
                    return candidate.rstrip(".")
        return "My Task"

    def _extract_score(self, text: str) -> Optional[float]:
        m = re.search(r"\b([1-5](?:\.\d)?)\b", text)
        if m:
            val = float(m.group(1))
            if 1.0 <= val <= 5.0:
                return val
        return None

    def _format_status(self, state: dict) -> str:
        if not state:
            return "No active session. Ready to start one? Tell me what you're working on! 🚀"
        remaining = state.get("remaining_seconds", 0)
        mins, secs = divmod(remaining, 60)
        s_state = state.get("state", "idle")
        task = state.get("task_title", "your task")
        session = state.get("session_number", 0)

        if s_state == "work":
            return (
                f"⏱️ **Session #{session}** — Working on *{task}*\n"
                f"⏰ **{mins:02d}:{secs:02d}** remaining\n"
                f"💪 Stay focused — you're doing great!"
            )
        elif s_state in ("short_break", "long_break"):
            label = "Short break" if s_state == "short_break" else "Long break 🎉"
            return (
                f"☕ **{label}** in progress\n"
                f"⏰ **{mins:02d}:{secs:02d}** remaining\n"
                f"🌿 Relax — you earned this!"
            )
        elif s_state == "paused":
            return f"⏸️ **Paused** — Session #{session} on *{task}*. Say 'resume' when ready!"
        else:
            return "📭 No active session. What would you like to focus on? 🚀"

    def _greeting_reply(self, message: AgentMessage) -> AgentMessage:
        import random
        content = random.choice(self.GREETING_RESPONSES)
        return self.reply(message, content)

    def get_message(self, moment: EncouragementMoment) -> str:
        return encouragement_skill.get_message(moment)

    async def _handle_start(self, message: AgentMessage, user_id: str, text: str) -> AgentMessage:
        task_title = self._extract_task(text)
        # Confirmation prompt if no task extracted
        if task_title == "My Task" and len(text.split()) < 4:
            return self.reply(
                message,
                "🎯 Let's do this! What task are you focusing on? "
                "(e.g. *'Start — working on my project report'*)"
            )
        # Send START to timer agent
        sub_msg = AgentMessage(
            type=MessageType.START_TIMER,
            payload={"user_id": user_id, "task_title": task_title, "work_minutes": 25},
            sender="orchestrator", recipient="timer",
        )
        timer_resp = await self.bus.send(sub_msg)
        # Get encouragement
        enc_content = encouragement_skill.get_session_start_message(task_title)
        state = timer_resp.payload.get("state", {}) if timer_resp else {}
        return self.reply(message, enc_content, {"state": state, "task_title": task_title})

    async def _handle_timer_done(self, message: AgentMessage, user_id: str) -> AgentMessage:
        # Get encouragement for session complete
        state = pomodoro_skill.get_status(user_id)
        session_num = state.get("session_number", 1)
        task_title = state.get("task_title", "your task")
        enc = encouragement_skill.get_session_complete_message(session_num, task_title)
        # Trigger reflection
        reflect_msg = AgentMessage(
            type=MessageType.REFLECT,
            payload={"user_id": user_id},
            sender="orchestrator", recipient="reflection",
        )
        reflect_resp = await self.bus.send(reflect_msg)
        reflect_content = reflect_resp.payload.get("content", "") if reflect_resp else ""
        full_content = f"{enc}\n\n---\n\n{reflect_content}"
        return self.reply(message, full_content)

    async def _handle_break_done(self, message: AgentMessage, user_id: str) -> AgentMessage:
        enc = encouragement_skill.get_message(EncouragementMoment.BREAK_END)
        content = f"{enc}\n\n🍅 Ready to start your next session? Just say 'start' and tell me what you're working on!"
        return self.reply(message, content)

    async def _handle_general_chat(self, message: AgentMessage, user_id: str, text: str) -> AgentMessage:
        """Handles messages that don't match any specific intent."""
        state = pomodoro_skill.get_status(user_id)
        current_state = state.get("state", "idle")

        # Context-aware fallback responses
        if current_state == "work":
            return self.reply(
                message,
                "💪 Stay focused on your task! If you need to pause, just say 'pause'. "
                "You're doing great — keep going! 🔥"
            )
        elif current_state in ("short_break", "long_break"):
            return self.reply(
                message,
                "☕ Enjoy your break! When you're ready to start the next session, "
                "just say 'start' followed by your task. 🌿"
            )
        else:
            return self.reply(
                message,
                "😊 I'm here to help you stay productive! Tell me what you'd like to work on, "
                "or type 'help' to see everything I can do. What's on your plate today? 🚀"
            )
