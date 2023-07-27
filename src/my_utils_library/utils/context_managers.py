# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# context_managers.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module ...
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import io
import logging
import sys
from contextlib import contextmanager
from typing import Type

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


@contextmanager
def suppress_errors(*exceptions: Type[Exception]):
    """
    Context manager to suppress specified exceptions.

    Args:
        exceptions:
            Variable length exception list which includes the exception classes of exceptions to be suppressed.

    Yields:
        None

    Example:
        ::

            with suppress_errors(ZeroDivisionError):
                1/0  # This will not raise an exception
    """

    try:
        yield

    except exceptions:
        pass


@contextmanager
def redirect_stdout_to_file(fileobj: io.TextIOWrapper):
    """
    Context manager to redirect stdout to file.

    Args:
        fileobj:
            Opened file object to redirect stdout to.

    Yields:
        None

    Example:
        ::

            with open("file.txt", 'w'):
                with redirect_stdout_to_file():
                    print("Hello World!")  # This will print to file.
    """

    current_stdout = sys.stdout
    sys.stdout = fileobj

    try:
        yield

    finally:
        sys.stdout = current_stdout


@contextmanager
def redirect_stdout_to_stderr():
    """
    Context manager to redirect stdout to stderr.

    Example:
        ::

            with redirect_stdout_to_stderr():
                print("Hello World!")  # This will print to stderr.
    """

    current_stdout = sys.stdout
    sys.stdout = sys.stderr

    try:
        yield

    finally:
        sys.stdout = current_stdout


if __name__ == '__main__':
    pass
    # print(*suppress_errors())
    # with suppress_errors(ValueError):
    #     raise ValueError()
    #
    # with suppress_errors(ValueError):
    #     raise ValueError()
