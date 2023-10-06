# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# db_utils.py
# Created 7/27/23 - 7:02 AM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains utility functions to work with databases.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, Generic

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


def sql_query_reader(file_path: str | Path) -> str:
    query = Path(file_path).read_text()

    return query
