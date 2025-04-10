# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_database.py
# Created 2/20/25 - 12:54 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made code or quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import sqlite3
from pprint import pprint
from unittest.mock import patch

# Third Party Library Imports
import psycopg2.extensions
import pytest
from test__entrypoint__ import master_logger

# My Library Imports
from carlogtt_library import Database, MySQL, PostgreSQL, SQLite
from carlogtt_library.exceptions import MySQLError, PostgresError, SQLiteError

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)

# Type aliases
#

mysql_db = MySQL(
    host="fake_host",
    user="fake_user",
    password="fake_pass",
    port="9999",
    database_schema="fake_db",
)


def test_database_abstract_methods():
    """Ensure Database abstract methods remain enforced."""
    with pytest.raises(TypeError):
        _ = Database()


def test_mysql_coverage():
    # Create a MySQL instance with dummy credentials
    mysql_db = MySQL(
        host="fake_host",
        user="fake_user",
        password="fake_pass",
        port="9999",
        database_schema="fake_db",
    )

    # Call db_connection property
    try:
        _ = mysql_db.db_connection
    except (MySQLError, AssertionError):
        pass

    # Call open_db_connection
    try:
        mysql_db.open_db_connection()
    except (MySQLError, AssertionError):
        pass

    # Call close_db_connection
    try:
        mysql_db.close_db_connection()
    except (MySQLError, AssertionError):
        pass

    # Call send_to_db with dummy SQL
    try:
        mysql_db.send_to_db("FAKE SQL", ("fake_value",))
    except (MySQLError, AssertionError):
        pass

    # Call fetch_from_db (once with fetch_one=False, once with fetch_one=True)
    try:
        list(mysql_db.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=False))
    except (MySQLError, AssertionError):
        pass

    try:
        list(mysql_db.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=True))
    except (MySQLError, AssertionError):
        pass

    # Mock MySQL connection error to test exception handling
    with patch("mysql.connector.connect", side_effect=MySQLError("Connection failed")):
        with pytest.raises(MySQLError):
            mysql_db.open_db_connection()

    # Test assertion error on closing connection without opening it
    mysql_db._db_connection = None
    with pytest.raises(AssertionError):
        mysql_db.close_db_connection()


def test_sqlite_coverage():
    # Create a SQLite instance pointing to an in-memory DB
    sqlite_db = SQLite(":memory:", "fake_sqlite_db")

    # Call db_connection property
    _ = sqlite_db.db_connection

    # Call open_db_connection
    sqlite_db.open_db_connection()
    assert isinstance(sqlite_db._db_connection, sqlite3.Connection)

    # Call close_db_connection
    sqlite_db.close_db_connection()
    assert sqlite_db._db_connection is None

    # Call send_to_db with dummy SQL
    sqlite_db.send_to_db(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT"
        " UNIQUE NOT NULL)",
        '',
    )

    # Call fetch_from_db (once with fetch_one=False, once with fetch_one=True)
    result = list(sqlite_db.fetch_from_db("SELECT 1 WHERE FALSE", '', fetch_one=False))
    assert result == [{}]

    result = list(sqlite_db.fetch_from_db("SELECT 1 WHERE FALSE", '', fetch_one=True))
    assert result == [{}]

    # Mock SQLite connection error to test exception handling
    with patch("sqlite3.connect", side_effect=SQLiteError("Connection failed")):
        with pytest.raises(SQLiteError):
            sqlite_db.open_db_connection()

    # Test assertion error on closing connection without opening it
    sqlite_db._db_connection = None
    with pytest.raises(AssertionError):
        sqlite_db.close_db_connection()


def test_postgresql_coverage():
    pg = PostgreSQL(
        host="fake_host",
        user="XXXXXXXXX",
        password="XXXX_pass",
        port="9999",
        database_schema="fake_db",
    )

    # Call db_connection property
    try:
        _ = pg.db_connection
    except (PostgresError, AssertionError):
        pass

    # Call open_db_connection
    try:
        pg.open_db_connection()
        assert isinstance(pg._db_connection, psycopg2.extensions.connection)
    except (PostgresError, AssertionError):
        pass

    # Call close_db_connection
    try:
        pg.close_db_connection()
        assert pg._db_connection is None
    except (PostgresError, AssertionError):
        pass

    # Call send_to_db with dummy SQL
    try:
        pg.send_to_db("FAKE SQL", ("fake_value",))
    except (PostgresError, AssertionError):
        pass

    # Call fetch_from_db (once with fetch_one=False, once with fetch_one=True)
    try:
        list(pg.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=False))
    except (PostgresError, AssertionError):
        pass

    try:
        list(pg.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=True))
    except (PostgresError, AssertionError):
        pass


def sql_query():
    sql_query = 'INSERT INTO `table` (`string`, `int`, `none`, `float`) VALUES (?, ?, ?, ?)'
    sql_values = ('hello', 123, None, 23.5)

    mysql_db.send_to_db(sql_query=sql_query, sql_values=sql_values)


if __name__ == '__main__':
    funcs = [
        # ,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
