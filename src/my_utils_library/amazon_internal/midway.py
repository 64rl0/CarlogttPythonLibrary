# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# midway.py
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
import subprocess
import sys

# Local Folder (Relative) Imports
from .. import utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'cli_midway_auth',
]

# Setting up logger for current module
# module_logger =

# Type aliases
#


def cli_midway_auth(max_retries: int = 3):
    """
    Run mwinit -s as bash command.

    :param max_retries: The maximum number of total attempts.
           Default is 3.
    :return: None
    """

    for i in range(max_retries):
        # Run mwinit -s
        command = "mwinit -s || exit 1"

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
                print()
                print(
                    utils.red + utils.bold + "[ERROR] Authentication to Midway failed." + utils.end
                )
                print()
                sys.exit(1)

            print()
            print(
                utils.red
                + utils.bold
                + f"[ERROR] Authentication to Midway failed. Retrying {i+2}..."
                + utils.end
            )
            print()
