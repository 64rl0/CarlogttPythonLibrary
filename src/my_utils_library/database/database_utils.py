# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# database_utils.py
# Created 9/25/23 - 1:49 PM UK Time (London) by carlogtt
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
import functools
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Union

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'retry_decorator',
    'sql_query_reader',
]

# Type aliases
OriginalFunction = Callable[..., Any]
InnerFunction = Callable[..., Any]
DecoratorFunction = Callable[[OriginalFunction], InnerFunction]


def retry_decorator(
    exception_to_check: type[Exception],
    tries: int = 4,
    delay_secs: int = 3,
    delay_multiplier: int = 2,
) -> DecoratorFunction:
    """
    Retry calling the decorated function using an exponential backoff
    multiplier.

    :param exception_to_check: the exception to check. may be a tuple
           of exceptions to check
    :param tries: number of times to try (not retry) before giving up
    :param delay_secs: initial delay between retries in seconds
    :param delay_multiplier: delay multiplier e.g. value of 2 will
           double the delay each retry
    """

    def decorator_retry(original_func: OriginalFunction) -> InnerFunction:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            nonlocal tries
            nonlocal delay_secs

            while tries > 1:
                try:
                    return original_func(*args, **kwargs)

                except exception_to_check as e:
                    message = f"{str(e)}, Retrying in {delay_secs} seconds..."

                    # Log error
                    logging.error(message)
                    print(message)

                    time.sleep(delay_secs)
                    tries -= 1
                    delay_secs *= delay_multiplier

            return original_func(*args, **kwargs)

        return inner

    return decorator_retry


def sql_query_reader(file_path: Union[Path, str]) -> str:
    query = Path(file_path).read_text()

    return query
