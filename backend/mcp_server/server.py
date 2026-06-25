"""
Novora — MCP Server
Exposes Pomodoro tools via the Model Context Protocol (FastMCP).
Runs locally on a separate port — no external services required.
"""
import asyncio
import sys
import os

# Make sure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastmcp import FastMCP
from mcp_server.tools.timer_tools import register_timer_tools
from mcp_server.tools.session_tools import register_session_tools
from mcp_server.tools.analytics_tools import register_analytics_tools
from config import get_settings

settings = get_settings()

# ─────────────────────────────────────────────
# Create the FastMCP application
# ─────────────────────────────────────────────

mcp = FastMCP(
    name="novora-mcp",
    version="1.0.0",
    description=(
        "Novora MCP Server — exposes Pomodoro timer management, session logging, "
        "and productivity analytics as structured MCP tools. "
        "Runs 100% locally, no internet required."
    ),
)

# Register all tool groups
register_timer_tools(mcp)
register_session_tools(mcp)
register_analytics_tools(mcp)


# ─────────────────────────────────────────────
# MCP Resource: Novora system info
# ─────────────────────────────────────────────

@mcp.resource("novora://system/info")
def get_system_info() -> dict:
    """Returns Novora system metadata and available tools."""
    return {
        "name": "Novora",
        "version": "1.0.0",
        "mode": "offline",
        "api_key_required": False,
        "tools": [
            "start_timer", "pause_timer", "resume_timer",
            "get_timer_status", "complete_work_session", "start_break",
            "log_session", "get_sessions", "get_session_by_id",
            "get_analytics_summary", "get_daily_trend",
        ],
    }


@mcp.resource("novora://pomodoro/defaults")
def get_pomodoro_defaults() -> dict:
    """Returns the default Pomodoro configuration."""
    return {
        "work_minutes": settings.work_minutes,
        "short_break_minutes": settings.short_break_minutes,
        "long_break_minutes": settings.long_break_minutes,
        "sessions_before_long_break": settings.sessions_before_long_break,
    }


if __name__ == "__main__":
    print(f"🔌 Starting Novora MCP Server on port {settings.mcp_port}...")
    mcp.run(transport="stdio")
