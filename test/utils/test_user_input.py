# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_user_input.py
# Created 4/25/25 - 10:31 PM UK Time (London) by carlogtt
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
import builtins
import itertools

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
# Helpers
# ----------------------------------------------------------------------
def feed_inputs(monkeypatch, answers):
    """
    Patch builtins.input so each call returns the next item in *answers*.
    """
    gen = itertools.chain(answers)

    monkeypatch.setattr(builtins, "input", lambda _: next(gen))


# ----------------------------------------------------------------------
# get_user_input_and_validate_int
# ----------------------------------------------------------------------
def test_get_user_input_and_validate_int_accepts_first_int(monkeypatch):
    import carlogtt_python_library as mylib

    feed_inputs(monkeypatch, ["42"])
    assert mylib.UserPrompter().get_user_input_and_validate_int() == 42


def test_get_user_input_and_validate_int_loops_until_valid(monkeypatch):
    import carlogtt_python_library as mylib

    # first two answers are not integers, third is valid
    feed_inputs(monkeypatch, ["banana", "3.14", "-7"])
    assert mylib.UserPrompter().get_user_input_and_validate_int() == -7


# ----------------------------------------------------------------------
# get_user_input_confirmation_y_n – default 'y' / 'n'
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "answer,expected",
    [
        ("y", True),
        ("n", False),
        ("Y", True),
        ("N", False),
    ],
)
def test_confirmation_default(monkeypatch, answer, expected):
    import carlogtt_python_library as mylib

    feed_inputs(monkeypatch, [answer])
    assert mylib.UserPrompter().get_user_input_confirmation_y_n() is expected


def test_confirmation_default_reprompts(monkeypatch):
    import carlogtt_python_library as mylib

    # first answer invalid -> loop, second valid
    feed_inputs(monkeypatch, ["maybe", "n"])
    assert mylib.UserPrompter().get_user_input_confirmation_y_n() is False


# ----------------------------------------------------------------------
# get_user_input_confirmation_y_n – custom tokens
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "true_token,false_token,answer,expected",
    [
        ("1", "0", "1", True),
        ("1", "0", "0", False),
        ("Y", "Z", "Y", True),
        ("Y", "Z", "Z", False),
        ("yes", "quit", "yes", True),
        ("yes", "quit", "quit", False),
    ],
)
def test_confirmation_custom_tokens(monkeypatch, true_token, false_token, answer, expected):
    import carlogtt_python_library as mylib

    feed_inputs(monkeypatch, [answer])
    assert (
        mylib.UserPrompter().get_user_input_confirmation_y_n(true=true_token, false=false_token)
        is expected
    )


def test_confirmation_custom_tokens_reprompt(monkeypatch):
    import carlogtt_python_library as mylib

    # wrong answer first, then correct custom token
    feed_inputs(monkeypatch, ["maybe", "quit"])
    assert mylib.UserPrompter().get_user_input_confirmation_y_n(true="go", false="quit") is False
