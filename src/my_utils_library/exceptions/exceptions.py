# MODULE DETAILS
# exceptions.py
# Created 9/25/23 - 6:34 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module provides a collection of custom exception classes that can
be used to handle specific error scenarios in a more precise and
controlled manner. These exceptions are tailored to the needs of the
library and can be raised when certain exceptional conditions occur
during the program's execution.

"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import json
import logging

# END IMPORTS


# List of public names in the module
__all__ = [
    'MyLibraryException',
    'DatabaseError',
    'SQLiteError',
    'MySQLError',
    'DynamoDBError',
    'DynamoDBUpdateConflictError',
    'SimTHandlerError',
]


class MyLibraryException(Exception):
    """
    This is the base exception for the AmzInventoryToolApp.
    """

    def __init__(self, *args) -> None:
        self.message = "Operation Failed!"
        self.error = repr(self)
        super().__init__(*args)

    def to_dict(self) -> dict[str, str]:
        return {
            'message': self.message,
            'error': self.error,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def log_exception(self) -> None:
        logging.error(repr(self))


class DatabaseError(MyLibraryException):
    """
    This is the base exception class to handle database errors.
    """


class SQLiteError(DatabaseError):
    """
    This is the base exception class to handle SQLite errors.
    """


class MySQLError(DatabaseError):
    """
    This is the base exception class to handle MySQL errors.
    """


class DynamoDBError(DatabaseError):
    """
    This is the base exception class to handle DynamoDB errors.
    """


class DynamoDBUpdateConflictError(DynamoDBError):
    """
    This is the base exception class to handle DynamoDB errors.
    """


class SimTHandlerError(MyLibraryException):
    """
    This is the base exception class to handle SimTicket Handler errors.
    """
