"""
Novora — ReflectionAgent
Guides users through post-session reflection with adaptive questions.
Runs 100% offline using the ReflectionSkill.
"""
from agents import BaseAgent, AgentBus, AgentMessage, MessageType
from skills.reflection_skill import reflection_skill
from skills.pomodoro_skill import pomodoro_skill


class ReflectionAgent(BaseAgent):
    """
    Responsible for:
    - Prompting structured reflection after each work session
    - Interpreting user focus scores
    - Generating personalized post-session summaries
    - Advising on focus improvement strategies
    """

    # Offline NLP: keyword → advice mapping
    KEYWORD_ADVICE = {
        "distract": "📵 Try putting your phone in another room during the next session.",
        "tired":    "😴 A short walk or some water might help. Are you getting enough sleep?",
        "focus":    "🎯 Great awareness! Try the '2-minute rule': if a thought pops up, write it down and return to it after the session.",
        "slow":     "🐢 Slow progress is still progress! Every session counts.",
        "hard":     "💪 Challenging tasks build the most resilience. You're growing!",
        "good":     "🌟 Excellent! Ride that momentum into the next session.",
        "great":    "🔥 You're on fire! Keep that energy going.",
        "interrupt": "🚫 Try using 'Do Not Disturb' mode to block interruptions next time.",
        "bored":    "🎮 If it's boring, try making it a game — beat your own speed record!",
        "stress":   "🧘 Take a deep breath. Remember: one Pomodoro at a time.",
    }

    def __init__(self, bus: AgentBus):
        super().__init__("reflection", bus)

    async def process(self, message: AgentMessage) -> AgentMessage:
        user_id = message.payload.get("user_id", "default")
        mtype = message.type

        if mtype == MessageType.REFLECT:
            state = pomodoro_skill.get_status(user_id)
            session_num = state.get("session_number", 1)
            task_title = state.get("task_title", "your task")
            focus_score = message.payload.get("focus_score")

            content = reflection_skill.get_reflection_prompts(
                session_num, task_title, focus_score
            )
            return self.reply(message, content, {"session_number": session_num})

        elif mtype == MessageType.USER_CHAT:
            # User has responded to reflection — give adaptive feedback
            user_text = message.payload.get("text", "").lower()
            focus_score = message.payload.get("focus_score")
            advice = self._generate_advice(user_text, focus_score)
            return self.reply(message, advice)

        return self.reply(
            message,
            "🤔 How are you feeling about your progress today? I'm here to help you reflect."
        )

    def _generate_advice(self, user_text: str, focus_score: float = None) -> str:
        lines = []

        # Score-based feedback
        if focus_score is not None:
            label = reflection_skill.interpret_score(focus_score)
            lines.append(f"**Focus Score:** {focus_score:.1f}/5 — {label}")
            lines.append("")

        # Keyword-based advice
        matched_advice = []
        for keyword, advice in self.KEYWORD_ADVICE.items():
            if keyword in user_text:
                matched_advice.append(advice)

        if matched_advice:
            lines.append("**💡 Personalized Tips:**")
            lines.extend(matched_advice[:2])  # Max 2 tips at a time
        else:
            lines.append("Thank you for sharing! Your reflection helps build self-awareness — that's a superpower for productivity. 🌱")

        lines.extend([
            "",
            "Ready to start your next session? Just say the word! 🚀"
        ])

        return "\n".join(lines)
