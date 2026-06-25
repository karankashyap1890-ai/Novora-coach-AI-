"""
Novora — Agent Skills: Reflection
Guides users through end-of-session reflection with structured prompts.
"""
from typing import Optional


REFLECTION_QUESTIONS = {
    1: [
        "What was your main accomplishment in this session?",
        "Did you stay focused the entire time, or did you notice any distractions?",
        "Is there anything you'd like to do differently in the next session?",
    ],
    2: [
        "How energized do you feel right now compared to when you started?",
        "What's one thing that made this session productive?",
        "What's your next priority after the break?",
    ],
    3: [
        "You've done {session_number} sessions! How's your momentum feeling?",
        "Are you still working toward your original goal, or has it evolved?",
        "What's keeping you motivated today?",
    ],
    4: [
        "Four sessions! That's impressive dedication. How do you feel overall?",
        "What's the biggest thing you've accomplished so far today?",
        "You deserve this long break — what will you do to truly recharge?",
    ],
}


class ReflectionSkill:
    """
    Generates structured reflection prompts after each Pomodoro session.
    Adapts questions based on session number and focus score.
    """

    def get_reflection_prompts(
        self,
        session_number: int,
        task_title: str,
        focus_score: Optional[float] = None,
    ) -> str:
        # Pick question set (cycle through 4 templates)
        question_set = REFLECTION_QUESTIONS.get(
            ((session_number - 1) % 4) + 1, REFLECTION_QUESTIONS[1]
        )
        questions = [q.format(session_number=session_number) for q in question_set]

        lines = [
            f"**📝 Session #{session_number} Reflection** — *{task_title}*",
            "",
        ]

        if focus_score is not None:
            if focus_score >= 4.5:
                lines.append("⭐ Your focus score is outstanding! What was your secret?")
            elif focus_score >= 3.0:
                lines.append("👍 Solid focus! Let's reflect on how to make the next one even better.")
            else:
                lines.append("💙 It was a tough one — that's okay! Reflection helps us improve.")
            lines.append("")

        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")

        lines.extend([
            "",
            "Take your time — even a few words of reflection make a big difference! 🌱",
        ])

        return "\n".join(lines)

    def interpret_score(self, score: float) -> str:
        if score >= 4.5:
            return "🌟 Elite focus!"
        elif score >= 3.5:
            return "✅ Great session"
        elif score >= 2.5:
            return "👍 Decent effort"
        elif score >= 1.5:
            return "💙 Challenging but you showed up"
        else:
            return "🌱 Learning experience"


# Global singleton
reflection_skill = ReflectionSkill()
