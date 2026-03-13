# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/utils/string_tools.py
# Created 10/2/23 - 9:25 AM UK Time (London) by carlogtt

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
import logging
import random
import re
import string
import warnings

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'StringUtils',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class StringUtils:
    """
    A collection of string utility functions including string
    normalization and random string generation.
    """

    def get_random_string(self, length: int) -> str:
        """
        Generate a random string.
        """

        secret = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(secret) for _ in range(length))

        return random_string

    def snake_case(self, string_to_normalize: str) -> str:
        """
        Normalize the given string by converting uppercase letters to
        lowercase and replacing whitespaces with underscores. The
        resulting string is stripped of leading and trailing
        underscores.

        :param string_to_normalize: The original string that needs to be
               normalized.
        :return: The normalized string with all uppercase characters
                 converted to lowercase and all whitespaces replaced by
                 underscores.
        """

        msg = (
            f"[DEPRECATED] '{self.snake_case.__name__}' is deprecated in Class"
            f" '{self.__class__.__name__}'. Use the new method '{self.snake_case_v2.__name__}()'"
            " instead."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=3)
        module_logger.warning(msg)

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

    def snake_case_v2(self, string_to_normalize: str) -> str:
        """
        Normalize the given string to snake_case by handling consecutive
        uppercase letters, digit boundaries, whitespaces, hyphens,
        and underscores.

        :param string_to_normalize: The original string that needs to be
               normalized.
        :return: The normalized snake_case string.
        """

        result = string_to_normalize

        # Replace whitespace and hyphens with underscores
        result = re.sub(r'[\s\-]+', '_', result)

        # Collapse multiple underscores
        result = re.sub(r'_+', '_', result)

        # Insert underscore between lowercase/digit and uppercase
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', result)

        # Insert underscore between consecutive uppercase and
        # uppercase followed by lowercase
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', result)

        # Insert underscore between letter and digit
        result = re.sub(r'([a-zA-Z])(\d)', r'\1_\2', result)

        # Insert underscore between digit and letter
        result = re.sub(r'(\d)([a-zA-Z])', r'\1_\2', result)

        # Convert to lowercase
        result = result.casefold()

        return result
