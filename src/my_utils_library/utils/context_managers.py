# MODULE DETAILS
# context_managers.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import io
import sys
from contextlib import contextmanager
from typing import Type

# END IMPORTS


# List of public names in the module
__all__ = [
    'suppress_errors',
    'redirect_stdout_to_file',
    'redirect_stdout_to_stderr',
]


@contextmanager
def suppress_errors(*exceptions: Type[Exception]):
    """
    Context manager to suppress specified exceptions.

    :param exceptions: Variable length exception list which includes
           the exception classes of exceptions to be suppressed.

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

    :param fileobj: Opened file object to redirect stdout to.

    Example:
        ::

            with open("file.txt", 'w') as file:
                with redirect_stdout_to_file(file):
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
