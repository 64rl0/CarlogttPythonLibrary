# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/cli_utils.py
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

# Standard Library Imports
import logging
import threading
import time

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'CLIStyle',
    'LoadingBar',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class CLIStyle:
    """
    A collection of ANSI escape codes and emojis for styling CLI output.
    """

    # Basic Foreground Colors
    CLI_BLACK = "\033[30m"
    CLI_RED = "\033[31m"
    CLI_GREEN = "\033[32m"
    CLI_YELLOW = "\033[33m"
    CLI_BLUE = "\033[34m"
    CLI_MAGENTA = "\033[35m"
    CLI_CYAN = "\033[36m"
    CLI_WHITE = "\033[37m"

    # Bold/Bright Foreground Colors
    CLI_BOLD_BLACK = "\033[1;30m"
    CLI_BOLD_RED = "\033[1;31m"
    CLI_BOLD_GREEN = "\033[1;32m"
    CLI_BOLD_YELLOW = "\033[1;33m"
    CLI_BOLD_BLUE = "\033[1;34m"
    CLI_BOLD_MAGENTA = "\033[1;35m"
    CLI_BOLD_CYAN = "\033[1;36m"
    CLI_BOLD_WHITE = "\033[1;37m"

    # Basic Background Colors
    CLI_BG_BLACK = "\033[40m"
    CLI_BG_RED = "\033[41m"
    CLI_BG_GREEN = "\033[42m"
    CLI_BG_YELLOW = "\033[43m"
    CLI_BG_BLUE = "\033[44m"
    CLI_BG_MAGENTA = "\033[45m"
    CLI_BG_CYAN = "\033[46m"
    CLI_BG_WHITE = "\033[47m"

    # Text Formatting
    CLI_BOLD = "\033[1m"
    CLI_DIM = "\033[2m"
    CLI_ITALIC = "\033[3m"
    CLI_UNDERLINE = "\033[4m"
    CLI_INVERT = "\033[7m"
    CLI_HIDDEN = "\033[8m"

    # Reset Specific Formatting
    CLI_END = "\033[0m"
    CLI_END_BOLD = "\033[21m"
    CLI_END_DIM = "\033[22m"
    CLI_END_ITALIC_UNDERLINE = "\033[23m"
    CLI_END_INVERT = "\033[27m"
    CLI_END_HIDDEN = "\033[28m"

    # Emoji
    EMOJI_GREEN_CHECK_MARK = "\xe2\x9c\x85"
    EMOJI_HAMMER_AND_WRENCH = "\xf0\x9f\x9b\xa0"
    EMOJI_CLOCK = "\xe2\x8f\xb0"
    EMOJI_SPARKLES = "\xe2\x9c\xa8"
    EMOJI_STOP_SIGN = "\xf0\x9f\x9b\x91"
    EMOJI_WARNING_SIGN = "\xe2\x9a\xa0\xef\xb8\x8f"
    EMOJI_KEY = "\xf0\x9f\x94\x91"
    EMOJI_CIRCLE_ARROWS = "\xf0\x9f\x94\x84"
    EMOJI_BROOM = "\xf0\x9f\xa7\xb9"
    EMOJI_LINK = "\xf0\x9f\x94\x97"
    EMOJI_PACKAGE = "\xf0\x9f\x93\xa6"
    EMOJI_NETWORK_WORLD = "\xf0\x9f\x8c\x90"


class LoadingBar(threading.Thread):
    """
    A class that represents a simple loading bar animation running in
    a separate thread.

    :param secs: The total duration in seconds for the loading bar
           to complete.
    """

    def __init__(self, secs: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._secs = secs
        self._stop_event = threading.Event()

    def run(self):
        """
        Overrides the Thread.run() method; generates and displays a
        loading bar animation.
        The animation progresses over the specified duration
        (self._secs) unless stop() is called.
        """

        for i in range(101):
            if not self._stop_event.is_set():
                ii = i // 2
                bar = "[" + "#" * ii + " " * (50 - ii) + "]"
                value = str(i) + "%"
                print(" " + bar + " " + value, end='\r', flush=True)
                time.sleep(self._secs / 101)

            else:
                break

        print("\n")

    def stop(self):
        """
        Stops the loading bar animation by setting the _stop_event.
        Once called, it signals the run method to terminate the
        animation loop.
        """

        self._stop_event.set()
