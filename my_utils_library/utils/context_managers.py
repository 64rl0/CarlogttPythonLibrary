# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# context_managers.py
# Created 7/2/23 - 2:21 PM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module ...
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
from contextlib import contextmanager
from typing import Type

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------
from ..logger import master_logger

# END IMPORTS ----------------------------------------------------------------------------------------------------------

# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
my_app_logger = master_logger.get_child_logger(__name__)


@contextmanager
def suppress_errors(*exceptions: Type[Exception]):
    try:
        yield
    except exceptions:
        pass


if __name__ == '__main__':
    pass
    # print(*suppress_errors())
    # with suppress_errors(ValueError):
    #     raise ValueError()
