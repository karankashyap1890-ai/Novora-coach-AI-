"""
Novora — Security: Safe Execution Sandbox
Sanitizes all agent-generated content before it reaches the user.
Prevents XSS, prompt-injection artifacts, and raw HTML injection.
"""
import re
import bleach
from typing import Any

# Allowed HTML tags in agent responses (none — plain text only)
ALLOWED_TAGS: list = []
ALLOWED_ATTRIBUTES: dict = {}

# Patterns that indicate prompt-injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s*prompt",
    r"<\s*script",
    r"javascript\s*:",
    r"data\s*:",
    r"vbscript\s*:",
    r"onload\s*=",
    r"onerror\s*=",
]

_injection_re = re.compile(
    "|".join(INJECTION_PATTERNS),
    re.IGNORECASE,
)


def sanitize_agent_output(text: str) -> str:
    """
    Clean agent-generated text before sending to the client:
    1. Strip any HTML tags via bleach
    2. Check for prompt injection patterns
    3. Return safe plain text
    """
    if not isinstance(text, str):
        return str(text)

    # Strip HTML
    clean = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

    # Detect injection attempts — log and redact
    if _injection_re.search(clean):
        return "[Content blocked by safety filter]"

    return clean.strip()


def sanitize_user_input(text: str, max_length: int = 2000) -> str:
    """Sanitize raw user input from chat or forms."""
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    text = text[:max_length]
    clean = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return clean.strip()


def safe_int(value: Any, default: int = 0, min_val: int = 0, max_val: int = 9999) -> int:
    """Safely parse an integer with bounds checking."""
    try:
        result = int(value)
        return max(min_val, min(max_val, result))
    except (TypeError, ValueError):
        return default
