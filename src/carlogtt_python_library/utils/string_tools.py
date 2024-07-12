# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# string_tools.py
# Created 10/2/23 - 9:25 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module contains useful functions to work with strings.
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
import random
import string

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'get_random_string',
    'snake_case',
]


def get_random_string(length: int) -> str:
    secret = string.ascii_letters + string.digits
    return ''.join(random.choice(secret) for _ in range(length))


def snake_case(string_to_normalize: str) -> str:
    """
    Normalize the given string by converting uppercase letters to
    lowercase and replacing whitespaces with underscores. The resulting
    string is stripped of leading and trailing underscores.

    :param string_to_normalize: The original string that needs to be
           normalized.
    :return: The normalized string with all uppercase characters
             converted to lowercase and all whitespaces replaced by
             underscores.
    """

    result: list[str] = []

    for idx, ch in enumerate(string_to_normalize):
        # Replace all whitespaces with underscore
        if ch in string.whitespace:
            ch = "_"

            # if the last char is already an underscore then skip it
            if result and result[-1] == "_":
                continue

        # Check if an underscore is part of the string_to_normalize
        elif ch in ["_", "-"]:
            ch = "_"

            # if the last char is already an underscore then skip it
            if result and result[-1] == "_":
                continue

        # Convert uppercase chars to lowercase
        elif ch in string.ascii_uppercase:
            ch = ch.casefold()

            # if the last char is already an underscore then skip it
            if result and not result[-1] == "_":
                result.append("_")

        result.append(ch)

    # Clean up possible leading and trailing underscores coming from
    # the composition loop
    result_str = "".join(result).strip("_")

    return result_str
