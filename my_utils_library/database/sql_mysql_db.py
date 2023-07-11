# MODULE NAME ----------------------------------------------------------------------------------------------------------
# db.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains the database classes for the application.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Generator

# Third Party Library Imports ------------------------------------------------------------------------------------------
import mysql.connector

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------
from .. import _config, utils
from ..exceptions import db_exceptions

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


class Database(ABC):
    @abstractmethod
    def open_db_connection(self) -> None:
        pass

    @abstractmethod
    def close_db_connection(self) -> None:
        pass

    @abstractmethod
    def send_to_db(self, sql_query: str, sql_values: tuple | str, db_is_open: bool = False) -> None:
        pass

    @abstractmethod
    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False, db_is_open: bool = False
    ) -> Generator[dict[str, str], None, None]:
        pass


class MySQL(Database):
    def __init__(self):
        self._db_connection = None

    @utils.retry_decorator(exception_to_check=db_exceptions.MySQLConnectionError)
    def open_db_connection(self) -> None:
        try:
            self._db_connection = mysql.connector.connect(
                host=_config.HOST,
                user=_config.USERNAME,
                password=_config.PASSWORD,
                port=_config.PORT,
                database=_config.DATABASE_SCHEMA,
            )

        except mysql.connector.Error as e:
            message = f"While connecting to {_config.HOST!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.MySQLConnectionError(message) from e

    @utils.retry_decorator(exception_to_check=db_exceptions.MySQLConnectionError)
    def close_db_connection(self) -> None:
        try:
            self._db_connection.close()

        except mysql.connector.Error as e:
            message = f"While closing {_config.HOST!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.MySQLConnectionError(message) from e

    def send_to_db(self, sql_query: str, sql_values: tuple | str, db_is_open: bool = False) -> None:
        if not db_is_open:
            self.open_db_connection()

        try:
            db_cursor = self._db_connection.cursor(prepared=True, dictionary=True)
            db_cursor.execute(sql_query, sql_values)

            self._db_connection.commit()
            module_logger.info("Database upload successful!")

        except mysql.connector.OperationalError as e:
            message = f"While sending to {_config.HOST!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.MySQLConnectionError(message) from e

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()

    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False, db_is_open: bool = False
    ) -> Generator[dict[str, str], None, None]:
        if not db_is_open:
            self.open_db_connection()

        try:
            db_cursor = self._db_connection.cursor(prepared=True, dictionary=True)
            db_cursor.execute(sql_query, sql_values)

            if fetch_one:
                for row in db_cursor:
                    yield row
                    break

            else:
                for row in db_cursor:
                    yield row

        except mysql.connector.OperationalError as e:
            message = f"While fetching from {_config.HOST!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.MySQLConnectionError(message) from e

        # This Exception handles the case where the table is not found.
        except mysql.connector.errors.ProgrammingError as e:
            module_logger.error(f"While connecting to {_config.HOST!r} operation failed! error: {str(e)}")

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()


class SQLite(Database):
    def __init__(self):
        self._db_connection = None

    def open_db_connection(self) -> None:
        try:
            self._db_connection = sqlite3.connect(_config.SQLITE_DB_PATH)
            # Row to the row_factory of connection creates what some people call a 'dictionary cursor'
            # Instead of tuples it starts returning 'dictionary'
            self._db_connection.row_factory = sqlite3.Row

        except sqlite3.OperationalError as e:
            message = f"While connecting to {_config.SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.SQLiteConnectionError(message) from e

    def close_db_connection(self) -> None:
        try:
            self._db_connection.close()

        except sqlite3.OperationalError as e:
            message = f"While closing {_config.SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.SQLiteConnectionError(message) from e

    def send_to_db(self, sql_query: str, sql_values: tuple | str, db_is_open: bool = False) -> None:
        if not db_is_open:
            self.open_db_connection()

        try:
            db_cursor = self._db_connection.cursor()
            db_cursor.execute(sql_query, sql_values)

            db_cursor.connection.commit()
            module_logger.info(f"Database upload successful!")

        except sqlite3.OperationalError as e:
            message = f"While sending to {_config.SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.SQLiteConnectionError(message) from e

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()

    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False, db_is_open: bool = False
    ) -> Generator[dict[str, str], None, None]:
        if not db_is_open:
            self.open_db_connection()

        try:
            db_cursor = self._db_connection.cursor()
            db_cursor.execute(sql_query, sql_values)

            # The dict() converts the sqlite3.Row object, created by row_factory, into a dictionary
            if fetch_one:
                for row in db_cursor:
                    yield dict(row)
                    break

            else:
                for row in db_cursor:
                    yield dict(row)

        except sqlite3.OperationalError as e:
            message = f"While fetching from {_config.SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            module_logger.error(message)
            raise db_exceptions.SQLiteConnectionError(message) from e

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()
