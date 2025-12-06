"""Utility functions for Fastpy CLI."""

import functools
import shlex
import subprocess
import time
from typing import Callable, Optional, TypeVar

from rich.console import Console

from fastpy_cli.logger import log_debug, log_warning

console = Console()

T = TypeVar("T")

# Allowlist of safe command prefixes for AI-generated commands
SAFE_COMMAND_PREFIXES = [
    "fastpy make:",
    "fastpy db:",
    "fastpy route:",
    "fastpy serve",
    "fastpy test",
    "fastpy ai:",
    "fastpy setup:",
    "fastpy deploy:",
    "fastpy domain:",
    "fastpy env:",
    "fastpy service:",
    "fastpy list",
    "fastpy update",
    "fastpy ",
]


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        log_warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log_debug(f"All {max_attempts} attempts failed")

            if last_exception:
                raise last_exception
            raise RuntimeError("Retry failed without exception")

        return wrapper

    return decorator


def is_safe_command(command: str) -> bool:
    """Check if a command is safe to execute.

    Args:
        command: The command string to check

    Returns:
        True if the command is considered safe
    """
    command = command.strip()

    # Check against allowlist of safe prefixes
    return any(command.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES)


def validate_command(command: str) -> tuple[bool, str]:
    """Validate a command for safe execution.

    Args:
        command: The command string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not command or not command.strip():
        return False, "Empty command"

    # Check for dangerous patterns
    dangerous_patterns = [
        "rm -rf",
        "rm -r /",
        "> /dev/",
        "| bash",
        "| sh",
        "; bash",
        "; sh",
        "curl | ",
        "wget | ",
        "eval ",
        "exec ",
        "$(",
        "`",
        "&&",  # Chained commands need individual validation
        "||",
        ";",  # Multiple commands
    ]

    command_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return False, f"Potentially dangerous pattern detected: {pattern}"

    return True, ""


def safe_execute_command(
    command: str,
    cwd: Optional[str] = None,
    allow_unsafe: bool = False,
) -> subprocess.CompletedProcess:
    """Safely execute a command without shell=True.

    Args:
        command: The command string to execute
        cwd: Working directory for the command
        allow_unsafe: Skip safety validation (for trusted commands)

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command is invalid or unsafe
    """
    if not allow_unsafe:
        # Validate command safety
        is_valid, error = validate_command(command)
        if not is_valid:
            raise ValueError(f"Unsafe command rejected: {error}")

        if not is_safe_command(command):
            raise ValueError(
                "Command not in allowlist. Only Fastpy CLI commands are allowed."
            )

    # Parse command into arguments (safe, no shell injection)
    try:
        args = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command syntax: {e}") from e

    log_debug(f"Executing: {args}")

    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=False,
    )


def parse_command_safely(command: str) -> list[str]:
    """Parse a command string into a list of arguments.

    Args:
        command: The command string to parse

    Returns:
        List of command arguments
    """
    return shlex.split(command)


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix
