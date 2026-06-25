"""
Novora — TimerAgent
Manages the Pomodoro state machine and triggers lifecycle events.
Runs 100% offline using the PomodoroSkill state machine.
"""
import asyncio
from agents import BaseAgent, AgentBus, AgentMessage, MessageType
from skills.pomodoro_skill import pomodoro_skill, PomodoroState


class TimerAgent(BaseAgent):
    """
    Responsible for:
    - Starting / pausing / resuming Pomodoro timers
    - Tracking elapsed time
    - Detecting session completion
    - Triggering TIMER_DONE / BREAK_DONE events on the bus
    """

    def __init__(self, bus: AgentBus):
        super().__init__("timer", bus)
        self._tasks: dict[str, asyncio.Task] = {}

    async def process(self, message: AgentMessage) -> AgentMessage:
        user_id = message.payload.get("user_id", "default")
        mtype = message.type

        if mtype == MessageType.START_TIMER:
            task_title = message.payload.get("task_title", "My Task")
            work_minutes = message.payload.get("work_minutes", 25)
            state = pomodoro_skill.start_session(user_id, task_title, work_minutes)
            self._schedule_countdown(user_id, state["remaining_seconds"], MessageType.TIMER_DONE)
            return self.reply(
                message,
                f"⏱️ Timer started! {work_minutes} minutes of focused work on '{task_title}'.",
                {"state": state},
            )

        elif mtype == MessageType.PAUSE_TIMER:
            self._cancel_countdown(user_id)
            state = pomodoro_skill.pause_session(user_id)
            return self.reply(message, "⏸️ Timer paused.", {"state": state})

        elif mtype == MessageType.RESUME_TIMER:
            state = pomodoro_skill.resume_session(user_id)
            self._schedule_countdown(user_id, state["remaining_seconds"], MessageType.TIMER_DONE)
            return self.reply(message, "▶️ Timer resumed! Keep going!", {"state": state})

        elif mtype == MessageType.STATUS:
            state = pomodoro_skill.get_status(user_id)
            return self.reply(message, "📊 Current timer status.", {"state": state})

        elif mtype == MessageType.TIMER_DONE:
            # Work session complete — start break countdown
            state = pomodoro_skill.complete_work_session(user_id)
            break_secs = state.get("remaining_seconds", 300)
            self._schedule_countdown(user_id, break_secs, MessageType.BREAK_DONE)
            return self.reply(
                message,
                "✅ Work session complete! Break started.",
                {"state": state},
            )

        elif mtype == MessageType.BREAK_DONE:
            state = pomodoro_skill.get_status(user_id)
            return self.reply(
                message,
                "☀️ Break over! Ready for the next session?",
                {"state": state},
            )

        return self.reply(message, "TimerAgent: unrecognized message type.")

    def _schedule_countdown(self, user_id: str, seconds: int, done_type: MessageType):
        """Start a background task that fires an event after `seconds`."""
        self._cancel_countdown(user_id)

        async def _countdown():
            await asyncio.sleep(seconds)
            done_msg = AgentMessage(
                type=done_type,
                payload={"user_id": user_id},
                sender="timer",
                recipient="orchestrator",
            )
            await self.bus.send(done_msg)

        self._tasks[user_id] = asyncio.create_task(_countdown())

    def _cancel_countdown(self, user_id: str):
        task = self._tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()
