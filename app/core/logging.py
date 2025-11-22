"""Logging configuration for the application."""

import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configure application logging.

    Sets up console logging with appropriate formatter.
    """
    # Create formatter
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        handlers=[console_handler],
    )

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Name of the logger (usually __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
