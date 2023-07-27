# MODULE NAME ----------------------------------------------------------------------------------------------------------
# __init__.py -> my_utils_library
# ----------------------------------------------------------------------------------------------------------------------

"""
my_utils_library is a collection of utility functions designed to simplify common tasks in Python.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------

# Imports for all the modules except for utils have been disables as the objective of this package is to be used
# with specific submodule imports.
# i.e. import my_utils_library.database to access the database utils.
# i.e. import my_utils_library.logger to access the logger utils.
from .utils import *

# END IMPORTS ----------------------------------------------------------------------------------------------------------
