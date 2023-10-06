# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# miscs.py
# Created 8/9/23 - 11:34 AM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module provides a set of various utilities.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import ctypes
import logging

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


def ref_count(obj_id: int) -> int:
    return ctypes.c_long.from_address(obj_id).value
