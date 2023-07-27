# MODULE NAME ----------------------------------------------------------------------------------------------------------
# string_tools.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains useful functions to work with strings.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging
import random
import string

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


def get_random_string(length: int) -> str:
    secret = string.ascii_letters + string.digits
    return ''.join(random.choice(secret) for _ in range(length))


def snake_case(string_to_normalize: str) -> str:
    """
    Normalize the given string by converting uppercase letters to lowercase and replacing whitespaces with underscores.
    The resulting string is stripped of leading and trailing underscores.

    Args:
        string_to_normalize:
            The original string that needs to be normalized.

    Returns:
        The normalized string with all uppercase characters converted to lowercase and all whitespaces replaced by
        underscores.
    """
    result = []

    for idx, ch in enumerate(string_to_normalize):

        # Replace all whitespaces with underscore
        if ch in string.whitespace:
            ch = "_"

            # if the last character is already an underscore then skip it
            if result and result[-1] == "_":
                continue

        # Check if an underscore is part of the string_to_normalize
        elif ch in ["_", "-"]:
            ch = "_"

            # if the last character is already an underscore then skip it
            if result and result[-1] == "_":
                continue

        # Convert uppercase characters to lowercase
        elif ch in string.ascii_uppercase:
            ch = ch.casefold()

            # if the last character is already an underscore then skip it
            if result and not result[-1] == "_":
                result.append("_")

        result.append(ch)

    # Clean up possible leading and trailing underscores coming from the composition loop
    result = "".join(result).strip("_")

    return result


if __name__ == '__main__':
    s = "  Hello __  this i7Is--My Name  "
    print(snake_case(s))
