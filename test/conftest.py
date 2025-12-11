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

    try:
        # try import Py-Pi library first
        # https://pypi.org/project/carlogtt-python-library/
        import carlogtt_python_library

        carlogtt_python_library.retry = _NoopRetry
        carlogtt_python_library.utils.retry = _NoopRetry
        carlogtt_python_library.utils.decorators.retry = _NoopRetry

        # Reload all the modules that use the retry decorator to use
        # the patched one
        to_reload = [
            '.amazon_internal.simt',
            '.database.database_dynamo',
            '.database.database_sql',
            '.database.redis_cache_manager',
            '.utils.aws_sig_v4_requests',
        ]
        for name in to_reload:
            importlib.reload(sys.modules[f"carlogtt_python_library{name}"])

    except (ImportError, ModuleNotFoundError):
        # If we are in Brazil try to alias to the Amazon Brazil package
        import carlogtt_library

        carlogtt_library.retry = _NoopRetry
        carlogtt_library.utils.retry = _NoopRetry
        carlogtt_library.utils.decorators.retry = _NoopRetry

        # Reload all the modules that use the retry decorator to use
        # the patched one
        to_reload = [
            '.amazon_internal.simt',
            '.database.database_dynamo',
            '.database.database_sql',
            '.database.redis_cache_manager',
            '.utils.aws_sig_v4_requests',
        ]
        for name in to_reload:
            importlib.reload(sys.modules[f"carlogtt_library{name}"])

        # Because all the unit tests import the library as
        # `carlogtt_python_library` we need to alias the Amazon Brazil
        # Library to `carlogtt_python_library`.
        sys.modules["carlogtt_python_library"] = importlib.import_module("carlogtt_library")

        # Ensure common subpackages resolve for patch targets
        for sub in (
            ".amazon_internal",
            ".amazon_internal.apollo",
            ".amazon_internal.bindle",
            ".amazon_internal.midway",
            ".amazon_internal.midway_selenium",
            ".amazon_internal.mirador",
            ".amazon_internal.phone_tool",
            ".amazon_internal.pipelines",
            ".amazon_internal.simt",
            ".amazon_internal.tiny_url",
            ".aws_boto3",
            ".aws_boto3.aws_lambda",
            ".aws_boto3.aws_service_base",
            ".aws_boto3.cloud_front",
            ".aws_boto3.ec2",
            ".aws_boto3.kms",
            ".aws_boto3.s3",
            ".aws_boto3.secrets_manager",
            ".database",
            ".database.database_dynamo",
            ".database.database_sql",
            ".database.database_utils",
            ".database.redis_cache_manager",
            ".exceptions",
            ".exceptions.exceptions",
            ".logger",
            ".logger.app_logger",
            ".utils",
            ".utils.aws_sig_v4_requests",
            ".utils.cli_utils",
            ".utils.context_managers",
            ".utils.decorators",
            ".utils.encryption",
            ".utils.miscs",
            ".utils.string_tools",
            ".utils.user_input",
            ".utils.validators",
        ):
            sys.modules[f"carlogtt_python_library{sub}"] = importlib.import_module(
                f"carlogtt_library{sub}"
            )
