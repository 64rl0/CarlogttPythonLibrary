# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/midway.py
# Created 12/11/23 - 11:19 PM UK Time (London) by carlogtt

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
import shlex
import subprocess
import sys
import warnings
from typing import Optional

# Third Party Library Imports
import requests
from requests_midway import RequestsMidway

# Local Folder (Relative) Imports
from .. import utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'MidwayUtils',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class MidwayUtils:
    """
    A handler class for Midway utilities.
    """

    def __init__(self) -> None:
        self._auth: Optional[RequestsMidway] = None

    def _get_auth(self) -> RequestsMidway:
        """Get or create the shared RequestsMidway auth object."""
        if self._auth is None:
            self._auth = RequestsMidway()
        return self._auth

    def cli_midway_auth(self, max_retries: int = 3, options: str = "-s"):
        """
        Run mwinit -s as bash command.

        :param max_retries: The maximum number of total attempts.
               Default is 3.
        :param options: The options to pass to the mwinit command.
               Default is -s
        :return: None
        """

        # Build the argument list safely
        command = ["mwinit"]
        if options:
            command_args = shlex.split(options)
            command.extend(command_args)

        for i in range(max_retries):
            try:
                # Run the command using subprocess.Popen
                process = subprocess.Popen(command)
            except FileNotFoundError:
                print(
                    utils.CLIStyle.CLI_BOLD_RED
                    + "\n[ERROR] 'mwinit' command not found. Ensure it is installed and in your"
                    " PATH.\n"
                    + utils.CLIStyle.CLI_END,
                    flush=True,
                )
                sys.exit(1)

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
        Retrieves valid Midway cookies using MCS (RequestsMidway)
        authentication.
        Return a dictionary of cookie names and their values.

        .. deprecated:: 1.0
           Use RequestsMidway authentication instead. This method is
           maintained for backward compatibility but will be removed in
           a future version.

        :param cookie_filepath: Retained for backward compatibility only
               and ignored; MCS (RequestsMidway) now owns the Midway
               session and cookie state.
        :return: A dictionary where each key-value pair corresponds to a
                 cookie name and its value returned by Midway.
        """
        warnings.warn(
            "extract_valid_cookies() is deprecated. "
            "Use requests_midway.RequestsMidway() for authentication instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        del cookie_filepath

        response = requests.get(
            "https://midway-auth.amazon.com/robots.txt", auth=self._get_auth(), timeout=10
        )

        cookies: dict[str, str] = {
            cookie_name: cookie_value for cookie_name, cookie_value in response.cookies.items()
        }

        if not cookies:
            raise ValueError("No valid cookies found from Midway authentication")

        return cookies

    def validate_midway_session(self) -> bool:
        """
        Validate that Midway session token is not expired using MCS.

        :return: True if session is valid, False if expired.
        :raises: SystemExit if MCS library is not available.
        """
        try:
            # MCS library doesn't have type stubs, ignore mypy error
            from midway_client_suite_library_python.mcs_lib import (  # type: ignore[import-untyped]  # noqa: E501
                McsLib,
            )

            mcs = McsLib()
            result = mcs.get_session_token_expiration("midway-auth.amazon.com")
            return not result.is_expired

        except ImportError:
            print(
                utils.CLIStyle.CLI_BOLD_RED
                + "\n[ERROR] MCS library not available. "
                "Please ensure MidwayClientSuiteLibraryPython is installed.\n"
                + utils.CLIStyle.CLI_END,
                flush=True,
            )
            sys.exit(1)
