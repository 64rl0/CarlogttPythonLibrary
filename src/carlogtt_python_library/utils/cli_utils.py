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

# Standard Library Imports
import threading
import time

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
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
    'LoadingBar',
]

# Setting up logger for current module
# module_logger =

# Type aliases
#


# Basic Foreground Colors
cli_black = "\033[30m"
cli_red = "\033[31m"
cli_green = "\033[32m"
cli_yellow = "\033[33m"
cli_blue = "\033[34m"
cli_magenta = "\033[35m"
cli_cyan = "\033[36m"
cli_white = "\033[37m"

# Bold/Bright Foreground Colors
cli_bold_black = "\033[1;30m"
cli_bold_red = "\033[1;31m"
cli_bold_green = "\033[1;32m"
cli_bold_yellow = "\033[1;33m"
cli_bold_blue = "\033[1;34m"
cli_bold_magenta = "\033[1;35m"
cli_bold_cyan = "\033[1;36m"
cli_bold_white = "\033[1;37m"

# Basic Background Colors
cli_bg_black = "\033[40m"
cli_bg_red = "\033[41m"
cli_bg_green = "\033[42m"
cli_bg_yellow = "\033[43m"
cli_bg_blue = "\033[44m"
cli_bg_magenta = "\033[45m"
cli_bg_cyan = "\033[46m"
cli_bg_white = "\033[47m"

# Text Formatting
cli_bold = "\033[1m"
cli_dim = "\033[2m"
cli_italic = "\033[3m"
cli_underline = "\033[4m"
cli_invert = "\033[7m"
cli_hidden = "\033[8m"

# Reset Specific Formatting
cli_end = "\033[0m"
cli_end_bold = "\033[21m"
cli_end_dim = "\033[22m"
cli_end_italic_underline = "\033[23m"
cli_end_invert = "\033[27m"
cli_end_hidden = "\033[28m"

# Emoji
emoji_green_check_mark = "\xe2\x9c\x85"
emoji_hammer_and_wrench = "\xf0\x9f\x9b\xa0"
emoji_clock = "\xe2\x8f\xb0"
emoji_sparkles = "\xe2\x9c\xa8"
emoji_stop_sign = "\xf0\x9f\x9b\x91"
emoji_warning_sign = "\xe2\x9a\xa0\xef\xb8\x8f"
emoji_key = "\xf0\x9f\x94\x91"
emoji_circle_arrows = "\xf0\x9f\x94\x84"
emoji_broom = "\xf0\x9f\xa7\xb9"
emoji_link = "\xf0\x9f\x94\x97"
emoji_package = "\xf0\x9f\x93\xa6"
emoji_network_world = "\xf0\x9f\x8c\x90"


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
