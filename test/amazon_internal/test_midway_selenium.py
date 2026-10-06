# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_midway_selenium.py
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


# ----------------------------------------------------------------------
# Tests for MidwaySeleniumDriver with MCS
# ----------------------------------------------------------------------
@patch('carlogtt_python_library.amazon_internal.midway_selenium.requests.get')
def test_midway_selenium_driver_init(mock_get):
    from carlogtt_python_library.amazon_internal.midway_selenium import (
        MidwaySeleniumDriver,
    )

    # Setup mocks
    mock_response = Mock()
    mock_cookies = {'midway-auth': 'test-token', 'session-id': '12345'}
    mock_response.cookies.items.return_value = mock_cookies.items()
    mock_get.return_value = mock_response

    mock_driver = Mock()

    # Test - RequestsMidway will try to instantiate, but requests.get is mocked
    selenium_driver = MidwaySeleniumDriver(mock_driver)

    # Verify
    assert selenium_driver.driver == mock_driver
    mock_driver.get.assert_called_once_with("https://midway-auth.amazon.com/robots.txt")
    assert mock_driver.add_cookie.call_count == 2


@patch('carlogtt_python_library.amazon_internal.midway_selenium.requests.get')
@patch('carlogtt_python_library.amazon_internal.midway_selenium.selenium.webdriver.Chrome')
def test_get_selenium_driver_headless(mock_chrome_cls, mock_get):
    from carlogtt_python_library.amazon_internal.midway_selenium import (
        MidwaySeleniumDriver,
    )

    # Setup mocks
    mock_response = Mock()
    mock_response.cookies.items.return_value = []
    mock_get.return_value = mock_response

    mock_driver = Mock()
    mock_chrome_cls.return_value = mock_driver

    # Test
    result = MidwaySeleniumDriver.get_selenium_driver(headless=True)

    # Verify
    assert isinstance(result, MidwaySeleniumDriver)
    mock_driver.set_page_load_timeout.assert_called_once_with(60)


@patch('carlogtt_python_library.amazon_internal.midway_selenium.requests.get')
@patch('carlogtt_python_library.amazon_internal.midway_selenium.selenium.webdriver.Chrome')
def test_get_selenium_driver_not_headless(mock_chrome_cls, mock_get):
    from carlogtt_python_library.amazon_internal.midway_selenium import (
        MidwaySeleniumDriver,
    )

    # Setup mocks
    mock_response = Mock()
    mock_response.cookies.items.return_value = []
    mock_get.return_value = mock_response

    mock_driver = Mock()
    mock_chrome_cls.return_value = mock_driver

    # Test
    result = MidwaySeleniumDriver.get_selenium_driver(headless=False)

    # Verify
    assert isinstance(result, MidwaySeleniumDriver)


@patch('carlogtt_python_library.amazon_internal.midway_selenium.requests.get')
@patch(
    'carlogtt_python_library.amazon_internal.midway_selenium.MidwaySeleniumDriver._authenticate_midway'
)
def test_get_midway_cookies(mock_auth, mock_get):
    from carlogtt_python_library.amazon_internal.midway_selenium import (
        MidwaySeleniumDriver,
    )

    # Setup mocks
    mock_response = Mock()
    mock_cookies = {'midway-auth': 'token123', 'session-id': 'sess456', 'csrf-token': 'csrf789'}
    mock_response.cookies.items.return_value = mock_cookies.items()
    mock_get.return_value = mock_response

    mock_driver = Mock()

    # Test - mock _authenticate_midway to avoid the call during __init__
    selenium_driver = MidwaySeleniumDriver(mock_driver)
    cookies = selenium_driver._get_midway_cookies()

    # Verify
    assert len(cookies) == 3
    cookie_names = [c['name'] for c in cookies]
    assert 'midway-auth' in cookie_names
    assert 'session-id' in cookie_names
    assert 'csrf-token' in cookie_names
    mock_get.assert_called_once()
