# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# apollo.py
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
import os

# Third Party Library Imports
from bender import apollo_environment_info  # type: ignore
from bender.apollo_error import ApolloError  # type: ignore

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'get_application_root',
]


def get_application_root() -> str:
    try:
        return os.path.abspath(apollo_environment_info.ApolloEnvironmentInfo().root)
    except ApolloError:
        return os.path.abspath(apollo_environment_info.BrazilBootstrapEnvironmentInfo().root)
