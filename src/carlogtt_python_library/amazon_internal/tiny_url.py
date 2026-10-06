# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/tiny_url.py
# Created 2/24/24 - 11:31 AM UK Time (London) by carlogtt

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

# Third Party Library Imports
import requests
from requests_midway import RequestsMidway

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'AmazonTinyUrl',
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
        # Lazy initialization to avoid network calls at import time
        self._auth = None

    def _get_auth(self):
        """Get or create the RequestsMidway auth object."""
        if self._auth is None:
            self._auth = RequestsMidway()
        return self._auth

    def create_amazon_tiny_url(self, long_url: str) -> str:
        """
        Create a tiny url.
        Using Amazon backend service https://tiny.amazon.com

        :param long_url: The url to convert to tiny.
        :return: The tiny url for the agenda preview.
        """

        response = requests.post(
            url='https://tiny.amazon.com/submit/url',
            headers={'Accept': 'application/json'},
            params=[('name', long_url), ('opaque', 1)],
            auth=self._get_auth(),
        )

        try:
            tiny_url = response.json()['short_url']

        except KeyError:
            tiny_url = ""

        assert isinstance(tiny_url, str)

        return tiny_url
