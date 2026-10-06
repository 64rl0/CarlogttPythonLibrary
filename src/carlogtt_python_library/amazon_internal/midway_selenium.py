# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/midway_selenium.py
# Created 12/11/23 - 9:48 AM UK Time (London) by carlogtt

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made code or quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Special Imports
from __future__ import annotations

# Standard Library Imports
import logging
from typing import Optional, Union

# Third Party Library Imports
import requests
import selenium.webdriver.chrome.options
from requests_midway import RequestsMidway

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'MidwaySeleniumDriver',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
WebDriver = Union[
    selenium.webdriver.Firefox,
    selenium.webdriver.Chrome,
    selenium.webdriver.Edge,
    selenium.webdriver.Safari,
]


class MidwaySeleniumDriver:
    """
    Facilitates the creation and management of a Selenium WebDriver that
    is authenticated against the Midway authentication system. This
    class provides methods to obtain a WebDriver instance with Midway
    authentication cookies applied, allowing automated navigation of
    pages that require Midway authentication.

    Use the `get_selenium_driver` class method to obtain an
    authenticated Selenium WebDriver instance, or instantiate this class
    with an existing WebDriver to apply Midway authentication.

    :param driver: An instance of Selenium WebDriver.
    """

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        # Type annotation for mypy: _auth can be None or RequestsMidway
        self._auth: Optional[RequestsMidway] = None
        self._authenticate_midway()

    def _get_auth(self):
        """Get or create the RequestsMidway auth object."""
        if self._auth is None:
            self._auth = RequestsMidway()
        return self._auth

    @classmethod
    def get_selenium_driver(cls, headless: bool = True) -> 'MidwaySeleniumDriver':
        """
        Get a Selenium driver instance.

        :return: a Selenium Chrome driver.
        """

        # set driver options
        options = selenium.webdriver.chrome.options.Options()

        if headless:
            options.add_argument("--headless=new")

        # initiate driver
        chrome_driver = selenium.webdriver.Chrome(options=options)
        chrome_driver.set_page_load_timeout(60)  # seconds

        return cls(chrome_driver)

    def _authenticate_midway(self) -> None:
        """
        Gets `url` handling **midway** authentication.
        Uses RequestsMidway to authenticate with MCS.

        :return: None
        """

        self.driver.get("https://midway-auth.amazon.com/robots.txt")

        for cookie in self._get_midway_cookies():
            self.driver.add_cookie(cookie)

    def _get_midway_cookies(self) -> list[dict[str, str]]:
        """
        Gets the cookies using MCS authentication.

        :return: the cookies as list
        """

        # Use RequestsMidway to make an authenticated request
        response = requests.get("https://midway-auth.amazon.com/robots.txt", auth=self._get_auth())

        # Extract cookies from the response
        cookies = []
        for cookie_name, cookie_value in response.cookies.items():
            cookies.append({"name": cookie_name, "value": cookie_value})

        return cookies
