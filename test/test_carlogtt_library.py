# flake8: noqa
# mypy: ignore-errors

# Standard Library Imports
import sqlite3
from unittest.mock import patch

# Third Party Library Imports
import pytest

# My Library Imports
from carlogtt_library import Database, MySQL, SQLite
from carlogtt_library.exceptions import MySQLError, SQLiteError


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
    except:
        pass

    # Call open_db_connection
    try:
        mysql_db.open_db_connection()
    except:
        pass

    # Call close_db_connection
    try:
        mysql_db.close_db_connection()
    except:
        pass

    # Call send_to_db with dummy SQL
    try:
        mysql_db.send_to_db("FAKE SQL", ("fake_value",))
    except:
        pass

    # Call fetch_from_db (once with fetch_one=False, once with fetch_one=True)
    try:
        list(mysql_db.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=False))
    except:
        pass

    try:
        list(mysql_db.fetch_from_db("FAKE SQL", ("fake_value",), fetch_one=True))
    except:
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
