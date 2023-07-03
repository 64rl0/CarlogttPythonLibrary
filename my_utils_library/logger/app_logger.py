# MODULE NAME ----------------------------------------------------------------------------------------------------------
# app_logger.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains the application logger class.
Guidelines for the application logger class are as follows:

# 10 - DEBUG:     Detailed information, typically of interest only when diagnosing problems.
# 20 - INFO:      Confirmation that things are working as expected.
# 30 - WARNING:   An indication that something unexpected happened, or indicative of some problem in the near future
                  (e.g. ‘disk space low’). The software is still working as expected.
# 40 - ERROR:     Due to a more serious problem, the software has not been able to perform some function.
# 50 - CRITICAL:  A serious error, indicating that the program itself may be unable to continue running.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging
import os
import sys
import uuid
from enum import Enum
from io import StringIO

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------
from .. import config

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
__all__ = ["master_logger"]


class Level(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    def __init__(self, log_name: str, log_level: str):
        # create a logger object
        self.app_logger = logging.getLogger(log_name)
        self.app_logger.setLevel(log_level)
        self.formatter = logging.Formatter(
            style='%', fmt='%(name)-30s | %(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )

    def add_file_handler(self, logger_file_path: str):
        # create a file handler which logs even debug messages
        file_handler = logging.FileHandler(logger_file_path, mode="a+")
        file_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(file_handler)

    def add_console_handler(self, logger_console_stream):
        # create a console handler which logs even debug messages
        console_handler = logging.StreamHandler(stream=logger_console_stream)
        console_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(console_handler)

    def add_stringio_handler(self, logger_stringio_stream):
        # create a string_io handler which logs even debug messages
        stringio_handler = logging.StreamHandler(stream=logger_stringio_stream)
        stringio_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(stringio_handler)

    def log(self, log_level: Level, message: str = ""):
        message_with_exception_id = f"{Logger._generate_exception_id()} | {message}"
        self.app_logger.log(level=log_level.value, msg=message_with_exception_id)

    def get_child_logger(self, log_name: str) -> logging.Logger:
        new_child_logger = self.app_logger.getChild(log_name)
        return new_child_logger

    # This method is not in use at the moment
    @staticmethod
    def _generate_exception_id() -> str:
        return "ID-" + str(uuid.uuid4().hex)


# Initiate master logger for Flask app
master_logger = Logger(config.LOGGER_NAME, config.LOGGER_LEVEL)
master_logger.add_file_handler(config.LOGGER_PATH)
master_logger.add_console_handler(config.CONSOLE_STREAM)
master_logger.add_stringio_handler(config.STRINGIO_STREAM)


if __name__ == '__main__':
    # Setting up logger for current module for testing purposes only when run as main
    my_app_logger = master_logger.get_child_logger(__name__)
    my_app_logger.error("this is a test log")
