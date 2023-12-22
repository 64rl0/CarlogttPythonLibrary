# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# cli_utils.py
# Created 12/22/23 - 6:57 PM UK Time (London) by carlogtt
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


# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'red',
    'green',
    'yellow',
    'blu',
    'bold',
    'end',
]

# Setting up logger for current module
# module_logger =

# Type aliases
#


# Colors
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blu = "\033[34m"
bold = "\033[1m"
end = "\033[0m"
