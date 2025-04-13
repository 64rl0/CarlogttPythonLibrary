# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/tiny_url.py
# Created 2/24/24 - 11:31 AM UK Time (London) by carlogtt
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

# Standard Library Imports
import logging
import warnings

# Third Party Library Imports
import requests

# Local Folder (Relative) Imports
from . import midway

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'AmazonTinyUrl',
    # Deprecated
    'create_amazon_tiny_url',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class AmazonTinyUrl:
    """
    A handler class for the TinyUrl API.
    """

    def __init__(self):
        self.midway_utils = midway.MidwayUtils()

    def create_amazon_tiny_url(
        self, long_url: str, cookie_filepath: str = "~/.midway/cookie"
    ) -> str:
        """
        Create a tiny url.
        Using Amazon backend service https://tiny.amazon.com

        :param long_url: The url to convert to tiny.
        :param cookie_filepath: The file path to the cookie file.
               Defaults to "~/.midway/cookie".
        :return: The tiny url for the agenda preview.
        """

        cookies = self.midway_utils.extract_valid_cookies(cookie_filepath)

        response = requests.post(
            url='https://tiny.amazon.com/submit/url',
            headers={'Accept': 'application/json'},
            params=[('name', long_url), ('opaque', 1)],
            cookies=cookies,
        )

        try:
            tiny_url = response.json()['short_url']

        except KeyError:
            tiny_url = ""

        return tiny_url


def create_amazon_tiny_url(long_url: str, cookie_filepath: str = "~/.midway/cookie") -> str:
    """
    Create a tiny url.
    Using Amazon backend service https://tiny.amazon.com

    :param long_url: The url to convert to tiny.
    :param cookie_filepath: The file path to the cookie file.
           Defaults to "~/.midway/cookie".
    :return: The tiny url for the agenda preview.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{create_amazon_tiny_url.__name__}' is deprecated. Use the parent"
        f" class '{AmazonTinyUrl.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    cookies = midway.extract_valid_cookies(cookie_filepath)

    response = requests.post(
        url='https://tiny.amazon.com/submit/url',
        headers={'Accept': 'application/json'},
        params=[('name', long_url), ('opaque', 1)],
        cookies=cookies,
    )

    try:
        tiny_url = response.json()['short_url']

    except KeyError:
        tiny_url = ""

    return tiny_url
