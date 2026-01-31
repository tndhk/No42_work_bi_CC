"""Logging tests following TDD."""
import pytest


def test_setup_logging_configures_structlog():
    """setup_logging()がstructlogを設定する."""
    from app.core.logging import setup_logging

    # Should not raise any exception
    setup_logging()

    # Verify structlog is configured
    import structlog

    config = structlog.get_config()
    assert config is not None
    assert len(config["processors"]) == 2
