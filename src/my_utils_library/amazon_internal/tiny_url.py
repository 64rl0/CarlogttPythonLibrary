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
import re

# Third Party Library Imports
import requests

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'create_amazon_tiny_url',
]

# Setting up logger for current module
# module_logger =

# Type aliases
#


def create_amazon_tiny_url(long_url: str, cookie_filepath: str) -> str:
    """
    Create a tiny url.
    Using Amazon backend service https://tiny.amazon.com

    :param cookie_filepath: The filepath to the midway cookie.
    :param long_url: The url to convert to tiny.
    :return: The tiny url for the agenda preview.
    """

    cookies = {}

    with open(cookie_filepath) as cookie:
        for line in cookie:
            if line.startswith("#") and not re.search("^#Http", line):
                continue

            fields = line.split()

            if len(fields) != 7:
                continue

            cookies.update({fields[5]: fields[6]})

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
