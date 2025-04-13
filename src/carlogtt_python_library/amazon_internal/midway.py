# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/midway.py
# Created 12/11/23 - 11:19 PM UK Time (London) by carlogtt
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
import re
import subprocess
import sys
import time
import warnings

# Local Folder (Relative) Imports
from .. import utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'MidwayUtils',
    # Deprecated
    'cli_midway_auth',
    'extract_valid_cookies',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class MidwayUtils:
    """
    A handler class for Midway utilities.
    """

    def cli_midway_auth(self, max_retries: int = 3, options: str = "-s"):
        """
        Run mwinit -s as bash command.

        :param max_retries: The maximum number of total attempts.
               Default is 3.
        :param options: The options to pass to the mwinit command.
               Default is -s
        :return: None
        """

        for i in range(max_retries):
            # Run mwinit -s
            command = "mwinit {options} || exit 1".format(options=options)

            # Run the command using subprocess.Popen
            process = subprocess.Popen(command, shell=True, executable="/bin/bash")

            # Wait for the process to complete
            process.wait()

            # Get the return code of the process
            return_code = process.returncode

            # Check the return code to see if the command was successful
            if return_code == 0:
                break

            else:
                if i == max_retries - 1:
                    print(
                        utils.CLIStyle.CLI_BOLD_RED
                        + "\n[ERROR] Authentication to Midway failed.\n"
                        + utils.CLIStyle.CLI_END,
                        flush=True,
                    )
                    sys.exit(1)

                print(
                    utils.CLIStyle.CLI_BOLD_RED
                    + f"\n[ERROR] Authentication to Midway failed. Retrying {i + 2}...\n"
                    + utils.CLIStyle.CLI_END,
                    flush=True,
                )

    def extract_valid_cookies(self, cookie_filepath: str = "~/.midway/cookie") -> dict[str, str]:
        """
        Retrieves valid cookies from a specified cookie file, filtering
        based on cookie that start with #Http and valid cookie
        expiration time.
        Return a dictionary of cookie names and their values.

        :param cookie_filepath: The file path to the cookie file.
               Defaults to "~/.midway/cookie".
        :return: A dictionary where each key-value pair corresponds to a
                 cookie name and its value extracted from the file.
        """

        real_cookie_filepath = os.path.realpath(os.path.expanduser(cookie_filepath))

        if not os.path.exists(real_cookie_filepath) or not os.path.isfile(real_cookie_filepath):
            raise ValueError(f"cookie_filepath: {real_cookie_filepath} not found!")

        cookies: dict[str, str] = {}

        search_pattern = re.compile("^#Http", re.IGNORECASE)

        with open(real_cookie_filepath, 'r') as cookie_file:
            for cookie in cookie_file:
                if not search_pattern.match(cookie):
                    continue

                cookie_fields = cookie.split()

                # Cookie fields
                # 0 - Domain
                # 1 - Flag
                # 2 - Path
                # 3 - Secure
                # 4 - Expiration Time
                # 5 - Name
                # 6 - Value

                if len(cookie_fields) != 7:
                    continue

                if int(cookie_fields[4]) <= time.time():
                    continue

                cookies.update({cookie_fields[5]: cookie_fields[6]})

            if not cookies:
                raise ValueError(f"No valid cookies found in {real_cookie_filepath}")

        return cookies


def cli_midway_auth(max_retries: int = 3, options: str = "-s"):
    """
    Run mwinit -s as bash command.

    :param max_retries: The maximum number of total attempts.
           Default is 3.
    :param options: The options to pass to the mwinit command.
           Default is -s
    :return: None
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{cli_midway_auth.__name__}' is deprecated. Use the parent"
        f" class '{MidwayUtils.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    for i in range(max_retries):
        # Run mwinit -s
        command = "mwinit {options} || exit 1".format(options=options)

        # Run the command using subprocess.Popen
        process = subprocess.Popen(command, shell=True, executable="/bin/bash")

        # Wait for the process to complete
        process.wait()

        # Get the return code of the process
        return_code = process.returncode

        # Check the return code to see if the command was successful
        if return_code == 0:
            break

        else:
            if i == max_retries - 1:
                print(
                    utils.CLIStyle.CLI_BOLD_RED
                    + "\n[ERROR] Authentication to Midway failed.\n"
                    + utils.CLIStyle.CLI_END,
                    flush=True,
                )
                sys.exit(1)

            print(
                utils.CLIStyle.CLI_BOLD_RED
                + f"\n[ERROR] Authentication to Midway failed. Retrying {i + 2}...\n"
                + utils.CLIStyle.CLI_END,
                flush=True,
            )


def extract_valid_cookies(cookie_filepath: str = "~/.midway/cookie") -> dict[str, str]:
    """
    Retrieves valid cookies from a specified cookie file, filtering
    based on cookie that start with #Http and valid cookie expiration
    time.
    Return a dictionary of cookie names and their values.

    :param cookie_filepath: The file path to the cookie file.
           Defaults to "~/.midway/cookie".
    :return: A dictionary where each key-value pair corresponds to a
             cookie name and its value extracted from the file.
    """

    # TODO(carlogtt): Delete this function after deprecation period
    msg = (
        f"[DEPRECATED] '{extract_valid_cookies.__name__}' is deprecated. Use the parent"
        f" class '{MidwayUtils.__qualname__}()' instead."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    module_logger.warning(msg)

    real_cookie_filepath = os.path.realpath(os.path.expanduser(cookie_filepath))

    if not os.path.exists(real_cookie_filepath) or not os.path.isfile(real_cookie_filepath):
        raise ValueError(f"cookie_filepath: {real_cookie_filepath} not found!")

    cookies: dict[str, str] = {}

    search_pattern = re.compile("^#Http", re.IGNORECASE)

    with open(real_cookie_filepath, 'r') as cookie_file:
        for cookie in cookie_file:
            if not search_pattern.match(cookie):
                continue

            cookie_fields = cookie.split()

            # Cookie fields
            # 0 - Domain
            # 1 - Flag
            # 2 - Path
            # 3 - Secure
            # 4 - Expiration Time
            # 5 - Name
            # 6 - Value

            if len(cookie_fields) != 7:
                continue

            if int(cookie_fields[4]) <= time.time():
                continue

            cookies.update({cookie_fields[5]: cookie_fields[6]})

        if not cookies:
            raise ValueError(f"No valid cookies found in {real_cookie_filepath}")

    return cookies
