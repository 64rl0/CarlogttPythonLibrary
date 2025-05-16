# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_decorators.py
# Created 4/25/25 - 3:30 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made code or quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import logging
import time
from importlib import reload

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


# Mocks
class CustomException(Exception):
    pass


@pytest.fixture(autouse=True)
def reload_decorators_module_to_override_patch():
    """
    Fixture to reload the decorators module to override the patch decorator.
    """

    import carlogtt_library.utils.decorators

    reload(carlogtt_library.utils.decorators)

    yield


def test_retry_success():
    from carlogtt_library.utils.decorators import retry

    counter = {"calls": 0}

    @retry(CustomException, tries=3, delay_secs=0)
    def might_fail():
        counter["calls"] += 1
        if counter["calls"] < 2:
            raise CustomException("Fail once!")
        return "success"

    assert might_fail() == "success"
    assert counter["calls"] == 2


def test_retry_failure():
    from carlogtt_library.utils.decorators import retry

    @retry(CustomException, tries=2, delay_secs=0)
    def always_fail():
        raise CustomException("Always fails")

    with pytest.raises(CustomException):
        always_fail()


def test_retry_context_manager():
    from carlogtt_library.utils.decorators import retry

    counter = {"calls": 0}

    def might_fail():
        counter["calls"] += 1
        if counter["calls"] < 3:
            raise CustomException("Fail twice!")
        return "done"

    with retry(CustomException, tries=4, delay_secs=0) as retryer:
        assert retryer(might_fail) == "done"

    assert counter["calls"] == 3


def test_benchmark_execution(caplog):
    from carlogtt_library.utils.decorators import benchmark_execution

    caplog.set_level(logging.INFO)

    @benchmark_execution()
    def dummy_function():
        time.sleep(0.01)
        return "ok"

    result = dummy_function()

    assert result == "ok"
    assert any("Execution of dummy_function took" in record.message for record in caplog.records)


def test_benchmark_custom_resolution(caplog):
    from carlogtt_library.utils.decorators import BenchmarkResolution, benchmark_execution

    caplog.set_level(logging.INFO)

    @benchmark_execution(resolution=BenchmarkResolution.SECONDS)
    def dummy_function():
        time.sleep(0.1)
        return "ok"

    result = dummy_function()
    assert result == "ok"


def test_log_execution(caplog):
    from carlogtt_library.utils.decorators import log_execution

    caplog.set_level(logging.INFO)

    @log_execution()
    def dummy_function():
        return "hello"

    result = dummy_function()

    assert result == "hello"
    messages = [record.message for record in caplog.records]
    assert any("Initiating dummy_function" in msg for msg in messages)
    assert any("Finished dummy_function" in msg for msg in messages)


def test_retry_invalid_exception():
    from carlogtt_library.utils.decorators import retry

    with pytest.raises(ValueError):
        retry(["not_an_exception"], tries=2)


def test_benchmark_invalid_resolution_type():
    from carlogtt_library.utils.decorators import benchmark_execution

    with pytest.raises(TypeError):
        benchmark_execution(resolution=123)


def test_benchmark_invalid_resolution_value():
    from carlogtt_library.utils.decorators import benchmark_execution

    with pytest.raises(ValueError):
        benchmark_execution(resolution="invalid")


def test_retryer_non_callable_arg_raises():
    from carlogtt_library.utils.decorators import retry

    with retry(Exception) as retryer:
        with pytest.raises(TypeError) as excinfo:
            retryer(42)  # 42 is *not* callable

    assert "expected a callable as its first argument" in str(excinfo.value)
