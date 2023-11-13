# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# app_logger.py
# Created 9/29/23 - 1:44 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module contains the application logger class.
Guidelines for the application logger class are as follows:

# 10 - DEBUG:     Detailed information, typically of interest only when
                  diagnosing problems.
# 20 - INFO:      Confirmation that things are working as expected.
# 30 - WARNING:   An indication that something unexpected happened, or
                  indicative of some problem in the near future
                  (e.g. ‘disk space low’). The software is still
                  working as expected.
# 40 - ERROR:     Due to a more serious problem, the software has not
                  been able to perform some function.
# 50 - CRITICAL:  A serious error, indicating that the program itself
                  may be unable to continue running.
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
import enum
import logging
import pathlib
import uuid
from typing import Union

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Logger',
]


class ColoredFormatter(logging.Formatter):
    """
    Logging Formatter to add colors
    """

    COLORS = {
        'DEBUG': '\033[31m',  # red
        'INFO': '\033[31m',  # red
        'WARNING': '\033[31m',  # red
        'ERROR': '\033[31m',  # red
        'CRITICAL': '\033[31m',  # red
    }

    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        log_message = super().format(record)
        return f"{color}{log_message}{self.RESET}"


class Level(enum.Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    def __init__(self, log_name: str, log_level: str):
        self.app_logger = logging.getLogger(log_name)
        self.app_logger.setLevel(log_level)
        self.formatter = ColoredFormatter(
            style='%',
            fmt=(
                '%(name)-40s | %(funcName)-20s | %(lineno)d | %(asctime)s | %(levelname)-8s |'
                ' %(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def add_file_handler(self, logger_file_path: Union[str, pathlib.Path]) -> None:
        """
        create a file handler which logs even debug messages
        """

        file_handler = logging.FileHandler(logger_file_path, mode="a+")
        file_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(file_handler)

    def add_console_handler(self, logger_console_stream) -> None:
        """
        create a console handler which logs even debug messages
        """

        console_handler = logging.StreamHandler(stream=logger_console_stream)
        console_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(console_handler)

    def add_stringio_handler(self, logger_stringio_stream) -> None:
        """
        create a string_io handler which logs even debug messages
        """

        stringio_handler = logging.StreamHandler(stream=logger_stringio_stream)
        stringio_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(stringio_handler)

    def get_child_logger(self, log_name: str) -> logging.Logger:
        new_child_logger = self.app_logger.getChild(log_name)
        return new_child_logger

    # this method is not currently being used so just making it private
    # for now
    def _log(self, log_level: Level, message: str = "") -> None:
        message_with_exception_id = f"{Logger._generate_exception_id()} | {message}"
        self.app_logger.log(level=log_level.value, msg=message_with_exception_id)

    @staticmethod
    def _generate_exception_id() -> str:
        return "ID-" + str(uuid.uuid4().hex)
