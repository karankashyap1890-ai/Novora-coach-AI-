"""
Novora Backend — Configuration Management
Centralizes all settings via pydantic-settings with .env file support.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Novora"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "novora-dev-secret-key-change-in-production-32chars"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    mcp_port: int = 3001

    # AI
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    demo_mode: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./novora.db"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Rate limiting
    rate_limit_per_minute: int = 60

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Pomodoro defaults
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4

    # Agent system
    coach_personality: str = "warm"
    agent_response_delay_ms: int = 600


@lru_cache()
def get_settings() -> Settings:
    return Settings()
