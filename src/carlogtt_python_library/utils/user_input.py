# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/user_input.py
# Created 7/20/23 - 3:12 PM UK Time (London) by carlogtt
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
import logging
import warnings

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'UserPrompter',
    # Deprecated
    'get_user_input_and_validate_int',
    'get_user_input_confirmation_y_n',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class UserPrompter:
    """
    A collection of CLI prompt utilities to get and validate user input.
    """

    def get_user_input_and_validate_int(self, question: str = "Enter a number: ") -> int:
        """
        Request the user for an int
        question = "question as a str"
        """

        while True:
            input_value = input(question)

            try:
                int(input_value)

            except ValueError:
                continue

            else:
                return int(input_value)

    def get_user_input_confirmation_y_n(
        self, question: str = "Continue: (y/n): ", true: str = "y", false: str = "n"
    ) -> bool:
        """
        Request the user for a confirmation to continue
        question = "question as a str"
        true = "character to be used as continue"
        false = "character to be used to stop"
        """

        while True:
            input_value = input(question)

            if true.isalpha() and false.isalpha():
                if true.islower() and false.islower():
                    if input_value[0].lower() == true or input_value[0].lower() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

                elif true.isupper() and false.isupper():
                    if input_value[0].upper() == true or input_value[0].upper() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

                elif true.islower() and false.isupper():
                    if input_value[0].lower() == true or input_value[0].upper() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

                elif true.isupper() and false.islower():
                    if input_value[0].upper() == true or input_value[0].lower() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

            elif true.isalpha():
                if true.islower():
                    if input_value[0].lower() == true or input_value[0] == false:
                        if input_value == true:
                            return True

                        else:
                            return False

                elif true.isupper():
                    if input_value[0].upper() == true or input_value[0] == false:
                        if input_value == true:
                            return True

                        else:
                            return False

            elif false.isalpha():
                if false.islower():
                    if input_value[0] == true or input_value[0].lower() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

                elif false.isupper():
                    if input_value[0] == true or input_value[0].upper() == false:
                        if input_value == true:
                            return True

                        else:
                            return False

            else:
                if input_value[0] == true or input_value[0] == false:
                    if input_value == true:
                        return True

                    else:
                        return False


def get_user_input_and_validate_int(question: str = "Enter a number: ") -> int:
    """
    Request the user for an int
    question = "question as a str"
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{get_user_input_and_validate_int.__name__}' is deprecated. Use the parent"
        f" class '{UserPrompter.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    while True:
        input_value = input(question)

        try:
            int(input_value)

        except ValueError:
            continue

        else:
            return int(input_value)


def get_user_input_confirmation_y_n(
    question: str = "Continue: (y/n): ", true: str = "y", false: str = "n"
) -> bool:
    """
    Request the user for a confirmation to continue
    question = "question as a str"
    true = "character to be used as continue"
    false = "character to be used to stop"
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{get_user_input_confirmation_y_n.__name__}' is deprecated. Use the parent"
        f" class '{UserPrompter.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    while True:
        input_value = input(question)

        if true.isalpha() and false.isalpha():
            if true.islower() and false.islower():
                if input_value[0].lower() == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper() and false.isupper():
                if input_value[0].upper() == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.islower() and false.isupper():
                if input_value[0].lower() == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper() and false.islower():
                if input_value[0].upper() == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        elif true.isalpha():
            if true.islower():
                if input_value[0].lower() == true or input_value[0] == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper():
                if input_value[0].upper() == true or input_value[0] == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        elif false.isalpha():
            if false.islower():
                if input_value[0] == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif false.isupper():
                if input_value[0] == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        else:
            if input_value[0] == true or input_value[0] == false:
                if input_value == true:
                    return True

                else:
                    return False
