# MODULE NAME ----------------------------------------------------------------------------------------------------------
# db_exceptions.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module provides a collection of custom exception classes that can be used to handle specific error scenarios in a
more precise and controlled manner. These exceptions are tailored to the needs of the application and can be raised
when certain exceptional conditions occur during the program's execution.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.


# END IMPORTS ----------------------------------------------------------------------------------------------------------


class MySQLConnectionError(Exception):
    """This is the base exception class to handle MySQL connection errors"""


class SQLiteConnectionError(Exception):
    """This is the base exception class to handle SQLite connection errors"""


class DynamoDBConnectionError(Exception):
    """This is the base exception class to handle DynamoDB connection errors."""


if __name__ == '__main__':
    pass
