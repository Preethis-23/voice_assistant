import os
import re
from pathlib import Path
from typing import Tuple
from app.core.config import settings
from app.core.logging import logger

# Protected system paths that should never be deleted or modified
PROTECTED_PATHS = [
    Path(os.environ.get("SystemRoot", r"C:\Windows")).resolve(),
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")).resolve(),
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).resolve(),
]

DESTRUCTIVE_COMMAND_PATTERNS = [
    r"\brmdir\s+/s\b",
    r"\bdel\s+/[fqs]\b",
    r"\bformat\s+[a-z]:",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bdiskpart\b",
]

class SafetyViolationError(Exception):
    """Raised when an action violates safety guardrails."""
    pass

def sanitize_path(path_str: str) -> Path:
    """Normalizes and resolves a path, expanding user shortcuts like Desktop/Downloads."""
    raw = path_str.strip().strip("'\"")
    home = Path.home()

    # Expand common shortcuts
    if raw.lower() == "desktop" or raw.lower().startswith("desktop/"):
        target = home / "Desktop" / raw[8:].lstrip(r"/\\")
    elif raw.lower() == "downloads" or raw.lower().startswith("downloads/"):
        target = home / "Downloads" / raw[10:].lstrip(r"/\\")
    elif raw.lower() == "documents" or raw.lower().startswith("documents/"):
        target = home / "Documents" / raw[10:].lstrip(r"/\\")
    else:
        target = Path(raw).expanduser()

    return target.resolve()

def is_safe_path(target_path: Path) -> Tuple[bool, str]:
    """Ensures a path does not target protected operating system directories."""
    resolved = target_path.resolve()
    for protected in PROTECTED_PATHS:
        try:
            if resolved == protected or protected in resolved.parents:
                return False, f"Access to system-protected directory '{protected}' is denied."
        except Exception:
            continue
    return True, ""

def is_destructive_command(cmd: str) -> Tuple[bool, str]:
    """Scans command string for destructive operations."""
    lowered = cmd.lower()
    for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
        if re.search(pattern, lowered):
            return True, f"Command matches dangerous pattern '{pattern}'"
    return False, ""

def verify_action_allowed(action_name: str, details: str, auto_confirm: bool = False) -> bool:
    """Checks if action requires user confirmation."""
    if not settings.REQUIRE_CONFIRMATION_FOR_DESTRUCTIVE or auto_confirm:
        return True

    logger.warning(f"Safety Gate: Confirmation required for {action_name}: {details}")
    # In interactive CLI, prompt user if possible:
    print(f"\n⚠️  [SAFETY CONFIRMATION NEEDED]")
    print(f"Action: {action_name}")
    print(f"Details: {details}")
    response = input("Allow this action? (y/N): ").strip().lower()
    return response == "y"
