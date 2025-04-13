# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/__init__.py
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

    DEPRECATED_NAMES_PUBLIC = {
        'cli_black': CLIStyle,
        'cli_red': CLIStyle,
        'cli_green': CLIStyle,
        'cli_yellow': CLIStyle,
        'cli_blue': CLIStyle,
        'cli_magenta': CLIStyle,
        'cli_cyan': CLIStyle,
        'cli_white': CLIStyle,
        'cli_bold_black': CLIStyle,
        'cli_bold_red': CLIStyle,
        'cli_bold_green': CLIStyle,
        'cli_bold_yellow': CLIStyle,
        'cli_bold_blue': CLIStyle,
        'cli_bold_magenta': CLIStyle,
        'cli_bold_cyan': CLIStyle,
        'cli_bold_white': CLIStyle,
        'cli_bg_black': CLIStyle,
        'cli_bg_red': CLIStyle,
        'cli_bg_green': CLIStyle,
        'cli_bg_yellow': CLIStyle,
        'cli_bg_blue': CLIStyle,
        'cli_bg_magenta': CLIStyle,
        'cli_bg_cyan': CLIStyle,
        'cli_bg_white': CLIStyle,
        'cli_bold': CLIStyle,
        'cli_dim': CLIStyle,
        'cli_italic': CLIStyle,
        'cli_underline': CLIStyle,
        'cli_invert': CLIStyle,
        'cli_hidden': CLIStyle,
        'cli_end': CLIStyle,
        'cli_end_bold': CLIStyle,
        'cli_end_dim': CLIStyle,
        'cli_end_italic_underline': CLIStyle,
        'cli_end_invert': CLIStyle,
        'cli_end_hidden': CLIStyle,
        'emoji_green_check_mark': CLIStyle,
        'emoji_hammer_and_wrench': CLIStyle,
        'emoji_clock': CLIStyle,
        'emoji_sparkles': CLIStyle,
        'emoji_stop_sign': CLIStyle,
        'emoji_warning_sign': CLIStyle,
        'emoji_key': CLIStyle,
        'emoji_circle_arrows': CLIStyle,
        'emoji_broom': CLIStyle,
        'emoji_link': CLIStyle,
        'emoji_package': CLIStyle,
        'emoji_network_world': CLIStyle,
        'get_random_string': StringUtils,
        'snake_case': StringUtils,
        'get_user_input_and_validate_int': UserPrompter,
        'get_user_input_confirmation_y_n': UserPrompter,
        'validate_non_empty_strings': InputValidator,
        'validate_username_requirements': InputValidator,
        'validate_password_requirements': InputValidator,
        'create_amazon_tiny_url': AmazonTinyUrl,
        'cli_midway_auth': MidwayUtils,
        'extract_valid_cookies': MidwayUtils,
    }

    try:
        DEPRECATED_NAMES_AMAZON_INTERNAL = {
            'get_application_root': Apollo,
            'phone_tool_lookup': PhoneTool,
        }

        DEPRECATED_NAMES = {**DEPRECATED_NAMES_PUBLIC, **DEPRECATED_NAMES_AMAZON_INTERNAL}

    except NameError:
        DEPRECATED_NAMES = DEPRECATED_NAMES_PUBLIC

    def __getattr__(self, name: str):
        """
        Redirects access to deprecated variables to the new variable
        location.
        """

        if name in self.DEPRECATED_NAMES:
            if self.DEPRECATED_NAMES[name] is CLIStyle:
                return self._handle_cli_style(name=name)
            else:
                return self._warn_user(name=name, new_class=self.DEPRECATED_NAMES[name])

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def _handle_cli_style(self, name: str):
        upper_name = name.upper()
        msg = (
            f"[DEPRECATED] '{name}' is deprecated. Use '{CLIStyle.__qualname__}.{upper_name}'"
            " instead."
        )

        _warnings.warn(msg, DeprecationWarning, stacklevel=3)
        _module_logger.warning(msg)

        return getattr(CLIStyle, upper_name)

    def _warn_user(self, name: str, new_class: type):
        msg = (
            f"[DEPRECATED] '{name}' is deprecated. Use the parent class"
            f" '{new_class.__qualname__}()' instead."
        )

        _warnings.warn(msg, DeprecationWarning, stacklevel=3)
        _module_logger.warning(msg)

        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. Use the parent class"
            f" '{new_class.__qualname__}()' instead."
        )


# Inject the compatibility proxy at module-level
_sys.modules[__name__].__getattr__ = _CompatibilityProxy().__getattr__  # type: ignore
