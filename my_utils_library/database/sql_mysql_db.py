# MODULE NAME ----------------------------------------------------------------------------------------------------------
# db.py
# ----------------------------------------------------------------------------------------------------------------------

"""
This module contains the database classes for the application.
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import os
import sqlite3
from abc import ABC, abstractmethod

# Third Party Library Imports ------------------------------------------------------------------------------------------
import mysql.connector

# Local Application Imports --------------------------------------------------------------------------------------------
from CarloCodes.my_utils_library import exceptions
from CarloCodes.my_utils_library.my_utils_library import utils
from CarloCodes.my_utils_library.my_utils_library.logger import master_logger

# END IMPORTS ----------------------------------------------------------------------------------------------------------

# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
my_app_logger = master_logger.get_child_logger(__name__)

# mySQL config
HOST = os.environ.get('MYSQL_HOST')
USERNAME = os.environ.get('MYSQL_USERNAME')
PASSWORD = os.environ.get('MYSQL_PASSWORD')
PORT = os.environ.get('MYSQL_PORT')
DATABASE_SCHEMA = os.environ.get('MYSQL_DATABASE_SCHEMA')

# sqlite config
SQLITE_DB_FILENAME = os.environ.get('SQLITE_DB_FILENAME')
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), SQLITE_DB_FILENAME)


class Database(ABC):
    @abstractmethod
    def _open_db_connection(self) -> None:
        pass

    @abstractmethod
    def _close_db_connection(self) -> None:
        pass

    @abstractmethod
    def send_to_db(self, sql_query: str, sql_values: tuple | str) -> None:
        pass

    @abstractmethod
    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False
    ) -> list[dict[str, str], ...]:
        pass


class MySQLdatabase(Database):
    def __init__(self):
        self._db_connection = None
        self._db_cursor = None

    @utils.retry_decorator(exception_to_check=exceptions.MySQLConnectionError, logger=my_app_logger)
    def _open_db_connection(self) -> None:
        try:
            self._db_connection = mysql.connector.connect(
                host=HOST, user=USERNAME, password=PASSWORD, port=PORT, database=DATABASE_SCHEMA
            )
            if self._db_connection.is_connected():
                self._db_cursor = self._db_connection.cursor(prepared=True, dictionary=True)
        except mysql.connector.Error as e:
            message = f"While connecting to {HOST!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.MySQLConnectionError(message) from e

    @utils.retry_decorator(exception_to_check=exceptions.MySQLConnectionError, logger=my_app_logger)
    def _close_db_connection(self) -> None:
        try:
            self._db_cursor.close()
            self._db_connection.close()
        except mysql.connector.Error as e:
            message = f"While connecting to {HOST!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.MySQLConnectionError(message) from e

    # TODO: @retry_decorator(exception_to_check=MySQLConnectionError) - this goes in a loop of 4x4 16 times
    def send_to_db(self, sql_query: str, sql_values: tuple | str) -> None:
        self._open_db_connection()
        try:
            self._db_cursor.execute(sql_query, sql_values)
            self._db_connection.commit()
            my_app_logger.info("Database upload successful!")
        except mysql.connector.OperationalError as e:
            message = f"While connecting to {HOST!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.MySQLConnectionError(message) from e
        finally:
            self._close_db_connection()

    # TODO: @retry_decorator(exception_to_check=MySQLConnectionError) - this goes in a loop of 4x4 16 times
    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False
    ) -> list[dict[str, str], ...]:
        self._open_db_connection()
        try:
            self._db_cursor.execute(sql_query, sql_values)
            if fetch_one:
                record_objects = self._db_cursor.fetchone()
            else:
                record_objects = self._db_cursor.fetchall()
            return record_objects
        except mysql.connector.OperationalError as e:
            message = f"While connecting to {HOST!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.MySQLConnectionError(message) from e
        # This Exception handles the case where the table is not found.
        except mysql.connector.errors.ProgrammingError as e:
            my_app_logger.error(f"While connecting to {HOST!r} operation failed! error: {str(e)}")
        finally:
            self._close_db_connection()


class SQLite(Database):
    def __init__(self):
        self._db_connection = None
        self._db_cursor = None

    def _open_db_connection(self) -> None:
        try:
            self._db_connection = sqlite3.connect(SQLITE_DB_PATH)
            # Row to the row_factory of connection creates what some people call a 'dictionary cursor'
            # Instead of tuples it starts returning 'dictionary'
            self._db_connection.row_factory = sqlite3.Row
            self._db_cursor = self._db_connection.cursor()
        except sqlite3.OperationalError as e:
            message = f"While connecting to {SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.SQLiteConnectionError(message) from e

    def _close_db_connection(self) -> None:
        self._db_cursor.close()
        self._db_connection.close()

    def send_to_db(self, sql_query: str, sql_values: tuple | str) -> None:
        self._open_db_connection()
        try:
            self._db_cursor.execute(sql_query, sql_values)
            self._db_cursor.connection.commit()
            my_app_logger.info(f"Database upload successful!")
        except sqlite3.OperationalError as e:
            message = f"While connecting to {SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.SQLiteConnectionError(message) from e
        finally:
            self._close_db_connection()

    def fetch_from_db(
        self, sql_query: str, sql_values: tuple | str, *, fetch_one: bool = False
    ) -> list[dict[str, str], ...]:
        self._open_db_connection()
        try:
            self._db_cursor.execute(sql_query, sql_values)
            if fetch_one:
                record_objects: sqlite3.Row = self._db_cursor.fetchone()
                # This converts the sqlite3.Row object, created by row_factory, into a dictionary
                record_objects: list[dict[str, str]] = [dict(record_objects)]
            else:
                record_objects: list[sqlite3.Row, ...] = self._db_cursor.fetchall()
                # This converts the sqlite3.Row object, created by row_factory, into a dictionary
                record_objects: list[dict[str, str], ...] = [dict(i) for i in record_objects]
            return record_objects
        except sqlite3.OperationalError as e:
            message = f"While connecting to {SQLITE_DB_FILENAME!r} operation failed! error: {str(e)}"
            my_app_logger.error(message)
            raise exceptions.SQLiteConnectionError(message) from e
        finally:
            self._close_db_connection()
