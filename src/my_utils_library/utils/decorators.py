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

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


original_f = Callable[..., Any]
inner_f = Callable[..., Any]
decorator_f = Callable[[original_f], inner_f]


def retry_decorator(
    exception_to_check: Type[Exception], tries: int = 4, delay_secs: int = 3, delay_multiplier: int = 2
) -> decorator_f:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    :param exception_to_check: the exception to check. may be a tuple of exceptions to check
    :param tries: number of times to try (not retry) before giving up
    :param delay_secs: initial delay between retries in seconds
    :param delay_multiplier: delay multiplier e.g. value of 2 will double the delay each retry
    """

    def decorator_retry(original_func: original_f) -> inner_f:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            local_tries, local_delay_secs = tries, delay_secs

            while local_tries > 1:
                try:
                    return original_func(*args, **kwargs)

                except exception_to_check as e:
                    message = f"{str(e)}, Retrying in {local_delay_secs} seconds..."

                    # Log error
                    logging.error(message)
                    print(message)

                    time.sleep(local_delay_secs)
                    local_tries -= 1
                    local_delay_secs *= delay_multiplier

            return original_func(*args, **kwargs)

        return inner

    return decorator_retry


def benchmark_decorator(logger: logging.Logger) -> decorator_f:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    """

    def decorator_benchmark(original_func: original_f) -> inner_f:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = original_func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.info(f"Execution of {original_func.__name__} took {execution_time:.3f} seconds.")

            return result

        return inner

    return decorator_benchmark


def logging_decorator(logger: logging.Logger) -> decorator_f:
    """
    Retry calling the decorated function using an exponential backoff multiplier.
    """

    def decorator_logging(original_func: original_f) -> inner_f:
        @functools.wraps(original_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Initiating {original_func.__name__}")
            result = original_func(*args, **kwargs)
            logger.info(f"Finished {original_func.__name__}")

            return result

        return inner

    return decorator_logging
