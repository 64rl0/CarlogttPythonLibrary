# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_validators.py
# Created 4/26/25 - 8:19 AM UK Time (London) by carlogtt
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

# Third Party Library Imports
import pytest
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


# ----------------------------------------------------------------------
# Fixture ----------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def iv():
    return mylib.InputValidator()


# ----------------------------------------------------------------------
# validate_non_empty_strings --------------------------------------------
# ----------------------------------------------------------------------
def test_non_empty_strips_and_returns(iv):
    res = iv.validate_non_empty_strings(name="  Alice ", city="\tParis\n")
    assert res == {"name": "Alice", "city": "Paris"}


def test_non_empty_empty_value_omitted(iv):
    # empty string should simply be omitted, not raise
    res = iv.validate_non_empty_strings(foo="", bar="ok")
    assert res == {"bar": "ok"}


def test_non_empty_whitespace_only_raises(iv):
    with pytest.raises(ValueError):
        iv.validate_non_empty_strings(title="  \t  ")


# ----------------------------------------------------------------------
# validate_username_requirements ----------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "good",
    [
        "Alice5",
        "user1234",
        "BobSmith16",
    ],
)
def test_username_valid(iv, good):
    assert iv.validate_username_requirements(good) == good


@pytest.mark.parametrize(
    "bad",
    [
        "abc",  # too short
        "thisusernameistoolong",  # too long
        "foo!",  # punctuation
        "name space",  # space
    ],
)
def test_username_invalid_cases(iv, bad):
    with pytest.raises(ValueError):
        iv.validate_username_requirements(bad)


# ----------------------------------------------------------------------
# validate_password_requirements ----------------------------------------
# ----------------------------------------------------------------------
GOOD_PW = "Abcdef1!Ghij"  # 12 chars, upper, lower, digit, special


def test_password_valid(iv):
    assert iv.validate_password_requirements(GOOD_PW) == GOOD_PW


@pytest.mark.parametrize(
    "bad",
    [
        "Short1!",  # <12
        "alllowercase1!",  # no upper
        "ALLUPPERCASE1!",  # no lower
        "NoDigits!!!!",  # no digit
        "NoSpecial1234",  # no special
        "InvalidØChar1!",  # non-ASCII char
    ],
)
def test_password_invalid_cases(iv, bad):
    with pytest.raises(ValueError):
        iv.validate_password_requirements(bad)
