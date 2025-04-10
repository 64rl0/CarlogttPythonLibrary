# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# __init__.py -> carlogtt_python_library
# Created 10/4/23 - 10:44 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
carlogtt_python_library is a collection of utility functions designed to
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

# Standard Library Imports
import logging as _logging
import sys as _sys
import warnings as _warnings

# Local Folder (Relative) Imports
from .amazon_internal import *
from .aws_boto3 import *
from .database import *
from .exceptions import *
from .logger import *
from .utils import *

# END IMPORTS
# ======================================================================


# Setting up logger for current module
_module_logger = _logging.getLogger(__name__)


class _CompatibilityProxy:
    """
    Compatibility proxy to warn on legacy-style variable access
    (e.g. `cli_red`) and redirect to the CLIStyle class.
    """

    DEPRECATED_CLI_STYLE_VARIABLES = {
        'cli_black',
        'cli_red',
        'cli_green',
        'cli_yellow',
        'cli_blue',
        'cli_magenta',
        'cli_cyan',
        'cli_white',
        'cli_bold_black',
        'cli_bold_red',
        'cli_bold_green',
        'cli_bold_yellow',
        'cli_bold_blue',
        'cli_bold_magenta',
        'cli_bold_cyan',
        'cli_bold_white',
        'cli_bg_black',
        'cli_bg_red',
        'cli_bg_green',
        'cli_bg_yellow',
        'cli_bg_blue',
        'cli_bg_magenta',
        'cli_bg_cyan',
        'cli_bg_white',
        'cli_bold',
        'cli_dim',
        'cli_italic',
        'cli_underline',
        'cli_invert',
        'cli_hidden',
        'cli_end',
        'cli_end_bold',
        'cli_end_dim',
        'cli_end_italic_underline',
        'cli_end_invert',
        'cli_end_hidden',
        'emoji_green_check_mark',
        'emoji_hammer_and_wrench',
        'emoji_clock',
        'emoji_sparkles',
        'emoji_stop_sign',
        'emoji_warning_sign',
        'emoji_key',
        'emoji_circle_arrows',
        'emoji_broom',
        'emoji_link',
        'emoji_package',
        'emoji_network_world',
    }

    def __getattr__(self, name: str):
        """
        Redirects access to deprecated variables to the new variable
        location.
        """

        if name in self.DEPRECATED_CLI_STYLE_VARIABLES:
            upper_name = name.upper()

            if hasattr(CLIStyle, upper_name):
                _warnings.warn(
                    f"[DEPRECATED] '{name}' is deprecated. Use 'CLIStyle.{upper_name}' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )

                _module_logger.warning(
                    f"[DEPRECATED] '{name}' is deprecated. Use 'CLIStyle.{upper_name}' instead.",
                )

                return getattr(CLIStyle, upper_name)

        else:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Inject the compatibility proxy at module-level
_sys.modules[__name__].__getattr__ = _CompatibilityProxy().__getattr__  # type: ignore
