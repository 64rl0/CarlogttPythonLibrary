# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_phone_tool.py
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
from unittest.mock import Mock, patch

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
def phone_tool():
    from carlogtt_python_library.amazon_internal.phone_tool import PhoneTool

    return PhoneTool()


# ----------------------------------------------------------------------
# Tests for phone_tool_lookup (already uses RequestsMidway)
# ----------------------------------------------------------------------
@patch('carlogtt_python_library.amazon_internal.phone_tool.requests_midway')
@patch('carlogtt_python_library.amazon_internal.phone_tool.requests.get')
def test_phone_tool_lookup_success(mock_get, mock_midway, phone_tool):
    # Setup mocks
    mock_response = Mock()
    mock_response.ok = True
    mock_response.text = '{"name": "Test User", "alias": "testuser"}'
    mock_get.return_value = mock_response

    # Test
    result = phone_tool.phone_tool_lookup('testuser')

    # Verify
    assert result == {"name": "Test User", "alias": "testuser"}
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args[1]
    assert 'auth' in call_kwargs


@patch('carlogtt_python_library.amazon_internal.phone_tool.requests_midway')
@patch('carlogtt_python_library.amazon_internal.phone_tool.requests.get')
def test_phone_tool_lookup_error_response(mock_get, mock_midway, phone_tool):
    # Setup mocks
    mock_response = Mock()
    mock_response.ok = False
    mock_response.text = 'User not found'
    mock_get.return_value = mock_response

    # Test
    result = phone_tool.phone_tool_lookup('nonexistent')

    # Verify
    assert result == {'error': 'User not found'}
