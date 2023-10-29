# MODULE NAME
# validators.py

"""
This module provides a set of functions and utilities for data
validation. It offers various validators to ensure the correctness and
integrity of different types of data inputs.
"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import datetime
import logging
import re
import string

# Local Folder (Relative) Imports
from . import encryption

# END IMPORTS


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


def validate_non_empty_strings(**strings: str) -> dict[str, str]:
    """
    Return a non-empty string without whitespace at the beginning and
    end of the string.
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


def validate_username_requirements(username_to_validate: str) -> str:
    """
    Check if username requirements are met and return a non-empty
    string without whitespace at the beginning and end of the string.
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


def validate_password_requirements(password_to_validate: str) -> str:
    """
    Check if password requirements are met and return a non-empty
    string without whitespace at the beginning and end of the string.
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


def validate_reset_code_match(
    hashed_reset_code: bytes,
    reset_code_user_input: str,
    reset_code_expiry: datetime.datetime,
    fernet_key: str,
) -> bool:
    """validate_reset_code_match"""

    if hashed_reset_code and reset_code_expiry:
        now = datetime.datetime.utcnow()

        if now < reset_code_expiry:
            return encryption.validate_hash_match(
                reset_code_user_input, hashed_reset_code, fernet_key
            )

    return False
