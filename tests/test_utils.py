"""Tests for shared utilities: FraudShieldException and logging helpers."""

import logging
import sys

import pytest

from utils.exception import FraudShieldException, error_message_detail
from utils.logging import get_logger, logger


# ── FraudShieldException ──────────────────────────────────────────────────

def test_fraud_shield_exception_has_message():
    try:
        raise ValueError("boom")
    except ValueError as e:
        exc = FraudShieldException(str(e), sys)
        assert "boom" in str(exc)
        assert "error_message" in exc.__dict__


def test_error_message_detail_handles_no_traceback():
    msg = error_message_detail(ValueError("x"), sys)
    assert "Error occurred" in msg


def test_exception_is_a_real_exception():
    assert issubclass(FraudShieldException, Exception)
    with pytest.raises(FraudShieldException):
        raise FraudShieldException("test", sys)


# ── logging ───────────────────────────────────────────────────────────────

def test_logger_is_a_logger():
    assert isinstance(logger, logging.Logger)
    assert logger.name == "FraudShieldAI"


def test_get_logger_returns_same_instance():
    # handler is already configured → returns the same logger
    a = get_logger("FraudShieldAI")
    b = get_logger("FraudShieldAI")
    assert a is b


def test_get_logger_creates_unique_named_logger():
    fresh = get_logger("some_other_logger")
    assert fresh.name == "some_other_logger"
    assert isinstance(fresh, logging.Logger)
