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
import sys
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
@patch("carlogtt_python_library.amazon_internal.midway.RequestsMidway")
@patch("carlogtt_python_library.amazon_internal.midway.requests.get")
def test_extract_valid_cookies_success(mock_get, mock_auth, midway_utils):
    mock_response = MagicMock()
    mock_response.cookies.items.return_value = {"cookie_name": "cookie_value"}.items()
    mock_get.return_value = mock_response

    cookies = midway_utils.extract_valid_cookies()
    assert cookies == {"cookie_name": "cookie_value"}
    mock_get.assert_called_once_with(
        "https://midway-auth.amazon.com/robots.txt", auth=mock_auth.return_value, timeout=10
    )


@patch("carlogtt_python_library.amazon_internal.midway.RequestsMidway")
@patch("carlogtt_python_library.amazon_internal.midway.requests.get")
def test_extract_valid_cookies_multiple_cookies(mock_get, mock_auth, midway_utils):
    mock_response = MagicMock()
    mock_response.cookies.items.return_value = {
        "cookie1": "value1",
        "cookie2": "value2",
    }.items()
    mock_get.return_value = mock_response

    cookies = midway_utils.extract_valid_cookies()
    assert cookies == {"cookie1": "value1", "cookie2": "value2"}


@patch("carlogtt_python_library.amazon_internal.midway.RequestsMidway")
@patch("carlogtt_python_library.amazon_internal.midway.requests.get")
def test_extract_valid_cookies_reuses_auth(mock_get, mock_auth, midway_utils):
    mock_response = MagicMock()
    mock_response.cookies.items.return_value = {"cookie_name": "cookie_value"}.items()
    mock_get.return_value = mock_response

    midway_utils.extract_valid_cookies()
    midway_utils.extract_valid_cookies()

    # RequestsMidway is expensive; it must be created once and reused.
    mock_auth.assert_called_once()


@patch("carlogtt_python_library.amazon_internal.midway.RequestsMidway")
@patch("carlogtt_python_library.amazon_internal.midway.requests.get")
def test_extract_valid_cookies_no_valid_cookies(mock_get, mock_auth, midway_utils):
    mock_response = MagicMock()
    mock_response.cookies.items.return_value = {}.items()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="No valid cookies found"):
        midway_utils.extract_valid_cookies()


@patch("carlogtt_python_library.amazon_internal.midway.RequestsMidway")
@patch("carlogtt_python_library.amazon_internal.midway.requests.get")
def test_extract_valid_cookies_deprecation_warning(mock_get, mock_auth, midway_utils):
    mock_response = MagicMock()
    mock_response.cookies.items.return_value = {"cookie_name": "cookie_value"}.items()
    mock_get.return_value = mock_response

    with pytest.warns(DeprecationWarning, match="extract_valid_cookies"):
        midway_utils.extract_valid_cookies()


# ----------------------------------------------------------------------
# Tests for validate_midway_session (MCS integration)
# ----------------------------------------------------------------------
@patch('midway_client_suite_library_python.mcs_lib.McsLib')
def test_validate_midway_session_valid(mock_mcs_lib_cls, midway_utils):
    """Test validate_midway_session returns True when session is not expired."""
    # Setup mocks
    mock_result = MagicMock()
    mock_result.is_expired = False

    mock_mcs_instance = MagicMock()
    mock_mcs_instance.get_session_token_expiration.return_value = mock_result
    mock_mcs_lib_cls.return_value = mock_mcs_instance

    # Test
    result = midway_utils.validate_midway_session()

    # Verify
    assert result is True
    mock_mcs_lib_cls.assert_called_once()
    mock_mcs_instance.get_session_token_expiration.assert_called_once_with("midway-auth.amazon.com")


@patch('midway_client_suite_library_python.mcs_lib.McsLib')
def test_validate_midway_session_expired(mock_mcs_lib_cls, midway_utils):
    """Test validate_midway_session returns False when session is expired."""
    # Setup mocks
    mock_result = MagicMock()
    mock_result.is_expired = True

    mock_mcs_instance = MagicMock()
    mock_mcs_instance.get_session_token_expiration.return_value = mock_result
    mock_mcs_lib_cls.return_value = mock_mcs_instance

    # Test
    result = midway_utils.validate_midway_session()

    # Verify
    assert result is False
    mock_mcs_lib_cls.assert_called_once()
    mock_mcs_instance.get_session_token_expiration.assert_called_once_with("midway-auth.amazon.com")


def test_validate_midway_session_import_error(midway_utils):
    """Test validate_midway_session exits when MCS library is not available."""
    # Mock the import to raise ImportError
    with patch.dict(sys.modules, {'midway_client_suite_library_python.mcs_lib': None}):
        with pytest.raises(SystemExit) as exc_info:
            midway_utils.validate_midway_session()
        assert exc_info.value.code == 1
