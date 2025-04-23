# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/exceptions/exceptions.py
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
import warnings

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'CarlogttLibraryError',
    'AwsSigV4SessionError',
    'CryptographyError',
    'SimTError',
    'SimTHandlerError',
    'MiradorError',
    'PipelinesError',
    'BindleError',
    'LoggerError',
    'RedisCacheManagerError',
    'DatabaseError',
    'SQLiteError',
    'MySQLError',
    'PostgresError',
    'DynamoDBError',
    'DynamoDBConflictError',
    'S3Error',
    'SecretsManagerError',
    'KMSError',
    'CloudFrontError',
    'EC2Error',
    'LambdaError',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class CarlogttLibraryError(Exception):
    """
    Custom exception class for CarlogttLibrary, providing enhanced
    functionality for error handling and reporting.
    """

    def __init__(self, *args) -> None:
        super().__init__(*args)

    def to_dict(self) -> dict[str, str]:
        """
        Converts the exception to a dictionary.

        :return: A dictionary with 'exception' as a key and the string
                 representation of the exception as its value.
        """

        response = {'exception': repr(self)}

        return response

    def to_json(self) -> str:
        """
        Converts the exception to a JSON string.

        :return: A JSON string representation of the exception, making
                 it suitable for logging or transmitting as part of an
                 API response.
        """

        response = json.dumps(self.to_dict())

        return response


class SimTError(CarlogttLibraryError):
    """
    This is the base exception class to handle SimTicket errors.
    """


class SimTHandlerError(SimTError):
    """
    DEPRECATED: Use SimTError instead.
    This subclass only exists for backward compatibility.
    """

    def __init__(self, *args):
        # Issue a DeprecationWarning at runtime
        msg = (
            f"[DEPRECATED] '{__package__}' class 'SimTHandlerError' is deprecated. Use"
            " 'SimTError' instead."
        )

        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        module_logger.warning(msg)

        super().__init__(*args)


class MiradorError(CarlogttLibraryError):
    """
    This is the base exception class to handle Mirador errors.
    """


class PipelinesError(CarlogttLibraryError):
    """
    This is the base exception class to handle Pipelines errors.
    """


class BindleError(CarlogttLibraryError):
    """
    This is the base exception class to handle Bindle errors.
    """


class AwsSigV4SessionError(CarlogttLibraryError):
    """
    This is the base exception class to handle AwsSigV4Session errors.
    """


class CryptographyError(CarlogttLibraryError):
    """
    This is the base exception class to handle Cryptography errors.
    """


class LoggerError(CarlogttLibraryError):
    """
    This is the base exception class to handle Logger errors.
    """


class RedisCacheManagerError(CarlogttLibraryError):
    """
    This is the base exception class to handle RedisCacheManager
    errors.
    """


class DatabaseError(CarlogttLibraryError):
    """
    This is the base exception class to handle Database errors.
    """


class SQLiteError(DatabaseError):
    """
    This is the base exception class to handle SQLite errors.
    """


class MySQLError(DatabaseError):
    """
    This is the base exception class to handle MySQL errors.
    """


class PostgresError(DatabaseError):
    """
    This is the base exception class to handle PostgreSQL errors.
    """


class DynamoDBError(DatabaseError):
    """
    This is the base exception class to handle DynamoDB errors.
    """


class DynamoDBConflictError(DynamoDBError):
    """
    This is the base exception class to handle DynamoDB Conflict errors.
    """


class S3Error(CarlogttLibraryError):
    """
    This is the base exception class to handle S3 errors.
    """


class SecretsManagerError(CarlogttLibraryError):
    """
    This is the base exception class to handle SecretsManager errors.
    """


class KMSError(CarlogttLibraryError):
    """
    This is the base exception class to handle KMS errors.
    """


class CloudFrontError(CarlogttLibraryError):
    """
    This is the base exception class to handle CloudFront errors.
    """


class EC2Error(CarlogttLibraryError):
    """
    This is the base exception class to handle EC2 errors.
    """


class LambdaError(CarlogttLibraryError):
    """
    This is the base exception class to handle Lambda errors.
    """
