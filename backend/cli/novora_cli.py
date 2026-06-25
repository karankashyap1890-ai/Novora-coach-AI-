"""
Novora — CLI Tool
Provides command-line access to Coach Novora for terminal-first users.
"""
import asyncio
import json
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich import print as rprint

console = Console()

BANNER = """
[bold violet]╔═══════════════════════════════════════╗[/bold violet]
[bold violet]║   🍅  NOVORA — Pomodoro Coach         ║[/bold violet]
[bold violet]║   Offline AI Agent System v1.0        ║[/bold violet]
[bold violet]╚═══════════════════════════════════════╝[/bold violet]
"""

API_BASE = "http://localhost:8000"
_token: str | None = None


def get_headers():
    if _token:
        return {"Authorization": f"Bearer {_token}"}
    return {}


def _load_token() -> str | None:
    try:
        import os
        token_file = os.path.join(os.path.expanduser("~"), ".novora_token")
        if os.path.exists(token_file):
            with open(token_file) as f:
                return f.read().strip()
    except Exception:
        pass
    return None


def _save_token(token: str):
    import os
    token_file = os.path.join(os.path.expanduser("~"), ".novora_token")
    with open(token_file, "w") as f:
        f.write(token)


# ─────────────────────────────────────────────
# CLI Group
# ─────────────────────────────────────────────

@click.group()
@click.pass_context
def cli(ctx):
    """🍅 Novora — Your offline AI Pomodoro coaching system."""
    ctx.ensure_object(dict)
    ctx.obj["token"] = _load_token()


# ─────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────

@cli.command()
def banner():
    """Show the Novora banner."""
    console.print(BANNER)


@cli.command()
@click.option("--username", "-u", prompt="Username", help="Your Novora username")
@click.option("--password", "-p", prompt="Password", hide_input=True, help="Your password")
def login(username, password):
    """Login to your Novora account."""
    import httpx
    try:
        r = httpx.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
        if r.status_code == 200:
            data = r.json()
            _save_token(data["access_token"])
            console.print(f"[green]✅ Logged in as {data['user']['username']}![/green]")
        else:
            console.print(f"[red]❌ Login failed: {r.json().get('detail', 'Unknown error')}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Cannot connect to Novora backend. Is it running?[/red]")
        console.print(f"   Start with: [cyan]cd backend && uv run uvicorn main:app --reload[/cyan]")


@cli.command()
@click.argument("task", required=False)
@click.option("--minutes", "-m", default=25, help="Work session duration in minutes (default: 25)")
@click.pass_context
def start(ctx, task, minutes):
    """▶️  Start a Pomodoro session.

    Example: novora start "Write my report" --minutes 25
    """
    import httpx

    token = ctx.obj.get("token") or _load_token()
    if not token:
        console.print("[red]❌ Not logged in. Run: novora login[/red]")
        return

    if not task:
        task = click.prompt("🎯 What are you working on")

    console.print(BANNER)
    console.print(Panel(
        f"[bold green]Starting Pomodoro Session[/bold green]\n"
        f"📋 Task: [cyan]{task}[/cyan]\n"
        f"⏱️  Duration: [yellow]{minutes} minutes[/yellow]",
        title="🍅 Novora",
        border_style="violet",
    ))

    try:
        r = httpx.post(
            f"{API_BASE}/sessions/start",
            json={"work_minutes": minutes, "break_minutes": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 201:
            console.print(f"[red]❌ Failed to start session: {r.text}[/red]")
            return

        session = r.json()
        console.print(f"\n[green]✅ Session #{session['session_number']} started![/green]")
        console.print("[dim]Press Ctrl+C to pause[/dim]\n")

        # CLI countdown timer
        total_seconds = minutes * 60
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold violet]{task.description}"),
            BarColumn(bar_width=40),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            timer_task = progress.add_task(f"🍅 Focusing on: {task}", total=total_seconds)
            for i in range(total_seconds):
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
                progress.advance(timer_task)

        console.print(Panel(
            "[bold green]🎉 Session Complete![/bold green]\n"
            "Excellent work! Take a well-deserved break.",
            border_style="green",
        ))

        # Ask for reflection
        score = click.prompt("\n⭐ Rate your focus (1-5)", type=float, default=4.0)
        note = click.prompt("📝 Any reflections? (press Enter to skip)", default="", show_default=False)

        httpx.patch(
            f"{API_BASE}/sessions/{session['id']}/complete",
            json={
                "session_id": session["id"],
                "focus_score": score,
                "reflection_note": note or None,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        console.print("[green]✅ Session saved![/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️  Session paused. Run 'novora resume' to continue.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@cli.command()
@click.pass_context
def status(ctx):
    """📊 Check your current timer status."""
    import httpx
    token = ctx.obj.get("token") or _load_token()
    if not token:
        console.print("[red]❌ Not logged in. Run: novora login[/red]")
        return

    try:
        r = httpx.get(
            f"{API_BASE}/sessions/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        state = r.json()
        remaining = state.get("remaining_seconds", 0)
        mins, secs = divmod(remaining, 60)
        s_state = state.get("state", "idle")
        task = state.get("task_title", "—")
        session = state.get("session_number", 0)

        table = Table(title="🍅 Novora Status", border_style="violet")
        table.add_column("Field", style="bold cyan")
        table.add_column("Value", style="white")
        table.add_row("State", s_state.upper())
        table.add_row("Task", task)
        table.add_row("Session #", str(session))
        table.add_row("Remaining", f"{mins:02d}:{secs:02d}")
        table.add_row("Sessions Done", str(state.get("completed_sessions", 0)))
        console.print(table)

    except Exception:
        console.print("[red]❌ Cannot connect to backend. Is Novora running?[/red]")


@cli.command()
@click.pass_context
def stats(ctx):
    """📈 Show your productivity statistics."""
    import httpx
    token = ctx.obj.get("token") or _load_token()
    if not token:
        console.print("[red]❌ Not logged in. Run: novora login[/red]")
        return

    try:
        r = httpx.get(
            f"{API_BASE}/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json()
        console.print(Panel(
            data.get("message", "No stats available yet."),
            title="📊 Your Productivity Stats",
            border_style="violet",
        ))
    except Exception:
        console.print("[red]❌ Cannot connect to backend.[/red]")


@cli.command()
def info():
    """ℹ️  Show system information."""
    console.print(BANNER)
    table = Table(title="System Info", border_style="violet")
    table.add_column("Component", style="bold cyan")
    table.add_column("Status", style="green")
    table.add_row("Backend", f"http://localhost:8000")
    table.add_row("Frontend", f"http://localhost:3000")
    table.add_row("MCP Server", "stdio transport")
    table.add_row("AI Mode", "Offline (no API key)")
    table.add_row("Agents", "5 (Orchestrator, Timer, Encouragement, Reflection, Analytics)")
    console.print(table)


if __name__ == "__main__":
    cli()
