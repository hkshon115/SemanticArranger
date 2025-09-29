"""
This module sets up structured, JSON-based logging for the application.

It uses the `structlog` library to create logs that are easy to parse and
query, and it automatically adds a `correlation_id` to each log entry.
This is essential for tracing requests as they flow through the various
components of the pipeline in a concurrent environment.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
import structlog

# Context variable to hold the correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    """
    Retrieves the current correlation ID or generates a new one.
    """
    correlation_id = correlation_id_var.get()
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id

def add_correlation_id(_, __, event_dict):
    """
    Structlog processor to add the correlation ID to the log entry.
    """
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict

def configure_logging(log_level: str = "INFO"):
    """
    Configures structlog for structured JSON logging.
    """
    logging.basicConfig(level=log_level, stream=sys.stdout, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_correlation_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> any:
    """
    Returns a configured structlog logger.
    """
    return structlog.get_logger(name)

# Configure logging on import
configure_logging()
