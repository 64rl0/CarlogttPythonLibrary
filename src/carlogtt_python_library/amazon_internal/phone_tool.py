# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/phone_tool.py
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
import logging
import warnings

# Third Party Library Imports
import requests
import requests_midway

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'PhoneTool',
    # Deprecated
    'phone_tool_lookup',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class PhoneTool:
    """
    A handler class for the PhoneTool API.
    """

    def phone_tool_lookup(self, alias: str) -> dict[str, str]:
        """
        This function will retrieve the Phone Tool user data based on
        the user alias.

        :param alias: The Amazon user alias used to look up on Phone
            Tool.
        :return: All the data available in Phone Tool inside a
            dictionary.
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
            json_data = {'error': response.text}

        return json_data


def phone_tool_lookup(alias: str) -> dict[str, str]:
    """
    This function will retrieve the Phone Tool user data based on the
    user alias.

    :param alias: The Amazon user alias used to look up on Phone Tool.
    :return: All the data available in Phone Tool inside a dictionary.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{phone_tool_lookup.__name__}' is deprecated. Use the parent"
        f" class '{PhoneTool.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

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
