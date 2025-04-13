# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/database/database_utils.py
# Created 9/25/23 - 1:49 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
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
from pathlib import Path
from typing import Union

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'sql_query_reader',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


def sql_query_reader(file_path: Union[Path, str]) -> str:
    """
    Reads an SQL query from a file and returns it as a string.

    This function simplifies the process of loading SQL queries
    from files, avoiding the need for manual file handling. It supports
    both string paths and Pathlib Path objects as input.

    :param file_path: The path to the SQL file. This can be a string
           or a Pathlib Path object.
    :return: The content of the SQL file as a string.
    """

    query = Path(file_path).read_text()

    return query
