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

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'MyLibraryException',
    'SimTHandlerError',
    'RedisCacheManagerError',
    'DatabaseError',
    'SQLiteError',
    'MySQLError',
    'DynamoDBError',
    'DynamoDBConflictError',
    'S3Error',
    'SecretsManagerError',
    'KMSError',
    'CloudFrontError',
    'EC2Error',
    'LambdaError',
]


class MyLibraryException(Exception):
    """
    Custom exception class for MyLibrary, providing enhanced
    functionality for error handling and reporting. This class extends
    the standard Python Exception class, adding methods for converting
    exception details to a dictionary or JSON string, facilitating
    easier logging and serialization of error information.
    """

    def __init__(self, *args) -> None:
        super().__init__(*args)

    def to_dict(self) -> dict[str, str]:
        """
        Converts the exception to a dictionary.

        :return: A dictionary with 'exception' as a key and the string
                 representation of the exception as its value.
        """

        return {
            'exception': repr(self),
        }

    def to_json(self) -> str:
        """
        Converts the exception to a JSON string.

        :return: A JSON string representation of the exception, making
                 it suitable for logging or transmitting as part of an
                 API response.
        """

        return json.dumps(self.to_dict())


class SimTHandlerError(MyLibraryException):
    """
    This is the base exception class to handle SimTicket Handler errors.
    """


class RedisCacheManagerError(MyLibraryException):
    """
    This is the base exception class to handle redis cache manager
    errors.
    """


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


class DynamoDBConflictError(DynamoDBError):
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


class KMSError(MyLibraryException):
    """
    This is the base exception class to handle Key Management Service
    (KMS) errors.
    """


class CloudFrontError(MyLibraryException):
    """
    This is the base exception class to handle CloudFront errors.
    """


class EC2Error(MyLibraryException):
    """
    This is the base exception class to handle EC2 errors.
    """


class LambdaError(MyLibraryException):
    """
    This is the base exception class to handle Lambda errors.
    """
