# 🍅 Novora — Offline AI Pomodoro Coaching System

<div align="center">

![Novora Banner](https://img.shields.io/badge/Novora-AI%20Pomodoro%20Coach-7c3aed?style=for-the-badge&logo=timer&logoColor=white)
![Offline](https://img.shields.io/badge/Mode-100%25%20Offline-10b981?style=for-the-badge)
![No API Key](https://img.shields.io/badge/API%20Key-Not%20Required-06b6d4?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)

**A full-stack AI agent Pomodoro coaching system that runs 100% locally — no API keys, no internet required.**

*Built with an offline multi-agent architecture, MCP server, JWT security, and a stunning glassmorphism UI.*

</div>

---

## 🌟 What is Novora?

Novora is **Coach Novora** — a warm and encouraging AI productivity mentor that guides you through the Pomodoro technique. It asks what you're working on, runs 25-minute focus sessions with 5-minute breaks, provides motivational encouragement, and asks for your reflection after each session.

Unlike typical AI tools, Novora runs **entirely on your machine** with no external dependencies — just start the server and go.

---

## 🏗️ Architecture: 4 Key Concepts

### 1. 🤖 ADK Multi-Agent System (Offline)

```
OrchestratorAgent (Coach Novora — root)
├── TimerAgent          → Manages Pomodoro state machine
├── EncouragementAgent  → Motivational messages & streak detection  
├── ReflectionAgent     → Post-session reflection + keyword NLP
└── AnalyticsAgent      → Statistics, streaks, 7-day trends
```

All agents communicate via an **in-process AgentBus** (typed message passing — no external broker). Intent detection uses regex-based NLP, so it works completely offline.

### 2. 🔌 MCP Server (FastMCP)

A local Model Context Protocol server exposes structured tools:

| Tool | Description |
|------|-------------|
| `start_timer` | Begin a Pomodoro work session |
| `pause_timer` | Pause the current session |
| `resume_timer` | Resume a paused session |
| `get_timer_status` | Get remaining time & state |
| `complete_work_session` | Mark complete & start break |
| `log_session` | Record session to store |
| `get_sessions` | Retrieve session history |
| `get_analytics_summary` | Compute productivity stats |
| `get_daily_trend` | 7-day session counts |

### 3. 🔒 Security (Multi-Layer)

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT tokens (python-jose + bcrypt) |
| **Input Validation** | Pydantic v2 strict models with custom validators |
| **Rate Limiting** | Sliding-window limiter (60 req/min/user) |
| **Safe Execution** | bleach HTML sanitizer + prompt-injection detector |
| **XSS Prevention** | All agent outputs sanitized before display |

### 4. 🛠️ Agent Skills & CLI

**Skills** (reusable modules used by agents):
- `PomodoroSkill` — State machine (IDLE → WORK → BREAK → LONG_BREAK)
- `EncouragementSkill` — 40+ curated motivational messages per moment
- `ReflectionSkill` — Adaptive reflection questions + focus score interpretation

**CLI** (powered by Click + Rich):
```bash
novora login           # Authenticate
novora start "task"    # Start a session with TUI countdown
novora status          # Check current timer
novora stats           # View productivity stats
novora info            # System information
```

---

## 📂 Project Structure

```
novora/
├── .env.example                   # Config template (no secrets!)
├── .gitignore
├── README.md
│
├── backend/
│   ├── pyproject.toml             # Python deps (uv/pip)
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings (pydantic-settings)
│   │
│   ├── agents/                    # 🤖 Multi-Agent System
│   │   ├── __init__.py            # AgentBus + BaseAgent framework
│   │   ├── orchestrator.py        # Coach Novora (root agent)
│   │   ├── timer_agent.py         # Pomodoro state + countdown tasks
│   │   ├── encouragement_agent.py # Motivational responses
│   │   ├── reflection_agent.py    # Post-session reflection NLP
│   │   └── analytics_agent.py     # Stats computation
│   │
│   ├── mcp_server/                # 🔌 MCP Server
│   │   ├── server.py              # FastMCP app
│   │   └── tools/
│   │       ├── timer_tools.py
│   │       ├── session_tools.py
│   │       └── analytics_tools.py
│   │
│   ├── skills/                    # 🧠 Reusable Agent Skills
│   │   ├── pomodoro_skill.py      # State machine
│   │   ├── encouragement_skill.py # Message bank (40+ messages)
│   │   └── reflection_skill.py    # Reflection prompts
│   │
│   ├── security/                  # 🔒 Security Layer
│   │   ├── auth.py                # JWT + bcrypt
│   │   ├── validators.py          # Pydantic v2 validators
│   │   ├── rate_limiter.py        # Sliding window
│   │   └── sandbox.py             # bleach + injection detection
│   │
│   ├── db/
│   │   ├── models.py              # SQLAlchemy ORM
│   │   └── session.py             # Async session factory
│   │
│   ├── api/routes/
│   │   ├── auth.py                # /auth/register, /auth/login
│   │   ├── chat.py                # /chat/message, /chat/ws/{id}
│   │   ├── sessions.py            # /sessions CRUD
│   │   └── analytics.py           # /analytics/summary, /trend
│   │
│   ├── cli/
│   │   └── novora_cli.py          # Click CLI with Rich TUI
│   │
│   └── tests/
│       └── test_novora.py         # 20+ test cases
│
└── frontend/
    ├── package.json               # React 18 + Vite
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                # Root layout (3-column grid)
        ├── index.css              # Design system (glassmorphism)
        └── components/
            ├── Auth/              # Login + Register
            ├── PomodoroTimer/     # Animated SVG ring timer
            ├── ChatPanel/         # WebSocket chat + streaming
            └── Analytics/         # Stats + 7-day bar chart
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- `uv` (recommended) or `pip`

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/novora.git
cd novora

# Copy environment config (no edits needed for local dev!)
cp .env.example backend/.env
```

### 2. Install Backend Dependencies

```bash
cd backend

# With uv (recommended — fast):
pip install uv
uv sync

# OR with pip:
pip install -e ".[dev]"
```

### 3. Start the Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

You'll see:
```
🚀 Novora starting up...
✅ Database initialized
🤖 Multi-agent system initialized (5 agents online)
   • OrchestratorAgent (Coach Novora)
   • TimerAgent
   • EncouragementAgent
   • ReflectionAgent
   • AnalyticsAgent
✅ Novora is ready! Visit http://localhost:3000
```

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** 🎉

### 5. (Optional) Use the CLI

```bash
cd backend
uv run python -m cli.novora_cli login
uv run python -m cli.novora_cli start "Write my project report"
uv run python -m cli.novora_cli status
uv run python -m cli.novora_cli stats
```

### 6. (Optional) Run the MCP Server

```bash
cd backend
uv run python -m mcp_server.server
```

---

## 🎮 End-to-End Usage

1. **Open** http://localhost:3000
2. **Register** a new account (or login)
3. **Tell Coach Novora** what you're working on: *"Start — writing my report"*
4. The **25-minute timer** starts with an animated ring
5. Coach Novora sends **real-time encouragement** via WebSocket
6. When the timer completes, a **break starts automatically**
7. After the break, Novora asks for your **reflection** (focus score 1–5)
8. After 4 sessions, you earn a **long break** (15 minutes)
9. View your **Analytics** panel for streaks, focus scores, and trends

---

## 🧪 Running Tests

```bash
cd backend
uv run pytest tests/ -v --tb=short
```

Expected output:
```
PASSED tests/test_novora.py::TestValidators::test_valid_register
PASSED tests/test_novora.py::TestSandbox::test_block_injection
PASSED tests/test_novora.py::TestAuth::test_jwt_roundtrip
PASSED tests/test_novora.py::TestPomodoroSkill::test_session_4_gives_long_break
PASSED tests/test_novora.py::TestAgentSystem::test_greeting_response
... (20+ tests)
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Get a JWT token |
| `GET` | `/auth/me` | Get current user |
| `POST` | `/chat/message` | Send a chat message |
| `WS` | `/chat/ws/{user_id}` | Real-time WebSocket chat |
| `GET` | `/chat/history` | Chat message history |
| `POST` | `/sessions/start` | Start a Pomodoro session |
| `PATCH` | `/sessions/{id}/complete` | Complete + rate a session |
| `GET` | `/sessions/` | List all sessions |
| `GET` | `/sessions/status` | Live timer status |
| `GET` | `/analytics/summary` | Productivity summary |
| `GET` | `/analytics/trend` | 7-day trend data |
| `GET` | `/health` | System health check |

Interactive API docs: **http://localhost:8000/docs**

---

## 🛡️ Security Details

```
Input Validation  →  Pydantic v2 strict models
                     - Username: alphanumeric only, 3-50 chars
                     - Password: 8+ chars, must contain digit + letter
                     - Task titles: no HTML/JS special chars

Rate Limiting     →  60 requests/minute/user (sliding window)
                     Returns 429 with Retry-After header

JWT Security      →  HS256 signing, 24h expiry
                     Token type validation (prevents refresh→access swap)

Sandbox           →  bleach HTML stripping on all agent outputs
                     Regex detection for 8 prompt-injection patterns
                     All XSS vectors blocked before client display
```

---

## 🤖 How the Agent System Works (Offline NLP)

The OrchestratorAgent detects user intent via regex patterns:

| User says… | Detected intent | Routes to |
|-----------|-----------------|-----------|
| *"Let's start! Focus on coding"* | `start` | TimerAgent + EncouragementAgent |
| *"Pause"* | `pause` | TimerAgent |
| *"How much time left?"* | `status` | TimerAgent |
| *"I'm done, score 4"* | `reflect` | ReflectionAgent |
| *"Show my stats"* | `analytics` | AnalyticsAgent |
| *"Hello"* | `greeting` | OrchestratorAgent (direct) |
| *"Help"* | `help` | OrchestratorAgent (direct) |

The ReflectionAgent also performs **keyword matching** on user responses:
- *"distracted"* → tip about phone-free working
- *"tired"* → sleep/hydration advice
- *"great"* → riding the momentum message

---

## 📊 Pomodoro Technique

| Phase | Duration | After |
|-------|----------|-------|
| 🔴 Work | 25 min | → Short Break |
| 🟢 Short Break | 5 min | → Work |
| 🔵 Long Break | 15 min | Every 4 sessions |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run the test suite: `uv run pytest tests/ -v`
5. Submit a pull request

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ using FastAPI · React · FastMCP · SQLite · Click · Rich<br>
<strong>100% Offline · No API Keys · No Internet Required</strong>
</div>
#   N o v o r a - c o a c h - A I -  
 