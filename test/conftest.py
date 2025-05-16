# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/CarlogttLibrary/test/conftest.py
# Created 5/8/25 - 8:12 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made code or quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import importlib
import sys

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


class _NoopRetry:
    def __init__(self, *a, **kw):
        self.a = a
        self.kw = kw

    def __call__(self, fn):
        return fn

    def __enter__(self):
        return lambda fn, *a, **kw: fn(*a, **kw)

    def __exit__(self, exc_type, exc, tb):
        return False


def pytest_sessionstart(session):
    """
    This function is called before the test session starts.
    It patches the retry decorator to disable retries during tests.
    """

    import carlogtt_library

    carlogtt_library.retry = _NoopRetry
    carlogtt_library.utils.retry = _NoopRetry
    carlogtt_library.utils.decorators.retry = _NoopRetry

    to_reload = [
        'carlogtt_library.amazon_internal.simt',
        'carlogtt_library.database.database_dynamo',
        'carlogtt_library.database.database_sql',
        'carlogtt_library.database.redis_cache_manager',
        'carlogtt_library.utils.aws_sig_v4_requests',
    ]
    for name in to_reload:
        importlib.reload(sys.modules[name])
