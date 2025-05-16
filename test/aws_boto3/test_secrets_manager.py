# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_secrets_manager.py
# Created 4/26/25 - 8:20 AM UK Time (London) by carlogtt
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
import datetime
import json

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


# ----------------------------------------------------------------------
# Autouse fixture – patch boto3 before the SUT is imported -------------
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_boto3(monkeypatch):
    """Replace boto3.session.Session with an in-memory fake."""

    # Fake client implementing just what SecretsManager calls
    class _FakeSMClient:
        def __init__(self):
            self.list_calls = 0
            self.deleted_args = None

        # ---------- paginator simulation ----------
        def list_secrets(self, **kw):
            self.list_calls += 1
            if kw.get("NextToken") is None:
                # first page
                return {
                    "SecretList": [{"Name": "s1"}, {"Name": "s2"}],
                    "NextToken": "TOKEN",
                }
            # second / last page
            return {"SecretList": [{"Name": "s3"}]}

        # ---------- secret retrieval ----------
        def get_secret_value(self, **kw):
            secret_id = kw["SecretId"]
            if secret_id == "exists":
                return {"SecretString": json.dumps({"username": "u", "password": "p"})}
            if secret_id == "empty":
                return {}  # no SecretString key
            # simulate AWS ClientError
            import botocore.exceptions as bce

            raise bce.ClientError(
                {"Error": {"Code": "ResourceNotFoundException", "Message": "boom"}},
                "GetSecretValue",
            )

        # ---------- deletion ----------
        def delete_secret(self, **kw):
            self.deleted_args = kw
            return {"DeletionDate": datetime.datetime.now(tz=datetime.timezone.utc)}

    # Fake boto3 session that always returns the same fake client
    class _FakeBotoSession:
        def __init__(self, **_):
            self._client = _FakeSMClient()

        def client(self, **_):
            return self._client

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    yield


# ----------------------------------------------------------------------
# Fixtures --------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def cached_manager():
    import carlogtt_library as mylib

    return mylib.SecretsManager("eu-west-1", caching=True)


@pytest.fixture
def fresh_manager():
    import carlogtt_library as mylib

    return mylib.SecretsManager("eu-west-1", caching=False)


# ----------------------------------------------------------------------
# Client caching behaviour ---------------------------------------------
# ----------------------------------------------------------------------
def test_client_cached(cached_manager):
    first = cached_manager._client
    second = cached_manager._client
    assert first is second  # same instance cached

    cached_manager.invalidate_client_cache()
    # cache cleared → new instance
    assert cached_manager._client is not first


def test_invalidate_without_cache_raises(fresh_manager):
    import carlogtt_library as mylib

    with pytest.raises(mylib.SecretsManagerError):
        fresh_manager.invalidate_client_cache()


# ----------------------------------------------------------------------
# list_secrets pagination ----------------------------------------------
# ----------------------------------------------------------------------
def test_get_all_secrets_paginates(cached_manager):
    secrets = cached_manager.get_all_secrets()
    names = [s["Name"] for s in secrets]
    assert names == ["s1", "s2", "s3"]
    # underlying fake client was called twice (page1 + page2)
    assert cached_manager._client.list_calls == 2


# ----------------------------------------------------------------------
# get_secret & get_secret_password -------------------------------------
# ----------------------------------------------------------------------
def test_get_secret_success(cached_manager):
    sec = cached_manager.get_secret("exists")
    assert sec == {"username": "u", "password": "p"}


def test_get_secret_missing_returns_none(cached_manager):
    assert cached_manager.get_secret("empty") is None


def test_get_secret_password_field(cached_manager):
    pwd = cached_manager.get_secret_password("exists")
    assert pwd == "p"

    # when secret missing → empty string
    assert cached_manager.get_secret_password("empty") == ""


def test_get_secret_error_raises(cached_manager):
    import carlogtt_library as mylib

    with pytest.raises(mylib.SecretsManagerError):
        cached_manager.get_secret("not-there")


# ----------------------------------------------------------------------
# delete_secret --------------------------------------------------------
# ----------------------------------------------------------------------
def test_delete_secret_recovery_window(cached_manager):
    resp = cached_manager.delete_secret("mysecret", recovery_days=7)
    assert "DeletionDate" in resp
    # verify args passed to underlying client
    assert cached_manager._client.deleted_args == {
        "SecretId": "mysecret",
        "RecoveryWindowInDays": 7,
    }


def test_delete_secret_force(cached_manager):
    cached_manager.delete_secret("force", force_delete=True)
    assert cached_manager._client.deleted_args == {
        "SecretId": "force",
        "ForceDeleteWithoutRecovery": True,
    }
