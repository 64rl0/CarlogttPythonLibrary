# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/logger/app_logger.py
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
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Logger',
    'LoggerLevel',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class _ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter to add color codes to log messages.
    This formatter extends the standard logging
    Formatter class, adding color to log messages for terminal output
    that supports ANSI color codes.
    """

    _COLOR_RESET = utils.CLIStyle.CLI_END

    def __init__(self, log_color: str, *args, **kwargs):
        self._log_color = log_color
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record and adds color codes to the message.

        :param record: The log record to be formatted.
        :return: A color-coded log message string.
        """

        # Inject a UUID if not already present
        if not hasattr(record, 'log_id'):
            record.log_id = str(uuid.uuid4().hex)

        log_message = super().format(record)
        log_formatted = f"{self._log_color}{log_message}{self._COLOR_RESET}"

        return log_formatted


class LoggerLevel(enum.Enum):
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

    _LOG_COLORS = {
        'default': utils.CLIStyle.CLI_END,
        'red': utils.CLIStyle.CLI_RED,
        'green': utils.CLIStyle.CLI_GREEN,
        'yellow': utils.CLIStyle.CLI_YELLOW,
        'blue': utils.CLIStyle.CLI_BLUE,
        'magenta': utils.CLIStyle.CLI_MAGENTA,
        'cyan': utils.CLIStyle.CLI_CYAN,
    }
    _LOG_FMT = '%(levelname)-8s | %(asctime)s | %(log_id)s | %(pathname)s:%(lineno)d | %(message)s'

    def __init__(
        self,
        log_name: str,
        log_level: Union[str, LoggerLevel],
        log_color: str = 'default',
        log_fmt: Optional[str] = None,
    ) -> None:
        if log_color not in self._LOG_COLORS:
            raise exceptions.LoggerError(
                f"log_color must be one of the following values: {self._LOG_COLORS.keys()}"
            )

        self._log_level_enum = self._parse_log_level(log_level=log_level)

        self.app_logger = logging.getLogger(log_name)
        self.app_logger.setLevel(self._log_level_enum.value)

        self.formatter = _ColoredFormatter(
            log_color=self._LOG_COLORS[log_color],
            style='%',
            fmt=log_fmt or self._LOG_FMT,
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        self._root_logger = logging.getLogger()
        self._root_logger_attached = False

    def attach_root_logger(self) -> None:
        """
        Attach the current handlers and logging level of 'app_logger'
        to the root logger.

        This ensures that calls to the Python root logger
        (e.g. logging.info(), logging.debug()) will produce output
        that matches the configuration of 'app_logger'.
        """

        # Copy app_logger level to root_logger
        self._root_logger.setLevel(self.app_logger.level)

        # Copy app_logger handlers to root_logger
        for handler in self.app_logger.handlers:
            self._root_logger.addHandler(handler)

        # Remove app_logger handlers to avoid logging duplication
        self.app_logger.handlers = []

        # Mark root logger as active
        logging.debug("root_logger attached to module_logger")
        self._root_logger_attached = True

    def detach_root_logger(self) -> None:
        """
        Detach custom handlers from the root logger and revert to a
        higher-level filter (WARNING).

        This effectively disables or limits root-logger output.
        Any modules still calling logging.info() or logging.debug()
        against the root logger will no longer produce output
        (or be limited to WARNING+).
        """

        # Copy root_logger level to app_logger
        self.app_logger.setLevel(self._root_logger.level)

        # Reset the default root logger level
        self._root_logger.setLevel(LoggerLevel.WARNING.value)

        # Copy root_logger handlers to app_logger
        for handler in self._root_logger.handlers:
            self.app_logger.addHandler(handler)

        # Remove root_logger handlers
        self._root_logger.handlers = []

        # Mark root logger as disabled
        logging.debug("root_logger detached from module_logger")
        self._root_logger_attached = False

    def add_file_handler(self, logger_file_path: Union[str, pathlib.Path]) -> None:
        """
        Adds a file handler to log messages to a file.

        :param logger_file_path: The path to the log file. Can be a
               string or a pathlib.Path object.
        """

        file_handler = logging.FileHandler(filename=logger_file_path, mode='a+')
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

    def change_logger_level(self, log_level: Union[str, LoggerLevel]) -> None:
        """
        Change the logger's effective level at runtime.

        This method updates both the logger instance's level and all
        registered handlers' levels to the newly specified value.

        :param log_level: The desired new log level. It can be either:
            - A :class:`LoggerLevel` enum member
            (e.g. ``LoggerLevel.DEBUG``)
            - A string representing one of the valid log level names
            (e.g. ``"DEBUG"``, ``"INFO"``)
        :raises LoggerError: If the provided string does not match any
            :class:`LoggerLevel` member.
        :return: None
        """

        # Update instance value
        self._log_level_enum = self._parse_log_level(log_level=log_level)

        # Get active logger
        if self._root_logger_attached:
            active_logger = self._root_logger
        else:
            active_logger = self.app_logger

        # Set app_logger new level
        active_logger.setLevel(self._log_level_enum.value)

        # Set all handlers new level
        for handler in active_logger.handlers:
            handler.setLevel(self._log_level_enum.value)

    def _parse_log_level(self, log_level: Union[str, LoggerLevel]) -> LoggerLevel:
        """
        Convert a string or LoggerLevel enum into a valid LoggerLevel.

        :param log_level: A string (e.g., 'INFO') or a LoggerLevel enum.
        :return: A LoggerLevel enum member.
        :raises LoggerError: If log_level is an invalid strig or if
            it's neither a string nor a LoggerLevel.
        """

        if isinstance(log_level, str):
            try:
                self._log_level_enum = LoggerLevel[log_level.upper()]

            except KeyError:
                raise exceptions.LoggerError(
                    f"Invalid log_level '{log_level}'. Valid options:"
                    f" {', '.join(lvl.name for lvl in LoggerLevel)}"
                ) from None

        elif isinstance(log_level, LoggerLevel):
            self._log_level_enum = log_level

        else:
            raise exceptions.LoggerError("log_level must be either a string or LoggerLevel.")

        return self._log_level_enum
