# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_legacy.py
# Created 4/26/25 - 8:51 PM UK Time (London) by carlogtt
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
import warnings

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


# ----------------------------------------------------------------------
# Helper – capture warnings conveniently
# ----------------------------------------------------------------------
class _WarnCatcher:
    def __enter__(self):
        self._cm = warnings.catch_warnings(record=True)
        self._records = self._cm.__enter__()
        warnings.simplefilter("always")
        return self._records

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


# ----------------------------------------------------------------------
# Tests ----------------------------------------------------------------
# ----------------------------------------------------------------------
def test_cli_style_attr_returns_constant_and_warns():
    import carlogtt_library as mylib

    # Pick one of the legacy names that maps to CLIStyle
    legacy_name = "cli_red"
    expected_attr = "CLI_RED"

    assert hasattr(mylib, "CLIStyle")  # sanity

    with _WarnCatcher() as rec:
        value = getattr(mylib, legacy_name)

    # Warning emitted once, correct category
    assert len(rec) == 1 and issubclass(rec[0].category, DeprecationWarning)
    assert legacy_name in str(rec[0].message)

    # Returned value is *exactly* the constant on CLIStyle
    assert value is getattr(mylib.CLIStyle, expected_attr)


def test_other_deprecated_name_warns_and_raises():
    import carlogtt_library as mylib

    # This name is mapped to StringUtils, but proxy should raise AttributeError
    legacy_name = "get_random_string"

    with _WarnCatcher() as rec:
        with pytest.raises(AttributeError):
            _ = getattr(mylib, legacy_name)

    # Deprecation warning still issued
    assert len(rec) == 1 and issubclass(rec[0].category, DeprecationWarning)
    assert legacy_name in str(rec[0].message)


def test_unknown_attribute_no_warning_and_attribute_error():
    import carlogtt_library as mylib

    unknown = "definitely_not_exported"

    with _WarnCatcher() as rec:
        with pytest.raises(AttributeError):
            _ = getattr(mylib, unknown)

    # No deprecation warnings because the name isn't mapped
    assert len(rec) == 0
