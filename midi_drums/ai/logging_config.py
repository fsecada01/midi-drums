"""Logging configuration for MIDI Drums AI module.

Production-grade logging using loguru with structured output,
proper log levels, and context tracking.
"""

import sys
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()


def configure_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str | Path = "logs",
    format_string: str | None = None,
) -> None:
    """Configure loguru logging for AI modules.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file in addition to console
        log_dir: Directory for log files
        format_string: Custom format string (uses default if None)

    Example:
        >>> from midi_drums.ai.logging_config import configure_logging
        >>> configure_logging(level="DEBUG", log_to_file=True)
    """
    # Default format with colors for console
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # Console handler with colors
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler (no colors, with rotation)
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Main log file with rotation
        logger.add(
            log_path / "midi_drums_ai.log",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

        # Error-only log file
        logger.add(
            log_path / "midi_drums_ai_errors.log",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}\n{exception}"
            ),
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

    logger.info(
        f"Logging configured: level={level}, file_logging={log_to_file}"
    )


# Default configuration for AI modules
configure_logging(level="INFO", log_to_file=False)


def get_logger(name: str):
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> from midi_drums.ai.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("AI pattern generation started")
    """
    return logger.bind(module=name)
