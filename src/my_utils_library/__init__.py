# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# __init__.py -> my_utils_library
# Created 10/4/23 - 10:44 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
my_utils_library is a collection of utility functions designed to
simplify common tasks in Python.
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
# Module imported but unused (F401)
# 'from module import *' used; unable to detect undefined names (F403)
# flake8: noqa

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Local Folder (Relative) Imports
from .amazon_internal import *
from .aws_boto import *
from .database import *
from .exceptions import *
from .logger import *
from .utils import *

# END IMPORTS
# ======================================================================
