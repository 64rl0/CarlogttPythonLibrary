# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# phone_tool.py
# Created 8/31/23 - 8:39 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import json

# Third Party Library Imports
import requests
import requests_midway  # type: ignore

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'phone_tool_lookup',
]


def phone_tool_lookup(alias: str) -> dict[str, str]:
    """
    This function will retrieve the Phone Tool user data based on the
    user alias.

    :param alias: The Amazon user alias used to look up on Phone Tool.
    :return: All the data available in Phone Tool inside a dictionary.
    """

    try:
        response = requests.get(
            url=f"https://phonetool.amazon.com/users/{alias}.json",
            auth=requests_midway.RequestsMidway(),
        )

    except requests_midway.requests_midway.RequestsMidwayException as e:
        return {'RequestsMidwayException raised:': str(e)}

    if response.ok:
        json_data = json.loads(response.text)

    else:
        json_data = {'error_code': str(response.status_code)}

    return json_data
