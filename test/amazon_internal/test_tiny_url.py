# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_tiny_url.py
# Created 4/27/25 - 6:18 PM UK Time (London) by carlogtt

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
from unittest.mock import MagicMock, Mock, patch

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
def amazon_tiny_url():
    from carlogtt_python_library.amazon_internal.tiny_url import AmazonTinyUrl

    return AmazonTinyUrl()


# ----------------------------------------------------------------------
# Tests for create_amazon_tiny_url with MCS
# ----------------------------------------------------------------------
@patch('carlogtt_python_library.amazon_internal.tiny_url.requests.post')
def test_create_amazon_tiny_url_success(mock_post, amazon_tiny_url):
    # Setup mocks
    mock_response = Mock()
    mock_response.json.return_value = {'short_url': 'https://tiny.amazon.com/abc123'}
    mock_post.return_value = mock_response

    # Test
    result = amazon_tiny_url.create_amazon_tiny_url('https://example.amazon.com/very/long/url')

    # Verify
    assert result == 'https://tiny.amazon.com/abc123'
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert 'auth' in call_kwargs
    assert call_kwargs['url'] == 'https://tiny.amazon.com/submit/url'


@patch('carlogtt_python_library.amazon_internal.tiny_url.requests.post')
def test_create_amazon_tiny_url_missing_short_url(mock_post, amazon_tiny_url):
    # Setup mocks
    mock_response = Mock()
    mock_response.json.return_value = {'error': 'Invalid URL'}
    mock_post.return_value = mock_response

    # Test
    result = amazon_tiny_url.create_amazon_tiny_url('https://example.amazon.com')

    # Verify empty string returned on KeyError
    assert result == ""


@patch('carlogtt_python_library.amazon_internal.tiny_url.requests.post')
def test_create_amazon_tiny_url_auth_reuse(mock_post, amazon_tiny_url):
    # Setup mocks
    mock_response = Mock()
    mock_response.json.return_value = {'short_url': 'https://tiny.amazon.com/abc'}
    mock_post.return_value = mock_response

    # Make multiple calls
    amazon_tiny_url.create_amazon_tiny_url('https://example1.amazon.com')
    amazon_tiny_url.create_amazon_tiny_url('https://example2.amazon.com')

    # Verify RequestsMidway only instantiated once (auth object reused)
    # We can't directly check instantiation, but we verify both calls happened
    assert mock_post.call_count == 2
