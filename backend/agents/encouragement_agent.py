"""
Novora — EncouragementAgent
Generates warm, contextual motivational messages at every Pomodoro milestone.
Runs 100% offline using the EncouragementSkill.
"""
from agents import BaseAgent, AgentBus, AgentMessage, MessageType
from skills.encouragement_skill import encouragement_skill, EncouragementMoment
from skills.pomodoro_skill import pomodoro_skill


class EncouragementAgent(BaseAgent):
    """
    Responsible for:
    - Injecting motivational messages at key moments
    - Detecting streaks and celebrating milestones
    - Maintaining the warm, coaching tone of Novora
    """

    def __init__(self, bus: AgentBus):
        super().__init__("encouragement", bus)

    async def process(self, message: AgentMessage) -> AgentMessage:
        user_id = message.payload.get("user_id", "default")
        mtype = message.type
        state = pomodoro_skill.get_status(user_id)
        session_num = state.get("session_number", 1)
        task_title = state.get("task_title", "your task")

        if mtype == MessageType.START_TIMER:
            content = encouragement_skill.get_session_start_message(task_title)
            return self.reply(message, content)

        elif mtype == MessageType.TIMER_DONE:
            content = encouragement_skill.get_session_complete_message(session_num, task_title)
            # Celebrate streaks at multiples of 4
            if session_num > 0 and session_num % 4 == 0:
                content += f"\n\n{encouragement_skill.get_message(EncouragementMoment.STREAK, count=session_num)}"
            return self.reply(message, content, {"session_number": session_num})

        elif mtype == MessageType.BREAK_DONE:
            content = encouragement_skill.get_message(EncouragementMoment.BREAK_END)
            return self.reply(message, content)

        elif mtype == MessageType.ENCOURAGE:
            sub_type = message.payload.get("sub_type", "session_start")
            try:
                moment = EncouragementMoment(sub_type)
            except ValueError:
                moment = EncouragementMoment.SESSION_START
            content = encouragement_skill.get_message(moment)
            return self.reply(message, content)

        return self.reply(message, "Keep going — you're doing amazing! 💪")
