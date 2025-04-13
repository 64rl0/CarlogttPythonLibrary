# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/midway_selenium.py
# Created 12/11/23 - 9:48 AM UK Time (London) by carlogtt
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
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Special Imports
from __future__ import annotations

# Standard Library Imports
import logging
import os
import pathlib
import re
import time
from typing import Union

# Third Party Library Imports
import selenium.webdriver.chrome.options

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
    :param cookie_filepath: Optional; the filepath to the Midway
           authentication cookies file. If not provided, the class
           looks for the cookie file in the default location
           `~/.midway/cookie`.
    """

    def __init__(self, driver: WebDriver, cookie_filepath: str = "") -> None:
        self.driver = driver
        self._cookie_filepath = cookie_filepath
        self._authenticate_midway()

    @classmethod
    def get_selenium_driver(
        cls, headless: bool = True, cookie_filepath: str = ""
    ) -> MidwaySeleniumDriver:
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

        return cls(chrome_driver, cookie_filepath)

    def _authenticate_midway(self) -> None:
        """
        Gets `url` handling **midway** authentication.
        Relies on the midway cookies stored in the home directory.

        :return: None
        """

        self.driver.get("https://midway-auth.amazon.com/robots.txt")

        for cookie in self._get_midway_cookies():
            self.driver.add_cookie(cookie)

    def _get_midway_cookies(self) -> list[dict[str, str]]:
        """
        Gets the cookies from file in home directory.
        See https://curl.se/docs/http-cookies.html

        :return: the cookies as list
        """

        if self._cookie_filepath == "":
            home_path = pathlib.Path.home()
            cookies_file = os.path.join(home_path, ".midway", "cookie")

        else:
            cookies_file = self._cookie_filepath

        cookies = []

        with open(cookies_file) as f:
            for line in f:
                if line.startswith("#") and not re.search("^#Http", line):
                    continue

                fields = line.split()

                if len(fields) != 7:
                    continue

                expire = int(fields[4])

                if round(time.time()) > expire:
                    raise ValueError("Midway cookie is expired. Run `mwinit`", self.driver)

                cookies.append({"name": fields[5], "value": fields[6]})

        return cookies
