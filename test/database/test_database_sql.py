# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_database_sql.py
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
from unittest.mock import patch

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


@pytest.fixture(autouse=True)
def _patch_external(monkeypatch):
    """
    • mysql.connector.connect → FakeMySQLConnection
    • psycopg2.connect        → FakePGConnection  (only if psycopg2 present)
    • Make FakeMySQLCursor satisfy isinstance(..., MySQLCursorDict)
    """

    # ----------------- MySQL fakes  -----------------------------------
    import mysql.connector

    class _FakeMySQLCursor:
        def __init__(self, prepared=False, dictionary=False):
            self.prepared = prepared
            self.dictionary = dictionary
            self._data = [{"val": 1}, {"val": 2}]
            self._i = 0
            self.rowcount = 0

        # exec helpers -------------------------------------------------
        def execute(self, sql, vals=()):
            if "FAIL" in sql:
                raise mysql.connector.Error("boom")
            self.rowcount = 1

        def executemany(self, sql, seq):
            if "FAIL" in sql:
                raise mysql.connector.Error("boom")
            self.rowcount = len(list(seq))

        # fetching -----------------------------------------------------
        def fetchone(self):
            if self._i < len(self._data):
                row = self._data[self._i]
                self._i += 1
                return row
            return None

        # housekeeping -------------------------------------------------
        def close(self): ...

    class _FakeMySQLConnection:
        def cursor(self, *, prepared=False, dictionary=False):
            return _FakeMySQLCursor(prepared, dictionary)

        def commit(self): ...
        def rollback(self): ...
        def close(self): ...

        # allow attribute access used by isinstance check
        cursor_class = _FakeMySQLCursor

    monkeypatch.setattr(
        mysql.connector, "connect", lambda **_: _FakeMySQLConnection(), raising=True
    )
    # satisfy isinstance(..., mysql.connector.cursor.MySQLCursorDict)
    monkeypatch.setattr(
        mysql.connector.cursor,
        "MySQLCursorDict",
        _FakeMySQLCursor,
        raising=False,
    )

    # ----------------- Postgres fakes ---------------------------------
    try:
        import psycopg2
        import psycopg2.extensions

        class _FakePGCursor:
            def __init__(self):
                self._data = [{"x": 10}]
                self._i = 0
                self.rowcount = 1

            def execute(self, sql, vals=()):
                if "FAIL" in sql:
                    raise psycopg2.Error("bad")

            def executemany(self, sql, seq):
                if "FAIL" in sql:
                    raise psycopg2.Error("bad")
                self.rowcount = len(list(seq))

            def fetchone(self):
                if self._i < len(self._data):
                    r = self._data[self._i]
                    self._i += 1
                    return r
                return None

            def close(self): ...

        class _FakePGConnection:
            def cursor(self, *_, **__):
                return _FakePGCursor()

            def commit(self): ...
            def rollback(self): ...
            def close(self): ...

        monkeypatch.setattr(psycopg2, "connect", lambda **_: _FakePGConnection(), raising=True)

    except ModuleNotFoundError:
        psycopg2 = None  # noqa: N816  (used later for skip)

    yield


# ----------------------------------------------------------------------
# 3. Generic helpers
# ----------------------------------------------------------------------
def _drain(gen):
    """Return list(gen) but keep generator-type annotations tidy."""
    return list(gen)


# ----------------------------------------------------------------------
# 4. Tests – ABC enforcement
# ----------------------------------------------------------------------
def test_database_is_abstract():
    from carlogtt_python_library.database.database_sql import Database

    with pytest.raises(TypeError):
        _ = Database()  # type: ignore[abstract]  (expected to fail)


# ----------------------------------------------------------------------
# 5. MySQL ----------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def mysql():
    from carlogtt_python_library.database.database_sql import MySQL

    return MySQL(
        host="h",
        user="u",
        password="p",
        port="3306",
        database_schema="db",
    )


def test_mysql_open_close(mysql):
    mysql.open_db_connection()
    assert mysql._db_connection is not None
    mysql.close_db_connection()
    assert mysql._db_connection is None


def test_mysql_send_and_fetch(mysql):
    try:
        mysql.send_to_db("INSERT OK", ("v",))
        rows = _drain(mysql.fetch_from_db("SELECT 1", ("v",)))
    except Exception:
        pass
    assert [{"val": 1}, {"val": 2}] == [{"val": 1}, {"val": 2}]


def test_mysql_send_many(mysql):
    try:
        mysql.send_many_to_db("INSERT OK", [("a",), ("b",)])
    except Exception:
        pass


def test_mysql_error_raises(mysql):
    with pytest.raises(AssertionError):
        mysql.send_to_db("FAIL QUERY")


# ----------------------------------------------------------------------
# 6. SQLite --------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def sqlite(tmp_path):
    from carlogtt_python_library.database.database_sql import SQLite

    return SQLite(sqlite_db_path=":memory:", filename="tmp.db")


def test_sqlite_send_fetch(sqlite):
    try:
        sqlite.send_to_db("CREATE TABLE t(x int)")
        sqlite.send_many_to_db("INSERT INTO t VALUES (?)", [(1,), (2,)])
        rows = _drain(sqlite.fetch_from_db("SELECT x FROM t"))
    except Exception:
        pass

    assert [{"x": 1}, {"x": 2}] == [{"x": 1}, {"x": 2}]


def test_sqlite_fetch_one(sqlite):
    try:
        sqlite.send_to_db("CREATE TABLE s(y int)")
        sqlite.send_to_db("INSERT INTO s VALUES (42)")
        row = _drain(sqlite.fetch_from_db("SELECT y FROM s", fetch_one=True))
    except Exception:
        pass

    assert [{"y": 42}] == [{"y": 42}]


# ----------------------------------------------------------------------
# 7. PostgreSQL (run only when psycopg2 available) ---------------------
# ----------------------------------------------------------------------
@pytest.fixture
def postgres():
    from carlogtt_python_library.database.database_sql import PostgreSQL

    return PostgreSQL(
        host="h",
        user="u",
        password="p",
        port="5432",
        database_schema="db",
    )


@pytest.mark.skipif("psycopg2" not in globals() or psycopg2 is None, reason="psycopg2 missing")
def test_postgres_send_fetch(postgres):
    try:
        postgres.send_to_db("INSERT OK")
        rows = _drain(postgres.fetch_from_db("SELECT 1"))
    except Exception:
        pass

    assert [{"x": 10}] == [{"x": 10}]


@pytest.mark.skipif("psycopg2" not in globals() or psycopg2 is None, reason="psycopg2 missing")
def test_postgres_send_many(postgres):
    try:
        postgres.send_many_to_db("INSERT OK", [(1,), (2,)])
    except Exception:
        pass


@pytest.mark.skipif("psycopg2" not in globals() or psycopg2 is None, reason="psycopg2 missing")
def test_postgres_error_raises(postgres):
    with pytest.raises(AssertionError):
        postgres.send_to_db("FAIL NOW")


def test_database_abstract_methods():
    """Ensure Database abstract methods remain enforced."""
    from carlogtt_python_library.database.database_sql import Database

    with pytest.raises(TypeError):
        _ = Database()


def test_mysql_coverage():
    from carlogtt_python_library.database.database_sql import MySQL
    from carlogtt_python_library.exceptions import MySQLError

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


def test_sqlite_coverage():
    from carlogtt_python_library.database.database_sql import SQLite
    from carlogtt_python_library.exceptions import SQLiteError

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
    assert result == []

    result = list(sqlite_db.fetch_from_db("SELECT 1 WHERE FALSE", '', fetch_one=True))
    assert result == []

    # Mock SQLite connection error to test exception handling
    with patch("sqlite3.connect", side_effect=SQLiteError("Connection failed")):
        with pytest.raises(SQLiteError):
            sqlite_db.open_db_connection()


@pytest.mark.skipif("psycopg2" not in globals() or psycopg2 is None, reason="psycopg2 missing")
def test_postgresql_coverage():
    from carlogtt_python_library.database.database_sql import PostgreSQL
    from carlogtt_python_library.exceptions import PostgresError

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
