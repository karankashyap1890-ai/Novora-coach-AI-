"""
Novora — Agent Skills: Encouragement
Provides motivational messages and coaching tone for different moments.
"""
import random
from enum import Enum


class EncouragementMoment(str, Enum):
    SESSION_START = "session_start"
    SESSION_COMPLETE = "session_complete"
    BREAK_START = "break_start"
    BREAK_END = "break_end"
    HALFWAY = "halfway"
    STRUGGLING = "struggling"
    STREAK = "streak"
    LONG_BREAK = "long_break"


ENCOURAGEMENT_BANK = {
    EncouragementMoment.SESSION_START: [
        "🚀 Let's do this! Your focus starts NOW. I believe in you!",
        "💪 25 minutes of pure focus — you've got this! Let's make it count.",
        "🌟 Every great achievement begins with a single focused session. Let's go!",
        "🔥 Time to shine! Block out distractions — it's YOUR time to focus.",
        "✨ Ready, set, focus! I'll be right here cheering you on.",
    ],
    EncouragementMoment.SESSION_COMPLETE: [
        "🎉 Fantastic work! You crushed that session! Take a well-deserved break.",
        "⭐ Incredible focus! One more Pomodoro done — you're building momentum!",
        "🙌 YES! That's how it's done! Rest up and come back stronger.",
        "🏆 You completed a full session! That's real discipline. So proud of you!",
        "✅ DONE! Look at you go — another step closer to your goal!",
    ],
    EncouragementMoment.BREAK_START: [
        "☕ Break time! Step away from the screen, stretch, hydrate. You earned it!",
        "🌿 Rest is part of the process. Take 5 and recharge your amazing brain.",
        "🎵 Break time! Do something that makes you smile — you deserve it.",
        "🧘 Breathe. You worked hard. This rest makes the next session even better.",
        "🌊 Let your mind float for a moment. You're doing phenomenally!",
    ],
    EncouragementMoment.BREAK_END: [
        "⚡ Break's over! Ready to build on that momentum? You're on fire!",
        "🌅 Welcome back! Time to continue your amazing work. Let's go!",
        "💡 Rested and ready? Your best ideas often come RIGHT after a break!",
        "🎯 Back to it! You're crushing your goals one session at a time.",
        "🚀 Round two! You've already proven you can focus — now do it again!",
    ],
    EncouragementMoment.HALFWAY: [
        "⏰ Halfway there! You're in the zone — keep that beautiful focus going!",
        "🌟 12 minutes down, 13 to go! You're doing incredible. Stay with it!",
        "💪 Past the halfway mark! This is where champions are made. Push through!",
    ],
    EncouragementMoment.STRUGGLING: [
        "💙 It's okay to find it hard. That's what makes it worth it. You can do this.",
        "🌱 Struggling is just growing in disguise. Take a breath and refocus.",
        "🤗 Hey, I notice you're having a tough moment. That's totally normal. Refocus on just the next 5 minutes.",
    ],
    EncouragementMoment.STREAK: [
        "🔥 Look at that STREAK! {count} sessions in a row — you're unstoppable!",
        "💥 {count} Pomodoros and counting! You're building an incredible habit!",
        "⭐ {count} sessions completed today! Your future self is going to thank you!",
    ],
    EncouragementMoment.LONG_BREAK: [
        "🎊 4 sessions done — you earned a long break! Take 15-20 minutes. You're amazing!",
        "🏖️ Long break time! This is a BIG deal. Reward yourself — you've worked hard!",
        "🎉 Wow! 4 full Pomodoros! Go for a walk, grab a snack, celebrate YOU!",
    ],
}


class EncouragementSkill:
    """
    Provides contextually appropriate encouragement messages.
    Used by the EncouragementAgent to inject warmth into the conversation.
    """

    def get_message(self, moment: EncouragementMoment, **kwargs) -> str:
        messages = ENCOURAGEMENT_BANK.get(moment, ["You're doing great! Keep going!"])
        message = random.choice(messages)
        return message.format(**kwargs)

    def get_session_start_message(self, task_title: str) -> str:
        base = self.get_message(EncouragementMoment.SESSION_START)
        return f"{base}\n\n🎯 **Task:** *{task_title}*\n\n⏱️ Your 25-minute focus session begins now. I'll check in with you when it's done!"

    def get_session_complete_message(self, session_number: int, task_title: str) -> str:
        base = self.get_message(EncouragementMoment.SESSION_COMPLETE)
        suffix = ""
        if session_number % 4 == 0:
            suffix = f"\n\n{self.get_message(EncouragementMoment.LONG_BREAK)}"
        else:
            suffix = f"\n\n{self.get_message(EncouragementMoment.BREAK_START)}"
        return f"{base}\n\n📊 **Session #{session_number}** on *{task_title}* complete!{suffix}"

    def get_reflection_prompt(self, session_number: int) -> str:
        prompts = [
            "🤔 How did that session feel? What did you accomplish?",
            "💭 Reflect for a moment — what went well in that session?",
            "📝 Quick check-in: How would you rate your focus from 1-5? Any distractions?",
        ]
        return random.choice(prompts)


# Global singleton
encouragement_skill = EncouragementSkill()
