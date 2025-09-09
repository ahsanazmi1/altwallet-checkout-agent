"""Structured logging configuration for Orca Checkout Agent.

Provides structured JSON logs when ``structlog`` is available. If ``structlog``
is not installed, falls back to Python's standard ``logging`` so the CLI can
run without extra dependencies.
"""

import contextvars
import logging
import os
import sys
import time
from collections.abc import MutableMapping
from typing import Any

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
    # Type alias for cleaner function signatures
    BoundLogger = structlog.stdlib.BoundLogger
except Exception:  # pragma: no cover - defensive fallback when structlog missing
    STRUCTLOG_AVAILABLE = False

    class BoundLogger:  # type: ignore[no-redef]
        """Minimal logger API compatible with structlog's BoundLogger methods.

        This wrapper ensures calls like ``logger.info(...)`` continue to work
        even when ``structlog`` isn't installed.
        """

        def __init__(self, name: str | None = None) -> None:
            self._logger = logging.getLogger(name or "altwallet_agent")

        def _log(self, level: int, event: str | None = None, **event_dict: Any) -> None:
            # Emit JSON-ish dictionary when kwargs provided; otherwise just the event
            if event_dict:
                # Avoid PII leakage by not attempting to massage fields here
                self._logger.log(level, str(event_dict))
            elif event:
                self._logger.log(level, event)
            else:
                self._logger.log(level, "")

        def info(self, event: str | None = None, **event_dict: Any) -> None:
            self._log(logging.INFO, event, **event_dict)

        def warning(self, event: str | None = None, **event_dict: Any) -> None:
            self._log(logging.WARNING, event, **event_dict)

        def error(self, event: str | None = None, **event_dict: Any) -> None:
            self._log(logging.ERROR, event, **event_dict)

        def debug(self, event: str | None = None, **event_dict: Any) -> None:
            self._log(logging.DEBUG, event, **event_dict)


# Context variables to store request context
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
request_start_time_var: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "request_start_time", default=None
)


def get_log_level() -> str:
    """Get log level from environment variable, defaulting to INFO."""
    # Check for LOG_SILENT first
    if is_silent_mode():
        return "CRITICAL"  # Only show critical errors when silent
    return os.getenv("LOG_LEVEL", "INFO").upper()


def is_silent_mode() -> bool:
    """Check if silent mode is enabled via LOG_SILENT environment variable."""
    return os.getenv("LOG_SILENT", "0").lower() in ("1", "true", "yes", "on")


def configure_logging() -> None:
    """Configure logging (structured if structlog available, else standard)."""

    # Check for silent mode
    if is_silent_mode():
        logging.basicConfig(level=logging.CRITICAL, handlers=[logging.NullHandler()])
        return

    # Base stdlib logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, get_log_level()),
    )

    if not STRUCTLOG_AVAILABLE:
        # Fallback: keep stdlib logging; nothing else to do
        return

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            _add_structured_fields,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Ensure structlog outputs to stderr for CLI compatibility
    logger_names = [
        "altwallet_agent",
        "altwallet_agent.scoring",
        "altwallet_agent.decisioning",
        "altwallet_agent.webhooks",
        "altwallet_agent.analytics",
    ]
    for logger_name in logger_names:
        lg = logging.getLogger(logger_name)
        if not lg.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(message)s"))
            lg.addHandler(handler)
            lg.propagate = False


def _add_structured_fields(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Add structured fields to log event."""

    # Add timestamp (ts)
    if "timestamp" in event_dict:
        event_dict["ts"] = event_dict.pop("timestamp")

    # Add level
    if "level" in event_dict:
        event_dict["level"] = event_dict["level"].lower()

    # Add component (from logger name)
    if "logger" in event_dict:
        logger_name = event_dict["logger"]
        # Extract component from logger name (e.g., "src.altwallet_agent.cli" -> "cli")
        component = logger_name.split(".")[-1] if "." in logger_name else logger_name
        event_dict["component"] = component
        # Remove the original logger field to avoid duplication
        del event_dict["logger"]

    # Add request_id (from trace_id)
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["request_id"] = trace_id

    # Add latency_ms if request start time is available
    request_start_time = request_start_time_var.get()
    if request_start_time:
        latency_ms = int((time.time() - request_start_time) * 1000)
        event_dict["latency_ms"] = latency_ms

    # Remove any PII fields that might have been added
    _remove_pii_fields(event_dict)

    return event_dict


def _remove_pii_fields(event_dict: MutableMapping[str, Any]) -> None:
    """Remove PII fields from log events."""
    pii_fields = {
        "customer_id",
        "user_id",
        "merchant_id",
        "device_id",
        "ip",
        "email",
        "phone",
        "name",
        "address",
        "city",
        "country",
        "postal_code",
        "ssn",
        "card_number",
        "account_number",
        "password",
        "token",
        "secret",
        "key",
    }

    # Remove exact matches
    for field in pii_fields:
        if field in event_dict:
            del event_dict[field]

    # Remove fields that contain PII keywords
    fields_to_remove = []
    for field in event_dict:
        field_lower = field.lower()
        if any(pii_keyword in field_lower for pii_keyword in pii_fields):
            fields_to_remove.append(field)

    for field in fields_to_remove:
        del event_dict[field]


def set_trace_id(trace_id: str) -> None:
    """Set trace_id in the current context."""
    trace_id_var.set(trace_id)


def set_request_start_time() -> None:
    """Set request start time for latency calculation."""
    request_start_time_var.set(time.time())


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

        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
            if frame is not None:
                name = frame.f_globals.get("__name__", "altwallet_agent")

    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)  # type: ignore[no-any-return]
    return BoundLogger(name)  # type: ignore[call-arg]


# Configure logging on module import
configure_logging()
