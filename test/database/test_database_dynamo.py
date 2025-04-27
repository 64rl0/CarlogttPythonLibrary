# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_database_dynamo.py
# Created 4/13/25 - 3:02 PM UK Time (London) by carlogtt
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
from unittest import mock

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
# Monkey-patches applied automatically to every test
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_decorators_retry(monkeypatch):
    """
    Replace decorators.retry with a do-nothing decorator/context-manager.
    """

    class _NoopRetry:
        def __call__(self, fn):  # decorator form
            return fn

        def __enter__(self):  # context-manager form
            return lambda fn, *a, **kw: fn(*a, **kw)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "carlogtt_library.retry",
        lambda *a, **kw: _NoopRetry(),
        raising=True,
    )


@pytest.fixture
def dynamodb_instance():
    import carlogtt_library as mylib

    return mylib.DynamoDB(aws_region_name="us-east-1", caching=True)


@pytest.fixture
def mock_boto3():
    with mock.patch("carlogtt_library.database.database_dynamo.boto3") as mock_boto3:
        yield mock_boto3


@pytest.fixture
def mock_client():
    with mock.patch("carlogtt_library.database.database_dynamo.DynamoDB._client") as mock_client:
        yield mock_client


def test_client_caching(mock_boto3, dynamodb_instance):
    mock_session = mock.Mock()
    mock_client = mock.Mock()
    mock_session.client.return_value = mock_client
    mock_boto3.session.Session.return_value = mock_session

    client1 = dynamodb_instance._client
    client2 = dynamodb_instance._client

    assert client1 is client2  # Cached client


def test_invalidate_client_cache(dynamodb_instance):
    dynamodb_instance._cache['client'] = "fake_client"
    dynamodb_instance.invalidate_client_cache()
    assert dynamodb_instance._cache['client'] is None


def test_invalidate_client_cache_without_caching():
    import carlogtt_library as mylib

    instance = mylib.DynamoDB(aws_region_name="us-east-1", caching=False)
    with pytest.raises(Exception) as excinfo:
        instance.invalidate_client_cache()
    assert "Session caching is not enabled" in str(excinfo.value)


def test_get_tables_success(mock_client, dynamodb_instance):
    mock_client.list_tables.return_value = {"TableNames": ["table1", "table2"]}
    tables = dynamodb_instance.get_tables()
    assert tables == ["table1", "table2"]


def test_get_tables_keyerror(mock_client, dynamodb_instance):
    mock_client.list_tables.return_value = {}
    tables = dynamodb_instance.get_tables()
    assert tables == []


def test_get_item_none(mock_client, dynamodb_instance):
    mock_client.get_item.return_value = {}
    result = dynamodb_instance.get_item("table", "pk", "value")
    assert result is None


def test_get_item_found(mock_client, dynamodb_instance):
    mock_client.get_item.return_value = {"Item": {"name": {"S": "test"}}}
    item = dynamodb_instance.get_item("table", "pk", "value")
    assert item == {"name": "test"}


def test_delete_item_single(mock_client, dynamodb_instance):
    mock_client.delete_item.return_value = {"Attributes": {"id": {"S": "1"}}}
    result = dynamodb_instance.delete_item("table", "pk", "1")
    assert result == [{"pk": "1", "id": "1"}]


def test_delete_item_multiple(mock_client, dynamodb_instance):
    mock_client.delete_item.return_value = {"Attributes": {"id": {"S": "1"}}}
    result = dynamodb_instance.delete_item("table", "pk", ["1", "2"])
    assert isinstance(result, list)
    assert len(result) == 2


def test_put_item_with_value(mock_client, dynamodb_instance):
    mock_client.put_item.return_value = {}
    item = dynamodb_instance.put_item("table", "pk", partition_key_value="123", name="test")
    assert "name" in item


def test_put_item_error_conflicting_options(dynamodb_instance):
    with pytest.raises(Exception):
        dynamodb_instance.put_item(
            "table", "pk", partition_key_value="id", auto_generate_partition_key_value=True
        )


def test_update_item_validation(mock_client, dynamodb_instance):
    with pytest.raises(Exception):
        dynamodb_instance.update_item("table", {"pk": "1"})


def test_upsert_item_no_items(mock_client, dynamodb_instance):
    with pytest.raises(Exception):
        dynamodb_instance.upsert_item("table", {"pk": "1"})


def test_get_items_count(mock_client, dynamodb_instance):
    mock_scan = mock.Mock()
    mock_scan.side_effect = [
        {"Items": [{"id": {"S": "1"}}], "LastEvaluatedKey": None},
        {},
    ]
    mock_client.scan = mock_scan
    count = dynamodb_instance.get_items_count("table")
    assert isinstance(count, int)
