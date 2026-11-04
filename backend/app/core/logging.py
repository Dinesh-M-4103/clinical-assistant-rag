"""structlog configuration shared by the app and its middleware."""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structured logging: JSON for production, coloured console for dev."""
    level_no = logging.getLevelName(level.upper())
    if not isinstance(level_no, int):
        raise ValueError(f"Unknown log level: {level}")

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_no),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=level_no, format="%(message)s", stream=sys.stdout, force=True)
    # The request middleware emits the access log (with request id); uvicorn's would duplicate it.
    logging.getLogger("uvicorn.access").disabled = True
