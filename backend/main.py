"""
Novora — FastAPI Entry Point
Bootstraps the entire application: DB, agents, routes, middleware.
"""
import asyncio
import sys
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from db.session import init_db
from agents import get_bus
from agents.orchestrator import OrchestratorAgent
from agents.timer_agent import TimerAgent
from agents.encouragement_agent import EncouragementAgent
from agents.reflection_agent import ReflectionAgent
from agents.analytics_agent import AnalyticsAgent
from api.routes import auth, chat, sessions, analytics
from security.rate_limiter import check_rate_limit

settings = get_settings()

# ─────────────────────────────────────────────
# Application Factory
# ─────────────────────────────────────────────

app = FastAPI(
    title="Novora API",
    description="Offline AI-powered Pomodoro coaching system — no API keys required",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Global Error Handler
# ─────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again.", "type": type(exc).__name__},
    )

# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(analytics.router)

# ─────────────────────────────────────────────
# Startup: Initialize DB + Spin up Agents
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    print("🚀 Novora starting up...")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Register all agents on the shared bus
    bus = get_bus()
    OrchestratorAgent(bus)
    TimerAgent(bus)
    EncouragementAgent(bus)
    ReflectionAgent(bus)
    AnalyticsAgent(bus)
    print("🤖 Multi-agent system initialized (5 agents online)")
    print(f"   • OrchestratorAgent (Coach Novora)")
    print(f"   • TimerAgent")
    print(f"   • EncouragementAgent")
    print(f"   • ReflectionAgent")
    print(f"   • AnalyticsAgent")
    print("✅ Novora is ready! Visit http://localhost:3000")


@app.on_event("shutdown")
async def shutdown():
    print("👋 Novora shutting down gracefully...")


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
        "mode": "offline",
        "agents": ["orchestrator", "timer", "encouragement", "reflection", "analytics"],
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Novora API 🍅",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
        log_level="info",
    )
