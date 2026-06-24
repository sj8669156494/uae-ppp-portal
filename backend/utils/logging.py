from __future__ import annotations
import logging
import logging.handlers
import os
import structlog
from backend.config import settings


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    os.makedirs(os.path.dirname(settings.log_file_path), exist_ok=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    handler = logging.handlers.TimedRotatingFileHandler(
        settings.log_file_path,
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(log_level)
    root_logger.addHandler(console)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
