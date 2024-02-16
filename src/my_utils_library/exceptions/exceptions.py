# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

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
import json
import logging

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'MyLibraryException',
    'DatabaseError',
    'SQLiteError',
    'MySQLError',
    'DynamoDBError',
    'DynamoDBUpdateConflictError',
    'S3Error',
    'SecretsManagerError',
    'CloudFrontError',
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


class S3Error(MyLibraryException):
    """
    This is the base exception class to handle S3 errors.
    """


class SecretsManagerError(MyLibraryException):
    """
    This is the base exception class to handle SecretsManager errors.
    """


class CloudFrontError(MyLibraryException):
    """
    This is the base exception class to handle CloudFront errors.
    """


class SimTHandlerError(MyLibraryException):
    """
    This is the base exception class to handle SimTicket Handler errors.
    """
