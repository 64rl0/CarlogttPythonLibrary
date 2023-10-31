# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

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
# TODO: disabled as not supported by python 3.9. re-enable once VS can
#  be updated to 3.10 or above
# from mysql.connector.connection_cext import CMySQLConnection
import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.pooling import PooledMySQLConnection

# Local Folder (Relative) Imports
from .. import exceptions
from . import database_utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Database',
    'MySQL',
    'SQLite',
    'QueryHandler',
]

# Type aliases
# TODO: disabled as not supported by python 3.9. re-enable once VS can
#  be updated to 3.10 or above
# MySQLConn = Union[
#     MySQLConnection,
#     CMySQLConnection,
#     PooledMySQLConnection
# ]
MySQLConn = Union[MySQLConnection, PooledMySQLConnection]


class Database(abc.ABC):
    @abc.abstractmethod
    def open_db_connection(self) -> None:
        pass

    @abc.abstractmethod
    def close_db_connection(self) -> None:
        pass

    @abc.abstractmethod
    def send_to_db(self, sql_query: str, sql_values: Union[tuple[str], str]) -> None:
        pass

    @abc.abstractmethod
    def fetch_from_db(
        self, sql_query: str, sql_values: Union[tuple[str], str], *, fetch_one: bool = False
    ) -> Generator[dict[str, str], None, None]:
        pass


class MySQL(Database):
    def __init__(self, host: str, user: str, password: str, port: str, database_schema: str):
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self._database_schema = database_schema
        self._db_connection: Optional[MySQLConn] = None

    @property
    def _db_active_connection(self) -> MySQLConn:
        if not self._db_connection:
            self.open_db_connection()

        assert (
            isinstance(self._db_connection, MySQLConnection)
            # TODO: disabled as not supported by python 3.9. re-enable
            #  once VS can be updated to 3.10 or above
            # or isinstance(self._db_connection, CMySQLConnection)
            or isinstance(self._db_connection, PooledMySQLConnection)
        ), "Expected self._db_connection to be type MySQLConn"

        return self._db_connection

    @_db_active_connection.setter
    def _db_active_connection(self, value) -> None:
        self._db_connection = value

    @database_utils.retry_decorator(exception_to_check=exceptions.MySQLError)
    def open_db_connection(self) -> None:
        try:
            self._db_active_connection = mysql.connector.connect(
                host=self._host,
                user=self._user,
                password=self._password,
                port=self._port,
                database=self._database_schema,
            )

        except mysql.connector.Error as e:
            message = f"While connecting to {self._host!r} operation failed! error: {str(e)}"
            logging.log(logging.ERROR, message)
            raise exceptions.MySQLError(message)

    @database_utils.retry_decorator(exception_to_check=exceptions.MySQLError)
    def close_db_connection(self) -> None:
        try:
            self._db_active_connection.close()

        except mysql.connector.Error as e:
            message = f"While closing {self._host!r} operation failed! error: {str(e)}"
            logging.log(logging.ERROR, message)
            raise exceptions.MySQLError(message)

    def send_to_db(self, sql_query: str, sql_values: Union[tuple[str], str]) -> None:
        """
        Send data to MySQL database.
        """

        db_cursor = self._db_active_connection.cursor(prepared=True, dictionary=True)

        try:
            db_cursor.execute(sql_query, sql_values)

            self._db_active_connection.commit()
            logging.log(logging.INFO, "Database upload successful")

        except mysql.connector.OperationalError as e:
            message = f"While sending to {self._host!r} operation failed! error: {str(e)}"
            logging.log(logging.ERROR, message)
            raise exceptions.MySQLError(message)

        finally:
            db_cursor.close()
            self.close_db_connection()

    def fetch_from_db(
        self, sql_query: str, sql_values: Union[tuple[str], str], *, fetch_one: bool = False
    ) -> Generator[dict[str, str], None, None]:
        """
        Fetch data from MySQL database.
        """

        db_cursor = self._db_active_connection.cursor(prepared=True, dictionary=True)

        try:
            db_cursor.execute(sql_query, sql_values)

            if fetch_one:
                yield db_cursor.fetchone()

            else:
                for row in db_cursor:
                    yield row

        except mysql.connector.OperationalError as e:
            message = f"While fetching from {self._host!r} operation failed! error: {str(e)}"
            logging.log(logging.ERROR, message)
            raise exceptions.MySQLError(message)

        # This Exception handles the case where the table is not found.
        except mysql.connector.errors.ProgrammingError as e:
            message = f"While connecting to {self._host!r} operation failed! error: {str(e)}"
            logging.log(logging.ERROR, message)
            raise exceptions.MySQLError(message)

        finally:
            # It typically discards the results of the last query and
            # resets the cursor to its initial state, without affecting
            # the underlying database connection. This is useful if
            # you've fetched some rows from a result but want to discard
            # the remaining unfetched rows and reuse the cursor for
            # another query.
            db_cursor.reset()
            self.close_db_connection()


class SQLite(Database):
    def __init__(self, sqlite_db_path: Union[str, pathlib.Path], filename: str):
        self._sqlite_db_path = sqlite_db_path
        self._filename = filename
        self._db_connection: Optional[sqlite3.Connection] = None

    def open_db_connection(self) -> None:
        try:
            self._db_connection = sqlite3.connect(self._sqlite_db_path)

            # Row to the row_factory of connection creates what some
            # people call a 'dictionary cursor'
            # Instead of tuples it starts returning 'dictionary'
            self._db_connection.row_factory = sqlite3.Row

            # foreign key constraint must be enabled by the application
            # at runtime using the PRAGMA command
            self._db_connection.execute("PRAGMA foreign_keys = ON;")

        except sqlite3.OperationalError as e:
            message = f"While connecting to {self._filename} operation failed! error: {str(e)}"
            logging.error(message)
            raise exceptions.SQLiteError(message)

    def close_db_connection(self) -> None:
        try:
            assert self._db_connection is not None, "Database connection is not open!"
            self._db_connection.close()

        except sqlite3.OperationalError as e:
            message = f"While closing {self._filename} operation failed! error: {str(e)}"
            logging.error(message)
            raise exceptions.SQLiteError(message)

    def send_to_db(
        self, sql_query: str, sql_values: Union[tuple[str], str], db_is_open: bool = False
    ) -> None:
        """
        Send data to SQLite database.
        """

        if not db_is_open:
            self.open_db_connection()

        assert self._db_connection is not None, "Database connection is not open!"
        db_cursor = self._db_connection.cursor()

        try:
            db_cursor.execute(sql_query, sql_values)

            db_cursor.connection.commit()
            logging.info("Database upload successful!")

        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            message = f"While sending to {self._filename} operation failed! error: {str(e)}"
            logging.error(message)
            raise exceptions.SQLiteError(message)

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()

    def fetch_from_db(
        self,
        sql_query: str,
        sql_values: Union[tuple[str], str],
        *,
        fetch_one: bool = False,
        db_is_open: bool = False,
    ) -> Generator[dict[str, str], None, None]:
        """
        Fetch data from SQLite database.
        """

        if not db_is_open:
            self.open_db_connection()

        assert self._db_connection is not None, "Database connection is not open!"
        db_cursor = self._db_connection.cursor()

        try:
            db_cursor.execute(sql_query, sql_values)

            # The dict() converts the sqlite3.Row object, created by
            # row_factory, into a dictionary
            if fetch_one:
                try:
                    yield dict(db_cursor.fetchone())

                # if the fetch is not found and returns None, the
                # dict(None) would raise TypeError
                except TypeError:
                    yield {}

            else:
                for row in db_cursor:
                    yield dict(row)

        except sqlite3.OperationalError as e:
            message = f"While fetching from {self._filename} operation failed! error: {str(e)}"
            logging.error(message)
            raise exceptions.SQLiteError(message)

        finally:
            db_cursor.close()

            if not db_is_open:
                self.close_db_connection()


class QueryHandler:
    def __init__(self, database: Database, sql_queries_folder: pathlib.Path) -> None:
        self._database = database
        self._sql_queries_folder = sql_queries_folder

    def open_db_connection(self) -> None:
        self._database.open_db_connection()

    def close_db_connection(self) -> None:
        self._database.close_db_connection()

    def create_table_on_db(self) -> None:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'create_table_on_db.sql'
        )
        sql_values = ""

        self._database.send_to_db(sql_query, sql_values)

    def fetch_record_from_db(self) -> dict[str, str]:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'fetch_record_from_db.sql'
        )
        sql_values = ""

        record_gen = self._database.fetch_from_db(sql_query, sql_values, fetch_one=True)
        record = [*record_gen][0]

        return record

    def fetch_all_records_from_db_lazy_load(self) -> Generator[dict[str, str], None, None]:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'fetch_all_records_from_db.sql'
        )
        sql_values = ""

        record = self._database.fetch_from_db(sql_query, sql_values)

        return record

    def send_record_to_db(self) -> None:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'send_record_to_db.sql'
        )
        sql_values = ""

        self._database.send_to_db(sql_query, sql_values)

    def update_record_on_db(self) -> None:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'update_record_on_db.sql'
        )
        sql_values = ""

        self._database.send_to_db(sql_query, sql_values)

    def delete_record_from_db(self) -> None:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'delete_record_from_db.sql'
        )
        sql_values = ""

        self._database.send_to_db(sql_query, sql_values)

    def delete_all_records_from_db(self) -> None:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'delete_all_records_from_db.sql'
        )
        sql_values = ""

        self._database.send_to_db(sql_query, sql_values)

    def count_all_db_records(self) -> int:
        sql_query = database_utils.sql_query_reader(
            self._sql_queries_folder / 'count_all_db_records.sql'
        )
        sql_values = ""

        records = self._database.fetch_from_db(sql_query, sql_values, fetch_one=True)
        record = [*records][0]

        return int(record['COUNT(*)'])
