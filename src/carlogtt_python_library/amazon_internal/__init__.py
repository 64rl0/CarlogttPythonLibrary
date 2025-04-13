# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/__init__.py
# Created 9/25/23 - 2:34 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module contains the package imports for the current package.
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
from .bindle import *
from .midway import *
from .midway_selenium import *
from .pipelines import *
from .simt import *
from .tiny_url import *

# These imports rely on internal Amazon Brazil packages that are not
# publicly available. If you're running this code outside of Amazon's
# internal environment, the import will fail. This is expected and safe
# to ignore. Any functionality requiring these internal packages simply
# won't be available externally.
try:
    from .apollo import *
    from .mirador import *
    from .phone_tool import *

except ImportError:
    import logging

    # Setting up logger for current module
    module_logger = logging.getLogger(__name__)
    module_logger.debug(
        "Amazon internal imports failed due to missing Brazil dependencies. This is expected if"
        " you're running outside the Amazon Brazil environment."
    )

# END IMPORTS
# ======================================================================
