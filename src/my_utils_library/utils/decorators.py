# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# decorators.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module contains useful decorators that can be used in the
application.
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
from collections.abc import Callable, Iterable
from typing import Any, Union

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'retry',
    'benchmark_execution',
    'log_execution',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
OriginalFunction = Callable[..., Any]
InnerFunction = Callable[..., Any]
DecoratorFunction = Callable[[OriginalFunction], InnerFunction]


def retry(
    exception_to_check: Union[type[Exception], Iterable[type[Exception]]],
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

            # Convert single exception to a tuple
            if isinstance(exception_to_check, Iterable):
                exceptions = tuple(exception_to_check)

            else:
                exceptions = tuple([exception_to_check])

            # Assert all exc in the exception tuple are exception types
            if not all(isinstance(exc, type) and issubclass(exc, Exception) for exc in exceptions):
                raise ValueError(
                    "exception_to_check must be an exception type or an iterable of exception types"
                )

            while tries > 1:
                try:
                    return original_func(*args, **kwargs)

                except exceptions as ex:
                    message = f"[RETRY]: {repr(ex)}, Retrying in {delay_secs} seconds..."

                    # Log error
                    module_logger.error(message)
                    print(message)

                    # Wait to retry
                    time.sleep(delay_secs)

                    # Increase delay for next retry
                    tries -= 1
                    delay_secs *= delay_multiplier

            return original_func(*args, **kwargs)

        return inner

    return decorator_retry


def benchmark_execution(logger: logging.Logger = module_logger) -> DecoratorFunction:
    """
    Retry calling the decorated function using an exponential
    backoff multiplier.

    :param logger: The logging.Logger instance to be used for logging
           the execution time of the decorated function.
           If not explicitly provided, the function uses
           Python's standard logging module as a default logger.
    """

    def decorator_benchmark(original_func: OriginalFunction) -> InnerFunction:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = original_func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            logger.info(f"Execution of {original_func.__name__} took {execution_time:.3f} seconds.")

            return result

        return inner

    return decorator_benchmark


def log_execution(logger: logging.Logger = module_logger) -> DecoratorFunction:
    """
    Retry calling the decorated function using an exponential
    backoff multiplier.

    :param logger: The logging.Logger instance to be used for logging
           the execution time of the decorated function.
           If not explicitly provided, the function uses
           Python's standard logging module as a default logger.
    """

    def decorator_logging(original_func: OriginalFunction) -> InnerFunction:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Initiating {original_func.__name__}")
            result = original_func(*args, **kwargs)
            logger.info(f"Finished {original_func.__name__}")

            return result

        return inner

    return decorator_logging
