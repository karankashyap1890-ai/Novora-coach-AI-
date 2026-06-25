"""
Novora — Security: Input Validators
Pydantic v2 models with strict validation rules for all API inputs.
"""
import re
from typing import Optional
from pydantic import BaseModel, field_validator, EmailStr, Field


# ---------- Shared Validators ----------

SAFE_TEXT_RE = re.compile(r"[<>\"'&;|`$\\]")  # Characters to block


def sanitize_text(value: str, field_name: str = "field") -> str:
    """Strip dangerous characters from user-supplied text."""
    if SAFE_TEXT_RE.search(value):
        raise ValueError(
            f"{field_name} contains disallowed characters: < > \" ' & ; | ` $ \\"
        )
    return value.strip()


# ---------- Auth Schemas ----------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username must be alphanumeric (underscore and dash allowed)")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


# ---------- Task Schemas ----------

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_safe(cls, v):
        return sanitize_text(v, "title")

    @field_validator("description")
    @classmethod
    def description_safe(cls, v):
        if v is not None:
            return sanitize_text(v, "description")
        return v


# ---------- Session Schemas ----------

class SessionStart(BaseModel):
    task_id: Optional[str] = Field(default=None, max_length=36)
    work_minutes: int = Field(default=25, ge=1, le=120)
    break_minutes: int = Field(default=5, ge=1, le=60)


class SessionReflection(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    focus_score: float = Field(ge=1.0, le=5.0)
    reflection_note: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("reflection_note")
    @classmethod
    def note_safe(cls, v):
        if v is not None:
            return sanitize_text(v, "reflection_note")
        return v


# ---------- Chat Schemas ----------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=36)

    @field_validator("message")
    @classmethod
    def message_safe(cls, v):
        # Bleach will handle final HTML sanitization — here we just strip
        return v.strip()
