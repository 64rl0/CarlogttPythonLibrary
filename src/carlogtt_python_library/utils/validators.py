# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/validators.py
# Created 10/2/23 - 9:25 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module provides a set of functions and utilities for data
validation. It offers various validators to ensure the correctness and
integrity of different types of data inputs.
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
import re
import string
import warnings

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'InputValidator',
    # Deprecated
    'validate_non_empty_strings',
    'validate_username_requirements',
    'validate_password_requirements',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class InputValidator:
    """
    A collection of input validation methods for strings, usernames,
    and passwords. All methods raise ValueError on invalid inputs.
    """

    def validate_non_empty_strings(self, **strings: str) -> dict[str, str]:
        """
        Return a non-empty string without whitespace at the beginning
        and end of the string.
        """

        strings_validated = {}

        for string_name, string_value in strings.items():
            if string_value:
                string_value = string_value.strip()

                # Match any non-whitespace character
                pattern = r'\S'
                non_whitespace_character_found = bool(re.search(pattern, string_value))

                if non_whitespace_character_found:
                    strings_validated[string_name] = string_value

                else:
                    raise ValueError(f"{string_name!r} cannot be empty.")

        return strings_validated

    def validate_username_requirements(self, username_to_validate: str) -> str:
        """
        Check if username requirements are met and return a non-empty
        string without whitespace at the beginning and end of the
        string.
        """

        if not username_to_validate:
            raise ValueError("Username cannot be empty")

        else:
            username = username_to_validate.strip()

            for ch in username:
                if not ch.isalnum():
                    raise ValueError("Username contains invalid characters.")

            if len(username) < 5 or len(username) > 16:
                raise ValueError(
                    "Username must be at least 5 characters and maximum 16 characters long."
                )

        return username

    def validate_password_requirements(self, password_to_validate: str) -> str:
        """
        Check if password requirements are met and return a non-empty
        string without whitespace at the beginning and end of the
        string.
        """

        if not password_to_validate:
            raise ValueError("Password cannot be empty.")

        else:
            password = password_to_validate.strip()

            if len(password) < 12:
                raise ValueError("Password must be at least 12 characters long.")

            magic_string_check = {"lower": 0, "upper": 0, "digit": 0, "special": 0}

            for ch in password:
                if ch in string.ascii_lowercase:
                    magic_string_check['lower'] += 1

                elif ch in string.ascii_uppercase:
                    magic_string_check['upper'] += 1

                elif ch in string.digits:
                    magic_string_check['digit'] += 1

                elif ch in string.punctuation:
                    magic_string_check['special'] += 1

                else:
                    raise ValueError(f"Password contains invalid character: {ch!r}")

            for i in magic_string_check.values():
                if i == 0:
                    raise ValueError("Password does not meet the minimum requirements.")

        return password


def validate_non_empty_strings(**strings: str) -> dict[str, str]:
    """
    Return a non-empty string without whitespace at the beginning and
    end of the string.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{validate_non_empty_strings.__name__}' is deprecated. Use the parent class"
        f" '{InputValidator.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    strings_validated = {}

    for string_name, string_value in strings.items():
        if string_value:
            string_value = string_value.strip()

            # Match any non-whitespace character
            pattern = r'\S'
            non_whitespace_character_found = bool(re.search(pattern, string_value))

            if non_whitespace_character_found:
                strings_validated[string_name] = string_value

            else:
                raise ValueError(f"{string_name!r} cannot be empty.")

    return strings_validated


def validate_username_requirements(username_to_validate: str) -> str:
    """
    Check if username requirements are met and return a non-empty
    string without whitespace at the beginning and end of the string.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{validate_username_requirements.__name__}' is deprecated. Use the parent"
        f" class '{InputValidator.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    if not username_to_validate:
        raise ValueError("Username cannot be empty")

    else:
        username = username_to_validate.strip()

        for ch in username:
            if not ch.isalnum():
                raise ValueError("Username contains invalid characters.")

        if len(username) < 5 or len(username) > 16:
            raise ValueError(
                "Username must be at least 5 characters and maximum 16 characters long."
            )

    return username


def validate_password_requirements(password_to_validate: str) -> str:
    """
    Check if password requirements are met and return a non-empty
    string without whitespace at the beginning and end of the string.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{validate_password_requirements.__name__}' is deprecated. Use the parent"
        f" class '{InputValidator.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    if not password_to_validate:
        raise ValueError("Password cannot be empty.")

    else:
        password = password_to_validate.strip()

        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long.")

        magic_string_check = {"lower": 0, "upper": 0, "digit": 0, "special": 0}

        for ch in password:
            if ch in string.ascii_lowercase:
                magic_string_check['lower'] += 1

            elif ch in string.ascii_uppercase:
                magic_string_check['upper'] += 1

            elif ch in string.digits:
                magic_string_check['digit'] += 1

            elif ch in string.punctuation:
                magic_string_check['special'] += 1

            else:
                raise ValueError(f"Password contains invalid character: {ch!r}")

        for i in magic_string_check.values():
            if i == 0:
                raise ValueError("Password does not meet the minimum requirements.")

    return password
