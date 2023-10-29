# MODULE DETAILS
# decorators.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module contains useful decorators that can be used in the
application.
"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import functools
import logging
import time
from typing import Any, Callable

# END IMPORTS


# List of public names in the module
__all__ = [
    'benchmark_decorator',
    'logging_decorator',
]


# Annotations
OriginalFunction = Callable[..., Any]
InnerFunction = Callable[..., Any]
DecoratorFunction = Callable[[OriginalFunction], InnerFunction]


def benchmark_decorator(logger: logging.Logger) -> DecoratorFunction:
    """
    Retry calling the decorated function using an exponential
    backoff multiplier.
    """

    def decorator_benchmark(original_func: OriginalFunction) -> InnerFunction:
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


def logging_decorator(logger: logging.Logger) -> DecoratorFunction:
    """
    Retry calling the decorated function using an exponential
    backoff multiplier.
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
