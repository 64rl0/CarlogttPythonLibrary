# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/apollo.py
# Created 10/30/23 - 11:01 PM UK Time (London) by carlogtt
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
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import logging
import os
import warnings

# Third Party Library Imports
import bender.apollo_environment_info  # type: ignore
import bender.apollo_error  # type: ignore

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Apollo',
    # Deprecated
    'get_application_root',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class Apollo:
    """
    A handler class for the Apollo API.
    """

    def get_application_root(self) -> str:
        """
        Retrieve the absolute path of the application root directory.

        :return: The absolute path to the application root directory.
        """

        try:
            root = os.path.abspath(bender.apollo_environment_info.ApolloEnvironmentInfo().root)

        except bender.apollo_error.ApolloError:
            root = os.path.abspath(
                bender.apollo_environment_info.BrazilBootstrapEnvironmentInfo().root
            )

        return root


def get_application_root() -> str:

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{get_application_root.__name__}' is deprecated. Use the parent"
        f" class '{Apollo.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    try:
        return os.path.abspath(bender.apollo_environment_info.ApolloEnvironmentInfo().root)
    except bender.apollo_error.ApolloError:
        return os.path.abspath(bender.apollo_environment_info.BrazilBootstrapEnvironmentInfo().root)
