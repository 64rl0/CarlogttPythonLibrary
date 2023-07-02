# MODULE NAME ----------------------------------------------------------------------------------------------------------
# decorators.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains useful decorators that can be used in the application.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import functools
import logging
import time
from typing import Any, Callable, Type

# Local Application Imports --------------------------------------------------------------------------------------------
from CarloCodes.my_utils_library.my_utils_library.logger import master_logger

# END IMPORTS ----------------------------------------------------------------------------------------------------------

# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
my_app_logger = master_logger.get_child_logger(__name__)


def retry_decorator(
    exception_to_check: Type[Exception],
    tries: int = 4,
    delay_secs: int = 3,
    delay_multiplier: int = 2,
    logger: logging.Logger = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    :param exception_to_check: the exception to check. may be a tuple of exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay_secs: initial delay between retries in seconds
    :type delay_secs: int
    :param delay_multiplier: delay multiplier e.g. value of 2 will double the delay each retry
    :type delay_multiplier: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def decorator_retry(original_func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(original_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            local_tries, local_delay_secs = tries, delay_secs

            while local_tries > 1:
                try:
                    return original_func(*args, **kwargs)

                except exception_to_check as e:
                    message = f"{str(e)}, Retrying in {local_delay_secs} seconds..."

                    if logger:
                        logger.error(message)

                    else:
                        print(message)

                    time.sleep(local_delay_secs)
                    local_tries -= 1
                    local_delay_secs *= delay_multiplier

            return original_func(*args, **kwargs)

        return wrapper

    return decorator_retry


def benchmark_decorator(logger: logging.Logger) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    """

    def decorator_benchmark(original_func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(original_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = original_func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.info(f"Execution of {original_func.__name__} took {execution_time:.3f} seconds.")

            return result

        return wrapper

    return decorator_benchmark


def logging_decorator(logger: logging.Logger) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    """

    def decorator_logging(original_func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(original_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Initiating {original_func.__name__}")
            result = original_func(*args, **kwargs)
            logger.info(f"Finished {original_func.__name__}")

            return result

        return wrapper

    return decorator_logging


if __name__ == '__main__':
    pass
