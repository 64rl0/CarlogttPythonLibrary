# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/utils/decorators.py
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
import enum
import functools
import logging
import sys
import time
from collections.abc import Callable, Iterable
from types import TracebackType
from typing import Any, Literal, Optional, TypeVar, Union

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec, TypeAlias
else:
    from typing_extensions import Concatenate, ParamSpec, TypeAlias

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'retry',
    'benchmark_execution',
    'log_execution',
    'BenchmarkResolution',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
P = ParamSpec("P")
R = TypeVar("R")
Retryer: TypeAlias = Callable[Concatenate[Callable[P, R], P], R]


class BenchmarkResolution(enum.Enum):
    """
    Defines time resolution units and their corresponding duration in
    seconds.
    """

    SECONDS = ("seconds", 1)
    MINUTES = ("minutes", 60)
    HOURS = ("hours", 3600)
    DAYS = ("days", 86400)


class retry:  # noqa
    """
    Retry helper that works both as a decorator and as a context
    manager, using an exponential backoff multiplier.

    Examples
    --------
    Decorator usage::

        @retry((TimeoutError, ConnectionError), tries=5, delay_secs=1)
        def fetch(url: str) -> bytes:
            ...

    Context-manager usage::

        with retry(ValueError, tries=3) as retryer:
            data = retryer(load_csv, "data.csv")
            retryer(save_report, path="out.pdf", data=data)

    :param exception_to_check: the exception to check. may be a tuple
        of exceptions to check
    :param tries: number of times to try (not retry) before giving up
    :param delay_secs: initial delay between retries in seconds
    :param delay_multiplier: delay multiplier e.g. value of 2 will
        double the delay each retry
    :param logger: The logging.Logger instance to be used for logging
        the execution time of the decorated function.
        If not explicitly provided, the function uses Python's standard
        logging module as a default logger.
    """

    def __init__(
        self,
        exception_to_check: Union[type[Exception], Iterable[type[Exception]]],
        tries: int = 4,
        delay_secs: int = 3,
        delay_multiplier: int = 2,
        logger: logging.Logger = module_logger,
    ) -> None:
        self.exception_to_check = exception_to_check
        self.tries = self.tot_tries = tries
        self.delay_secs = delay_secs
        self.delay_multiplier = delay_multiplier
        self.logger = logger

        # Convert single exception to a tuple
        if isinstance(self.exception_to_check, Iterable):
            self.exceptions = tuple(self.exception_to_check)
        else:
            self.exceptions = tuple([self.exception_to_check])

        # Assert all exc in the exception tuple are exception types
        if not all(isinstance(exc, type) and issubclass(exc, Exception) for exc in self.exceptions):
            raise ValueError(
                "exception_to_check must be an exception type or an iterable of exception types"
            )

    def __call__(self, original_func: Callable[P, R]) -> Callable[P, R]:
        return self._decorator(original_func)

    def __enter__(self) -> Callable[..., Any]:
        """
        Enter the retry context.

        :returns: retryer – a small helper
        """

        return self._retryer

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """
        Exit the retry context.

        Returning False tells Python to propagate any exception that
        occurred inside the with block.
        """

        return False

    def _retryer(self, original_func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Internal one-shot wrapper used by the context-manager helper.

        :raises TypeError: If original_func is not callable.
        """

        if not callable(original_func):
            raise TypeError(
                "retryer expected a callable as its first argument, "
                f"but received {original_func!r} (type: {type(original_func).__name__})"
            )

        return self._decorator(original_func)(*args, **kwargs)

    def _decorator(self, original_func: Callable[P, R]) -> Callable[P, R]:
        """
        Build the retrying wrapper around original_func.
        """

        @functools.wraps(original_func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            while self.tries > 1:
                try:
                    return original_func(*args, **kwargs)

                except self.exceptions as ex:
                    message = (
                        f"[RETRY {self.tot_tries - self.tries + 2}/{self.tot_tries}]: Caught"
                        f" {repr(ex)}, Retrying in {self.delay_secs} seconds..."
                    )

                    # Log error
                    self.logger.debug(message)

                    # Wait to retry
                    time.sleep(self.delay_secs)

                    # Increase delay for next retry
                    self.tries -= 1
                    self.delay_secs *= self.delay_multiplier

            return original_func(*args, **kwargs)

        return inner


def benchmark_execution(
    logger: logging.Logger = module_logger,
    resolution: Union[str, BenchmarkResolution] = BenchmarkResolution.SECONDS,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Measure and log the execution time of the decorated function.

    :param logger: The logging.Logger instance to be used for logging
        the execution time of the decorated function.
        If not explicitly provided, the function uses Python's standard
        logging module as a default logger.
    :param resolution: The time unit for reporting execution time.
        Can be either:
        - A string from {"sec", "min", "hour", "day"}, or
        - An instance of BenchmarkResolution
        (e.g. BenchmarkResolution.SECONDS).
        Defaults to BenchmarkResolution.SECONDS.
    """

    valid_resolutions = {
        "sec": BenchmarkResolution.SECONDS,
        "min": BenchmarkResolution.MINUTES,
        "hour": BenchmarkResolution.HOURS,
        "day": BenchmarkResolution.DAYS,
    }

    # Validate the resolution
    if isinstance(resolution, str):
        try:
            resolution_enum = valid_resolutions[resolution]
        except KeyError:
            raise ValueError(
                f"Invalid resolution '{resolution}'. Must be one of:"
                f" {list(valid_resolutions.keys())}"
            )

    elif issubclass(type(resolution), BenchmarkResolution):
        resolution_enum = resolution

    else:
        raise TypeError(
            f"Invalid type for 'resolution': expected str (one of {list(valid_resolutions.keys())})"
            f" or a 'BenchmarkResolution' value, but got {type(resolution)}."
        )

    unit_label, divisor = resolution_enum.value

    def decorator_benchmark(original_func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(original_func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            result = original_func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time

            # Convert to the desired resolution
            converted_time = execution_time / divisor

            logger.info(
                f"Execution of {original_func.__name__} took {converted_time:.3f} {unit_label}."
            )

            return result

        return inner

    return decorator_benchmark


def log_execution(
    logger: logging.Logger = module_logger,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Log the start and completion of the decorated function using the
    provided logger.

    :param logger: The logging.Logger instance to be used for logging
           the execution time of the decorated function.
           If not explicitly provided, the function uses
           Python's standard logging module as a default logger.
    """

    def decorator_logging(original_func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(original_func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.info(f"Initiating {original_func.__name__}")
            result = original_func(*args, **kwargs)
            logger.info(f"Finished {original_func.__name__}")

            return result

        return inner

    return decorator_logging
