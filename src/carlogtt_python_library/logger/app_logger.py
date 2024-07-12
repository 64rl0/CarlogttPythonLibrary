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

10 - DEBUG: Detailed information, typically of interest only when
diagnosing problems.

20 - INFO: Confirmation that things are working as expected.

30 - WARNING: An indication that something unexpected happened, or
indicative of some problem in the near future (e.g. ‘disk space low’).
The software is still working as expected.

40 - ERROR: Due to a more serious problem, the software has not been
able to perform some function.

50 - CRITICAL: A serious error, indicating that the program itself may
be unable to continue running.
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
import io
import logging
import pathlib
import sys
import uuid
from typing import Optional, TextIO, Union

# Local Folder (Relative) Imports
from .. import utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Logger',
]


class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter to add color codes to log messages.
    This formatter extends the standard logging
    Formatter class, adding color to log messages for terminal output
    that supports ANSI color codes.
    """

    _COLOR_RESET = utils.cli_end

    def __init__(self, log_color: str, *args, **kwargs):
        self._log_color = log_color
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record and adds color codes to the message.

        :param record: The log record to be formatted.
        :return: A color-coded log message string.
        """

        log_message = super().format(record)
        log_formatted = f"{self._log_color}{log_message}{self._COLOR_RESET}"

        return log_formatted


class Level(enum.Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    """
    Custom logger class for application-wide logging with support for
    file, console, and StringIO logging. Provides colored formatting
    and hierarchical logging capabilities.

    :param log_name: The name of the logger, used as a namespace for
           hierarchical logging.
    :param log_level: The minimum log level for the logger. Messages
           below this level will not be logged.
    :param log_color: Specifies the color of the log messages. This is
           used to set the initial color for all log messages handled
           by this logger. The default color is 'default', which
           applies no additional color formatting. Available colors
           include 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan'.
    :param log_fmt: The log format.
    """

    LOG_COLORS = {
        'default': utils.cli_end,
        'red': utils.cli_red,
        'green': utils.cli_green,
        'yellow': utils.cli_yellow,
        'blue': utils.cli_blue,
        'magenta': utils.cli_magenta,
        'cyan': utils.cli_cyan,
    }
    LOG_FMT = '%(levelname)-8s | %(asctime)s | %(pathname)s:%(lineno)d | %(message)s'

    def __init__(
        self,
        log_name: str,
        log_level: str,
        log_color: str = 'default',
        log_fmt: Optional[str] = None,
    ):
        if log_color not in self.LOG_COLORS:
            raise ValueError(
                f"log_color must be one of the following values: {self.LOG_COLORS.keys()}"
            )

        self.app_logger = logging.getLogger(log_name)
        self.app_logger.setLevel(log_level)
        self.formatter = ColoredFormatter(
            log_color=self.LOG_COLORS[log_color],
            style='%',
            fmt=log_fmt or self.LOG_FMT,
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def add_file_handler(self, logger_file_path: Union[str, pathlib.Path]) -> None:
        """
        Adds a file handler to log messages to a file.

        :param logger_file_path: The path to the log file. Can be a
               string or a pathlib.Path object.
        """

        file_handler = logging.FileHandler(filename=logger_file_path, mode="a+")
        file_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(file_handler)

    def add_console_handler(self, logger_console_stream: Optional[TextIO] = None) -> None:
        """
        Adds a console handler to log messages to the console.

        :param logger_console_stream: The stream to log messages to.
               Typically, sys.stdout or sys.stderr.
               If not specified, sys.stderr is used.
        """

        if logger_console_stream is None:
            logger_console_stream = sys.stderr

        console_handler = logging.StreamHandler(stream=logger_console_stream)
        console_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(console_handler)

    def add_stringio_handler(self, logger_stringio_stream: Optional[TextIO] = None) -> None:
        """
        Adds a StringIO handler to log messages to a StringIO stream.

        :param logger_stringio_stream: The StringIO stream to log
               messages to.
               If not specified, io.StringIO is used.
        """

        if logger_stringio_stream is None:
            logger_stringio_stream = io.StringIO()

        stringio_handler = logging.StreamHandler(stream=logger_stringio_stream)
        stringio_handler.setFormatter(self.formatter)
        self.app_logger.addHandler(stringio_handler)

    def get_child_logger(self, log_name: str) -> logging.Logger:
        """
        Creates and returns a child logger with a specific name.

        :param log_name: The name of the child logger. This name is
               appended to the parent logger's name.
        :return: A new child logger instance.
        """

        new_child_logger = self.app_logger.getChild(log_name)

        return new_child_logger

    def log_with_exception_id(self, log_level: Level, message: str = "") -> None:
        """
        Logs a message at a specific log level with an exception ID.

        :param log_level: The logging level for the message.
        :param message: The log message.
        """

        exc_id = "EID-" + str(uuid.uuid4().hex)
        message_with_exception_id = f"{exc_id} | {message}"

        self.app_logger.log(level=log_level.value, msg=message_with_exception_id)
