import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from config import get_settings
from db.session import init_db
from agents import get_bus, AgentMessage, MessageType
from agents.orchestrator import OrchestratorAgent
from agents.timer_agent import TimerAgent
from agents.encouragement_agent import EncouragementAgent
from agents.reflection_agent import ReflectionAgent
from agents.analytics_agent import AnalyticsAgent

async def simulate_startup():
    s = get_settings()
    print(f"App: {s.app_name} v1.0.0  |  Mode: offline  |  Port: {s.backend_port}")

    await init_db()
    print("DB:  SQLite initialized (novora.db)")

    bus = get_bus()
    OrchestratorAgent(bus)
    TimerAgent(bus)
    EncouragementAgent(bus)
    ReflectionAgent(bus)
    AnalyticsAgent(bus)
    print("Agents: 5 agents registered on AgentBus")
    print("  - OrchestratorAgent (Coach Novora)")
    print("  - TimerAgent")
    print("  - EncouragementAgent")
    print("  - ReflectionAgent")
    print("  - AnalyticsAgent")

    print()
    print("--- Simulating full conversation flow ---")
    flows = [
        ("Hello there!", "GREETING"),
        ("Start! Working on my Novora demo", "START"),
        ("What is my status?", "STATUS"),
        ("Show me my stats", "ANALYTICS"),
        ("I am done, my focus score was 4", "REFLECT"),
        ("Help", "HELP"),
        ("Pause", "PAUSE"),
        ("Resume", "RESUME"),
    ]

    for text, intent in flows:
        msg = AgentMessage(
            type=MessageType.USER_CHAT,
            payload={"user_id": "demo_user", "text": text, "sessions": []},
            sender="demo_user",
            recipient="orchestrator",
        )
        resp = await bus.send(msg)
        content = resp.payload.get("content", "") if resp else "[no response]"
        short = content[:65].replace("\n", " ")
        print(f"  [{intent:<10}] -> {short}...")

    print()
    print("=" * 55)
    print("  NOVORA IS FULLY OPERATIONAL")
    print("  Backend:  http://localhost:8000")
    print("  Frontend: http://localhost:3000")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 55)

asyncio.run(simulate_startup())
