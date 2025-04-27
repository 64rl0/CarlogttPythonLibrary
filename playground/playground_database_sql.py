# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/playground_database_sql.py
# Created 2/20/25 - 12:54 PM UK Time (London) by carlogtt
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
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
from pprint import pprint

# Third Party Library Imports
from _playground_base import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)

# Type aliases
#


mysql_db = mylib.MySQL(
    host="fake_host",
    user="fake_user",
    password="fake_pass",
    port="9999",
    database_schema="fake_db",
)


def sql_query():
    sql_query = 'INSERT INTO `table` (`string`, `int`, `none`, `float`) VALUES (?, ?, ?, ?)'
    sql_values = ('hello', 123, None, 23.5)

    mysql_db.send_to_db(sql_query=sql_query, sql_values=sql_values)


if __name__ == '__main__':
    funcs = [
        # ,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
