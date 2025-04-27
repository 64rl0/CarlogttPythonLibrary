# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/logger/test_app_logger.py
# Created 4/27/25 - 12:55 PM UK Time (London) by carlogtt
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
import io
import logging
import pathlib

# Third Party Library Imports
import pytest

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


# ----------------------------------------------------------------------
# 1.  Validation errors
# ----------------------------------------------------------------------
def test_invalid_colour_raises():
    with pytest.raises(mylib.LoggerError):
        mylib.Logger("x", "INFO", log_color="not_a_colour")


def test_invalid_level_string_raises():
    with pytest.raises(mylib.LoggerError):
        mylib.Logger("x", "NOT_A_LEVEL")


# ----------------------------------------------------------------------
# 2.  Handler basics — StringIO
# ----------------------------------------------------------------------
def test_stringio_handler_captures_output():
    sio = io.StringIO()
    lg = mylib.Logger("demo", "INFO", log_color="yellow")
    lg.add_stringio_handler(sio)

    lg.app_logger.info("hello world")
    captured = sio.getvalue()

    assert "hello world" in captured  # message appears
    # colour codes wrapped by CLIStyle
    assert mylib.CLIStyle.CLI_YELLOW in captured
    assert captured.rstrip().endswith(mylib.CLIStyle.CLI_END)


# ----------------------------------------------------------------------
# 3.  change_logger_level updates logger + handlers
# ----------------------------------------------------------------------
def test_change_level_propagates_to_handlers():
    sio = io.StringIO()
    lg = mylib.Logger("lvl", "INFO")
    lg.add_stringio_handler(sio)

    lg.app_logger.debug("not-visible")  # below INFO
    lg.change_logger_level("DEBUG")  # lower threshold
    lg.app_logger.debug("now visible!")

    assert "now visible!" in sio.getvalue()
    assert "not-visible" not in sio.getvalue()


# ----------------------------------------------------------------------
# 4.  File handler (uses pytest tmp_path)
# ----------------------------------------------------------------------
def test_file_handler_writes(tmp_path: pathlib.Path):
    log_path = tmp_path / "app.log"
    lg = mylib.Logger("file", mylib.LoggerLevel.INFO)
    lg.add_file_handler(log_path)

    lg.app_logger.error("saved!")

    text = log_path.read_text()
    assert "saved!" in text


# ----------------------------------------------------------------------
# 5.  Console handler to an arbitrary stream
# ----------------------------------------------------------------------
def test_console_handler_custom_stream():
    buf = io.StringIO()
    lg = mylib.Logger("con", "INFO", log_color="cyan")
    lg.add_console_handler(buf)  # stream instead of sys.stderr

    lg.app_logger.warning("watch me")
    assert "watch me" in buf.getvalue()


# ----------------------------------------------------------------------
# 6.  attach_root_logger / detach_root_logger
# ----------------------------------------------------------------------
def test_attach_and_detach_root_logger():
    stream = io.StringIO()
    lg = mylib.Logger("rooty", "INFO")
    lg.add_console_handler(stream)

    # attach – calls to logging.* go through our handler
    lg.attach_root_logger()
    logging.info("from-root")
    assert "from-root" in stream.getvalue()

    # detach – lower root level to WARNING (default)
    stream.truncate(0)
    stream.seek(0)
    lg.detach_root_logger()
    logging.info("should-be-filtered")
    assert stream.getvalue() == ""


# ----------------------------------------------------------------------
# 7.  Child logger inherits formatting
# ----------------------------------------------------------------------
def test_get_child_logger_inherits_parent_formatter():
    buf = io.StringIO()
    parent = mylib.Logger("parent", "INFO", log_color="green")
    parent.add_stringio_handler(buf)

    child = parent.get_child_logger("child")
    child.info("hi!")

    out = buf.getvalue()
    assert "hi!" in out
