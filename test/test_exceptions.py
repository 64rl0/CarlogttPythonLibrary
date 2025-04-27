# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_exceptions.py
# Created 4/25/25 - 10:08 PM UK Time (London) by carlogtt
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
import json
import logging
import warnings

# Third Party Library Imports
from test__entrypoint__ import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)
# master_logger.detach_root_logger()

# Type aliases
#


def _instantiate_with_warning(*args, **kwargs):
    """
    Instantiate SimTHandlerError while forcing DeprecationWarning
    to be raised each time (even after the first call).
    """
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", category=DeprecationWarning)
        exc = mylib.SimTHandlerError(*args, **kwargs)
    return exc, record


def test_deprecation_warning_is_emitted():
    """A DeprecationWarning should be issued on every instantiation."""
    _, record = _instantiate_with_warning("boom")

    assert any(
        issubclass(item.category, DeprecationWarning) for item in record
    ), "Expected a DeprecationWarning to be raised"

    # Optional: check that the warning message contains the class name
    assert any("SimTHandlerError" in str(item.message) for item in record)


def test_warning_is_logged(caplog):
    """
    The module logger should log the same deprecation message
    at WARNING level.
    """
    with caplog.at_level(logging.WARNING):
        _instantiate_with_warning("boom")

    assert any(
        "SimTHandlerError" in message and "deprecated" in message.lower()
        for message in caplog.messages
    ), "Expected a deprecation log record at WARNING level"


def test_inheritance_relationships():
    """The deprecated class should still be compatible with the hierarchy."""
    exc, _ = _instantiate_with_warning("kaboom")

    assert isinstance(exc, mylib.SimTHandlerError)
    assert isinstance(exc, mylib.SimTError)
    assert isinstance(exc, mylib.CarlogttLibraryError)
    assert isinstance(exc, Exception)  # ultimately a built-in Exception


def test_to_dict_and_to_json_roundtrip():
    """`to_dict` and `to_json` should stay in sync."""
    exc, _ = _instantiate_with_warning("payload error")

    as_dict = exc.to_dict()
    assert as_dict == {"exception": repr(exc)}

    as_json = exc.to_json()
    parsed = json.loads(as_json)
    assert parsed == as_dict
