"""
Novora — MCP Server: Timer Tools
Exposes Pomodoro timer operations as MCP tools.
"""
from skills.pomodoro_skill import pomodoro_skill


def register_timer_tools(mcp):
    """Register all timer-related MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def start_timer(user_id: str, task_title: str, work_minutes: int = 25) -> dict:
        """
        Start a new Pomodoro work session for a user.

        Args:
            user_id: The authenticated user's ID
            task_title: The task the user is focusing on
            work_minutes: Duration of work session in minutes (1-120)

        Returns:
            Current session state dictionary
        """
        if not user_id or not task_title:
            return {"error": "user_id and task_title are required"}
        work_minutes = max(1, min(120, work_minutes))
        return pomodoro_skill.start_session(user_id, task_title, work_minutes)

    @mcp.tool()
    def pause_timer(user_id: str) -> dict:
        """
        Pause the current Pomodoro session.

        Args:
            user_id: The authenticated user's ID

        Returns:
            Updated session state
        """
        return pomodoro_skill.pause_session(user_id)

    @mcp.tool()
    def resume_timer(user_id: str) -> dict:
        """
        Resume a paused Pomodoro session.

        Args:
            user_id: The authenticated user's ID

        Returns:
            Updated session state
        """
        return pomodoro_skill.resume_session(user_id)

    @mcp.tool()
    def get_timer_status(user_id: str) -> dict:
        """
        Get the current timer status for a user.

        Args:
            user_id: The authenticated user's ID

        Returns:
            Current session state including remaining seconds
        """
        return pomodoro_skill.get_status(user_id)

    @mcp.tool()
    def complete_work_session(
        user_id: str,
        focus_score: float = None,
        reflection_note: str = None,
    ) -> dict:
        """
        Mark a work session as complete and transition to break.

        Args:
            user_id: The authenticated user's ID
            focus_score: Optional focus quality rating (1.0-5.0)
            reflection_note: Optional reflection text

        Returns:
            Updated session state (now in break mode)
        """
        return pomodoro_skill.complete_work_session(user_id, focus_score, reflection_note)

    @mcp.tool()
    def start_break(user_id: str) -> dict:
        """
        Begin the break phase after a completed work session.

        Args:
            user_id: The authenticated user's ID

        Returns:
            Updated session state with break duration
        """
        return pomodoro_skill.begin_break(user_id)
