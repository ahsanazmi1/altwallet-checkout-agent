"""Structured logging configuration for AltWallet Checkout Agent."""

import contextvars
import logging
import os
import sys
from typing import Any

import structlog

# Type alias for cleaner function signatures
BoundLogger = structlog.stdlib.BoundLogger

# Context variable to store trace_id
trace_id_var = contextvars.ContextVar("trace_id", default=None)


def get_log_level() -> str:
    """Get log level from environment variable, defaulting to INFO."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging() -> None:
    """Configure structlog with JSON formatting and ISO8601 timestamps."""
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, get_log_level()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp in ISO8601 format
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            # Add trace_id from context
            _add_trace_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Output as JSON
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _add_trace_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add trace_id to log event if available in context."""
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def set_trace_id(trace_id: str) -> None:
    """Set trace_id in the current context."""
    trace_id_var.set(trace_id)


def get_logger(name: str | None = None) -> BoundLogger:
    """Get a pre-configured structured logger.

    Args:
        name: Logger name (optional, defaults to module name)

    Returns:
        Configured structlog logger
    """
    if name is None:
        # Get the calling module name
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "altwallet_agent")

    return structlog.get_logger(name)


# Configure logging on module import
configure_logging()
