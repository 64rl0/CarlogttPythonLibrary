# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_logger.py
# Created 4/12/25 - 9:24 AM UK Time (London) by carlogtt
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

# Third Party Library Imports
from test__entrypoint__ import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#

module_logger = master_logger.get_child_logger(__name__)

module_logger.debug("this is a debug message on stderr")

master_logger.change_logger_level(mylib.LoggerLevel.WARNING)
module_logger.debug("this is a debug message 2 on stderr")

master_logger.change_logger_level('debug')
module_logger.debug("this is a debug message 3 on stderr")
module_logger.debug("this is a debug message 4 on stderr")

print('hello')

module_logger.debug("this is a debug message 5 on stderr")
