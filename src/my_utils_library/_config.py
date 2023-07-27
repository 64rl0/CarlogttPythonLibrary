# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# _config.py
# Created 7/3/23 - 6:41 AM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module handles the loading of environment variables which are used as configuration values in other parts of the
application. Environment variables are used for configurations to keep sensitive information like API keys, database
URIs, and other credentials out of the codebase.

This module uses the os library to access environment variables using os.getenv(), and stores these values as
module-level constants which can be imported into other modules as needed.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import os
import sys
from io import StringIO

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# Reading environment variables from the environment

# mySQL configuration
HOST = os.environ.get('MYSQL_HOST', '')
USERNAME = os.environ.get('MYSQL_USERNAME', '')
PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
PORT = os.environ.get('MYSQL_PORT', '')
DATABASE_SCHEMA = os.environ.get('MYSQL_DATABASE_SCHEMA', '')

# sqlite configuration
SQLITE_DB_FILENAME = os.environ.get('SQLITE_DB_FILENAME', '')
SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', '')

# DynamoDB configuration
AWS_ENVIRONMENT = os.environ.get('AWS_ENVIRONMENT', '')

# Logger configuration
LOGGER_NAME = os.environ.get('LOGGER_NAME', '')
LOGGER_PATH = os.environ.get("LOGGER_PATH", '')
LOGGER_LEVEL = os.environ.get('LOGGER_LEVEL', '')
CONSOLE_STREAM = sys.stderr
STRINGIO_STREAM = StringIO()

# Fernet encryption configuration
FERNET_KEY = os.environ.get('FERNET_KEY', '')


if __name__ == '__main__':
    pass
