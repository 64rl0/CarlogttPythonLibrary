# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_midway.py
# Created 4/27/25 - 1:30 PM UK Time (London) by carlogtt
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
import os
import tempfile
import time
from unittest.mock import MagicMock, patch

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


@pytest.fixture
def midway_utils():
    from carlogtt_python_library.amazon_internal.midway import MidwayUtils

    return MidwayUtils()


# ----------------------------------------------------------------------
# Tests for cli_midway_auth
# ----------------------------------------------------------------------
def test_cli_midway_auth_success(midway_utils):
    mock_process = MagicMock()
    mock_process.returncode = 0

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        midway_utils.cli_midway_auth()
        mock_popen.assert_called_once_with(["mwinit", "-s"])
        mock_process.wait.assert_called_once()


def test_cli_midway_auth_custom_options(midway_utils):
    mock_process = MagicMock()
    mock_process.returncode = 0

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        midway_utils.cli_midway_auth(options="-s -o")
        mock_popen.assert_called_once_with(["mwinit", "-s", "-o"])


def test_cli_midway_auth_no_options(midway_utils):
    mock_process = MagicMock()
    mock_process.returncode = 0

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        midway_utils.cli_midway_auth(options="")
        mock_popen.assert_called_once_with(["mwinit"])


def test_cli_midway_auth_retry_then_success(midway_utils):
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process_success = MagicMock()
    mock_process_success.returncode = 0

    with patch("subprocess.Popen", side_effect=[mock_process, mock_process_success]) as mock_popen:
        midway_utils.cli_midway_auth(max_retries=2)
        assert mock_popen.call_count == 2


def test_cli_midway_auth_all_retries_fail(midway_utils):
    mock_process = MagicMock()
    mock_process.returncode = 1

    with patch("subprocess.Popen", return_value=mock_process):
        with pytest.raises(SystemExit) as exc_info:
            midway_utils.cli_midway_auth(max_retries=2)
        assert exc_info.value.code == 1


def test_cli_midway_auth_command_not_found(midway_utils):
    with patch("subprocess.Popen", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as exc_info:
            midway_utils.cli_midway_auth()
        assert exc_info.value.code == 1


# ----------------------------------------------------------------------
# Tests for extract_valid_cookies
# ----------------------------------------------------------------------
def test_extract_valid_cookies_success(midway_utils):
    future_time = str(int(time.time()) + 3600)
    cookie_content = (
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tcookie_name\tcookie_value\n"
    )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        cookies = midway_utils.extract_valid_cookies(temp_path)
        assert cookies == {"cookie_name": "cookie_value"}
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_multiple_cookies(midway_utils):
    future_time = str(int(time.time()) + 3600)
    cookie_content = (
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tcookie1\tvalue1\n"
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tcookie2\tvalue2\n"
    )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        cookies = midway_utils.extract_valid_cookies(temp_path)
        assert cookies == {"cookie1": "value1", "cookie2": "value2"}
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_expired_cookie(midway_utils):
    past_time = str(int(time.time()) - 3600)
    future_time = str(int(time.time()) + 3600)
    cookie_content = (
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{past_time}\texpired\tvalue\n"
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tvalid\tvalue\n"
    )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        cookies = midway_utils.extract_valid_cookies(temp_path)
        assert cookies == {"valid": "value"}
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_skip_non_http_lines(midway_utils):
    future_time = str(int(time.time()) + 3600)
    cookie_content = (
        "# Comment line\n"
        "some random text\n"
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tcookie_name\tcookie_value\n"
    )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        cookies = midway_utils.extract_valid_cookies(temp_path)
        assert cookies == {"cookie_name": "cookie_value"}
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_skip_malformed_lines(midway_utils):
    future_time = str(int(time.time()) + 3600)
    cookie_content = (
        "#HttpOnly_.amazon.com\tTRUE\t/\n"  # Too few fields
        f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{future_time}\tcookie_name\tcookie_value\n"
    )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        cookies = midway_utils.extract_valid_cookies(temp_path)
        assert cookies == {"cookie_name": "cookie_value"}
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_file_not_found(midway_utils):
    with pytest.raises(ValueError, match="not found"):
        midway_utils.extract_valid_cookies("/nonexistent/path/cookie")


def test_extract_valid_cookies_no_valid_cookies(midway_utils):
    past_time = str(int(time.time()) - 3600)
    cookie_content = f"#HttpOnly_.amazon.com\tTRUE\t/\tTRUE\t{past_time}\texpired\tvalue\n"

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        f.write(cookie_content)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="No valid cookies found"):
            midway_utils.extract_valid_cookies(temp_path)
    finally:
        os.unlink(temp_path)


def test_extract_valid_cookies_empty_file(midway_utils):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cookie') as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="No valid cookies found"):
            midway_utils.extract_valid_cookies(temp_path)
    finally:
        os.unlink(temp_path)
