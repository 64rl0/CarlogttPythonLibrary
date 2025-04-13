# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/context_managers.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
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
import contextlib
import io
import logging
import sys

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'suppress_errors',
    'redirect_stdout_to_file',
    'redirect_stdout_to_stderr',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


@contextlib.contextmanager
def suppress_errors(*exceptions: type[Exception]):
    """
    Context manager to suppress specified exceptions.

    :param exceptions: Variable length exception list which includes
           the exception classes of exceptions to be suppressed.

    Example:
        with suppress_errors(ZeroDivisionError):
            1/0  # This will not raise an exception
    """

    try:
        yield

    except exceptions:
        pass


@contextlib.contextmanager
def redirect_stdout_to_file(fileobj: io.TextIOWrapper):
    """
    Context manager to redirect stdout to file.

    :param fileobj: Opened file object to redirect stdout to.

    Example:
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


@contextlib.contextmanager
def redirect_stdout_to_stderr():
    """
    Context manager to redirect stdout to stderr.

    Example:
        with redirect_stdout_to_stderr():
            print("Hello World!")  # This will print to stderr.
    """

    current_stdout = sys.stdout
    sys.stdout = sys.stderr

    try:
        yield

    finally:
        sys.stdout = current_stdout
