"""Logging configuration for Fastpy CLI."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Global logger instance
_logger: Optional[logging.Logger] = None
_verbose: bool = False
_debug: bool = False

console = Console(stderr=True)


def setup_logger(
    verbose: bool = False,
    debug: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up and configure the logger.

    Args:
        verbose: Enable verbose output (INFO level)
        debug: Enable debug output (DEBUG level)
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    global _logger, _verbose, _debug

    _verbose = verbose
    _debug = debug

    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Create logger
    logger = logging.getLogger("fastpy")
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    logger.handlers.clear()

    # Rich console handler
    console_handler = RichHandler(
        console=console,
        show_time=debug,
        show_path=debug,
        rich_tracebacks=True,
        tracebacks_show_locals=debug,
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _verbose


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _debug


def log_debug(message: str) -> None:
    """Log a debug message."""
    get_logger().debug(message)


def log_info(message: str) -> None:
    """Log an info message."""
    get_logger().info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    get_logger().warning(message)


def log_error(message: str) -> None:
    """Log an error message."""
    get_logger().error(message)


def log_exception(message: str) -> None:
    """Log an exception with traceback."""
    get_logger().exception(message)
