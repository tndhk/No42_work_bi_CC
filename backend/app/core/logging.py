"""Logging configuration using structlog."""
import structlog


def setup_logging() -> None:
    """Configure structured logging with JSON output."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
