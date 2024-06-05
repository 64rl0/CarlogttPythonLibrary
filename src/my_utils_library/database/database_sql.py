# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# database_sql.py
# Created 9/25/23 - 2:34 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
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
import abc
import logging
import pathlib
import sqlite3
from collections.abc import Generator
from typing import Optional, Union

# Third Party Library Imports
import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Database',
    'MySQL',
    'SQLite',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
MySQLConn = Union[MySQLConnectionAbstract, PooledMySQLConnection]


class Database(abc.ABC):
    @abc.abstractmethod
    def open_db_connection(self) -> None:
        pass

    @abc.abstractmethod
    def close_db_connection(self) -> None:
        pass

    @abc.abstractmethod
    def send_to_db(self, sql_query: str, sql_values: Union[tuple[str, ...], str]) -> None:
        pass

    @abc.abstractmethod
    def fetch_from_db(
        self, sql_query: str, sql_values: Union[tuple[str, ...], str], *, fetch_one: bool = False
    ) -> Generator[dict[str, str], None, None]:
        pass


class MySQL(Database):
    """
    Handles MySQL database connections.

    :param host: Hostname or IP address of the MySQL server.
    :param user: Username to authenticate with the MySQL server.
    :param password: Password to authenticate with the MySQL server.
    :param port: Port number of the MySQL server.
    :param database_schema: Name of the database schema to use.
    """

    def __init__(self, host: str, user: str, password: str, port: str, database_schema: str):
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self._database_schema = database_schema
        self._db_connection: Optional[MySQLConn] = None

    @property
    def _db_active_connection(self) -> MySQLConn:
        """
        Gets the active db connection. If there is not an active
        connection it creates one.
        """

        if not self._db_connection:
            self.open_db_connection()

        assert isinstance(self._db_connection, MySQLConnectionAbstract) or isinstance(
            self._db_connection, PooledMySQLConnection
        ), "Expected self._db_connection to be type MySQLConn"

        return self._db_connection

    @_db_active_connection.setter
    def _db_active_connection(self, value) -> None:
        """
        Sets the active db connection.
        """

        self._db_connection = value

    @utils.retry(exceptions.MySQLError)
    def open_db_connection(self) -> None:
        """
        Open a MySQL db connection.
        Auto retry up to 4 times on connection error.

        :raise MySQLError: If the operation fails.
        """

        try:
            self._db_active_connection = mysql.connector.connect(
                host=self._host,
                user=self._user,
                password=self._password,
                port=self._port,
                database=self._database_schema,
            )

        except mysql.connector.Error as ex:
            message = f"While connecting to [{self._host}] operation failed! traceback: {repr(ex)}"
            module_logger.error(message)
            raise exceptions.MySQLError(message)

    @utils.retry(exceptions.MySQLError)
    def close_db_connection(self) -> None:
        """
        Close the MySQL db connection.
        Auto retry up to 4 times on connection error.

        :raise MySQLError: If the operation fails.
        """

        try:
            self._db_active_connection.close()

        except mysql.connector.Error as ex:
            message = f"While closing [{self._host}] operation failed! traceback: {repr(ex)}"
            module_logger.error(message)
            raise exceptions.MySQLError(message)

    def send_to_db(self, sql_query: str, sql_values: Union[tuple[str, ...], str]) -> None:
        """
        Send data to MySQL database.

        :param sql_query: SQL query to be executed.
        :param sql_values: Values to be substituted in the SQL query.
        :raise MySQLError: If the operation fails.
        """

        db_cursor = self._db_active_connection.cursor(prepared=True, dictionary=True)

        try:
            db_cursor.execute(sql_query, sql_values)

            self._db_active_connection.commit()

            module_logger.info(f"Database SQL query {sql_query=} executed successfully")

        except mysql.connector.OperationalError as ex:
            message = (
                f"While executing SQL query {sql_query=} to [{self._host}] operation failed!"
                f" traceback: {repr(ex)}"
            )
            module_logger.error(message)
            raise exceptions.MySQLError(message)

        finally:
            db_cursor.close()
            self.close_db_connection()

    def fetch_from_db(
        self, sql_query: str, sql_values: Union[tuple[str, ...], str], *, fetch_one: bool = False
    ) -> Generator[dict[str, str], None, None]:
        """
        Fetch data from MySQL database.

        :param sql_query: SQL query to be executed.
        :param sql_values: Values to be substituted in the SQL query.
        :param fetch_one: If True, only fetch the first row.
        :return: Generator of dictionaries containing the fetched rows.
        :raise MySQLError: If the operation fails.
        """

        db_cursor = self._db_active_connection.cursor(prepared=True, dictionary=True)

        try:
            db_cursor.execute(sql_query, sql_values)

            module_logger.info(f"Database SQL query {sql_query=} executed successfully")

            if fetch_one:
                yield db_cursor.fetchone()

            else:
                for row in db_cursor:
                    yield row

        except (mysql.connector.OperationalError, mysql.connector.errors.ProgrammingError) as ex:
            message = (
                f"While executing SQL query {sql_query=} to [{self._host}] operation failed!"
                f" traceback: {repr(ex)}"
            )
            module_logger.error(message)
            raise exceptions.MySQLError(message)

        finally:
            # cursor.reset typically discards the results of the last
            # query and resets the cursor to its initial state, without
            # affecting the underlying database connection. This is
            # useful if you've fetched some rows from a result but want
            # to discard the remaining unfetched rows and reuse the
            # cursor for another query.
            db_cursor.reset()
            self.close_db_connection()


class SQLite(Database):
    """
    Handles SQLite database connections.

    :param sqlite_db_path: Fullpath to the SQLite database file.
    :param filename: Name of the SQLite database file.
    """

    def __init__(self, sqlite_db_path: Union[str, pathlib.Path], filename: str):
        self._sqlite_db_path = sqlite_db_path
        self._filename = filename
        self._db_connection: Optional[sqlite3.Connection] = None

    def open_db_connection(self) -> None:
        """
        Open a SQLite db connection and cache it for quick access.
        To equal the style of MySQL it enables some features by default:
        - Set the cursor to return dictionary instead of tuples.
        - Enable foreign key constraint.

        :raise SQLiteError: If the operation fails.
        """

        try:
            self._db_connection = sqlite3.connect(self._sqlite_db_path)

            # Row to the row_factory of connection creates what some
            # people call a 'dictionary cursor'. Instead of tuples,
            # it starts returning 'dictionary'
            self._db_connection.row_factory = sqlite3.Row

            # Foreign key constraint must be enabled by the application
            # at runtime using the PRAGMA command
            self._db_connection.execute("PRAGMA foreign_keys = ON;")

        except sqlite3.OperationalError as ex:
            message = (
                f"While connecting to [{self._filename}] operation failed! traceback: {repr(ex)}"
            )
            module_logger.error(message)
            raise exceptions.SQLiteError(message)

    def close_db_connection(self) -> None:
        """
        Close the SQLite db connection.

        :raise SQLiteError: If the operation fails.
        """

        try:
            assert self._db_connection is not None, "Database connection is not open!"

            self._db_connection.close()

        except sqlite3.OperationalError as ex:
            message = f"While closing [{self._filename}] operation failed! traceback: {repr(ex)}"
            module_logger.error(message)
            raise exceptions.SQLiteError(message)

    def send_to_db(
        self, sql_query: str, sql_values: Union[tuple[str, ...], str], db_is_open: bool = False
    ) -> None:
        """
        Send data to SQLite database.

        :param sql_query: SQL query to be executed.
        :param sql_values: Values to be substituted in the SQL query.
        :param db_is_open: If True, the database connection is already
               open.
        :raise SQLiteError: If the operation fails.
        """

        if not db_is_open:
            self.open_db_connection()

        assert self._db_connection is not None, "Database connection is not open!"

        db_cursor = self._db_connection.cursor()

        try:
            db_cursor.execute(sql_query, sql_values)

            db_cursor.connection.commit()

            module_logger.info(f"Database SQL query {sql_query=} executed successfully")

        except (sqlite3.OperationalError, sqlite3.IntegrityError) as ex:
            message = (
                f"While executing SQL query {sql_query=} to [{self._filename}] operation failed!"
                f" traceback: {repr(ex)}"
            )
            module_logger.error(message)
            raise exceptions.SQLiteError(message)

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()

    def fetch_from_db(
        self,
        sql_query: str,
        sql_values: Union[tuple[str, ...], str],
        *,
        fetch_one: bool = False,
        db_is_open: bool = False,
    ) -> Generator[dict[str, str], None, None]:
        """
        Fetch data from SQLite database.

        :param sql_query: SQL query to be executed.
        :param sql_values: Values to be substituted in the SQL query.
        :param fetch_one: If True, only fetch the first row.
        :param db_is_open: If True, the database connection is already
               open.
        :return: Generator of dictionaries containing the fetched rows.
        :raise SQLiteError: If the operation fails.
        """

        if not db_is_open:
            self.open_db_connection()

        assert self._db_connection is not None, "Database connection is not open!"

        db_cursor = self._db_connection.cursor()

        try:
            db_cursor.execute(sql_query, sql_values)

            module_logger.info(f"Database SQL query {sql_query=} executed successfully")

            if fetch_one:
                try:
                    # The dict() converts the sqlite3.Row object,
                    # created by row_factory, into a dictionary
                    yield dict(db_cursor.fetchone())

                except TypeError:
                    # if the fetch is not found and returns None,
                    # the dict(None) would raise TypeError
                    yield {}

            else:
                for row in db_cursor:
                    yield dict(row)

        except sqlite3.OperationalError as ex:
            message = (
                f"While executing SQL query {sql_query=} to [{self._filename}] operation failed!"
                f" traceback: {repr(ex)}"
            )
            module_logger.error(message)
            raise exceptions.SQLiteError(message)

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()
