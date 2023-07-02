# MODULE NAME ----------------------------------------------------------------------------------------------------------
# string_tools.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains useful functions to work with strings.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import random
import string

# Local Application Imports --------------------------------------------------------------------------------------------
from ..logger import master_logger

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
my_app_logger = master_logger.get_child_logger(__name__)


def get_random_string(length: int) -> str:
    secret = string.ascii_letters + string.digits
    return ''.join(random.choice(secret) for _ in range(length))


if __name__ == '__main__':
    pass
