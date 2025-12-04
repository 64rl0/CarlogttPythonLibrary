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
import botocore.exceptions
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


@pytest.fixture
def dynamodb_instance():
    from carlogtt_python_library.database.database_dynamo import DynamoDB

    return DynamoDB(aws_region_name="us-east-1", caching=True)


@pytest.fixture
def mock_boto3():
    with mock.patch("carlogtt_python_library.aws_boto3.aws_service_base.boto3") as mock_boto3:
        yield mock_boto3


@pytest.fixture
def mock_client():
    with mock.patch(
        "carlogtt_python_library.database.database_dynamo.DynamoDB._client"
    ) as mock_client:
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
    from carlogtt_python_library.database.database_dynamo import DynamoDB

    instance = DynamoDB(aws_region_name="us-east-1", caching=False)
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


def test_delete_item_with_sort_key(mock_client, dynamodb_instance):
    mock_client.delete_item.return_value = {"Attributes": {"id": {"S": "1"}}}
    result = dynamodb_instance.delete_item(
        "table", "pk", "1", sort_key_key="sk", sort_key_value="sort-1"
    )
    assert result == [{"id": "1", "pk": "1", "sk": "sort-1"}]


def test_delete_item_multiple_with_sort_keys(mock_client, dynamodb_instance):
    mock_client.delete_item.side_effect = [
        {"Attributes": {"id": {"S": "1"}}},
        {"Attributes": {"id": {"S": "2"}}},
    ]
    result = dynamodb_instance.delete_item(
        "table", "pk", ["1", "2"], sort_key_key="sk", sort_key_value=["sort-1", "sort-2"]
    )
    assert [item["pk"] for item in result] == ["1", "2"]
    assert [item["sk"] for item in result] == ["sort-1", "sort-2"]


def test_delete_item_mismatched_pk_sk_lengths(dynamodb_instance):
    from carlogtt_python_library import exceptions

    with pytest.raises(exceptions.DynamoDBError):
        dynamodb_instance.delete_item(
            "table", "pk", ["1", "2"], sort_key_key="sk", sort_key_value=["only-one"]
        )


def test_delete_item_missing_sort_key_params(dynamodb_instance):
    from carlogtt_python_library import exceptions

    with pytest.raises(exceptions.DynamoDBError):
        dynamodb_instance.delete_item("table", "pk", "1", sort_key_key="sk")


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


def test_get_items_pagination(mock_client, dynamodb_instance):
    mock_client.scan.side_effect = [
        {
            "Items": [{"id": {"S": "1"}}],
            "LastEvaluatedKey": {"id": {"S": "1"}},
        },
        {
            "Items": [{"id": {"S": "2"}}],
        },
    ]

    items = list(dynamodb_instance.get_items("table"))
    assert items == [{"id": "1"}, {"id": "2"}]
    assert mock_client.scan.call_count == 2


def test_get_items_client_error(mock_client, dynamodb_instance):
    from carlogtt_python_library import exceptions

    mock_client.scan.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "Validation", "Message": "bad"}}, "Scan"
    )
    with pytest.raises(exceptions.DynamoDBError):
        list(dynamodb_instance.get_items("table"))


def test_put_item_success_path(mock_client, dynamodb_instance):
    with mock.patch.object(dynamodb_instance, "_put_single_item") as mock_put_single_item:
        mock_put_single_item.return_value = {"pk": "123", "name": "test"}
        item = dynamodb_instance.put_item(
            "table",
            "pk",
            partition_key_value="123",
            sort_key_key="sk",
            sort_key_value="1",
            name="test",
        )

    mock_put_single_item.assert_called_once()
    assert item["pk"] == "123"
    assert item["name"] == "test"


def test_put_item_autogenerated_pk(mock_client, dynamodb_instance):
    with mock.patch.object(dynamodb_instance, "atomic_writes") as mock_atomic_writes:
        mock_atomic_writes.return_value = {"Put": [{"pk": "auto", "name": "test"}]}
        item = dynamodb_instance.put_item(
            "table",
            "pk",
            partition_key_value=None,
            auto_generate_partition_key_value=True,
            name="test",
        )

    mock_atomic_writes.assert_called_once()
    assert item == {"pk": "auto", "name": "test"}


def test_update_item_success_with_condition(mock_client, dynamodb_instance):
    serializer = mock.Mock()
    serializer.serialize_p_key.return_value = {"pk": {"S": "1"}}
    serializer.serialize_update_items.return_value = (
        "SET #name = :name",
        {"#name": "name"},
        {":name": {"S": "new"}},
    )
    serializer.deserialize_p_key.return_value = ("pk", "1", None, None)
    serializer.deserialize_att.side_effect = lambda v: v
    serializer.normalize_item.side_effect = lambda item: item
    serializer.serialize_att.side_effect = lambda v: {"S": v}
    dynamodb_instance._serializer = serializer

    mock_client.update_item.return_value = {"Attributes": {"old": {"S": "old"}}}

    result = dynamodb_instance.update_item(
        "table", {"pk": "1"}, condition_attribute={"cond": "match"}, name="new"
    )

    assert result["pk"] == "1"
    assert result["name"] == "new"
    kwargs = mock_client.update_item.call_args.kwargs
    assert "ConditionExpression" in kwargs
    assert "#cond" in kwargs["ExpressionAttributeNames"]


def test_update_item_conflict(mock_client, dynamodb_instance):
    from carlogtt_python_library import exceptions

    serializer = mock.Mock()
    serializer.serialize_p_key.return_value = {"pk": {"S": "1"}}
    serializer.serialize_update_items.return_value = (
        "SET #a = :a",
        {"#a": "a"},
        {":a": {"S": "v"}},
    )
    serializer.deserialize_p_key.return_value = ("pk", "1", None, None)
    serializer.deserialize_att.side_effect = lambda v: v
    serializer.normalize_item.side_effect = lambda item: item
    serializer.serialize_att.side_effect = lambda v: {"S": v}
    dynamodb_instance._serializer = serializer

    mock_client.update_item.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "ConditionalCheckFailed", "Message": "fail"}}, "UpdateItem"
    )

    with pytest.raises(exceptions.DynamoDBConflictError):
        dynamodb_instance.update_item("table", {"pk": "1"}, name="v")


def test_upsert_item_success(mock_client, dynamodb_instance):
    serializer = mock.Mock()
    serializer.serialize_p_key.return_value = {"pk": {"S": "1"}}
    serializer.serialize_update_items.return_value = (
        "SET #a = :a",
        {"#a": "a"},
        {":a": {"S": "v"}},
    )
    serializer.deserialize_p_key.return_value = ("pk", "1", None, None)
    serializer.deserialize_att.side_effect = lambda v: v
    serializer.normalize_item.side_effect = lambda item: item
    serializer.serialize_att.side_effect = lambda v: {"S": v}
    dynamodb_instance._serializer = serializer

    mock_client.update_item.return_value = {"Attributes": {"old": {"S": "old"}}}

    result = dynamodb_instance.upsert_item("table", {"pk": "1"}, name="v")
    assert result["pk"] == "1"
    assert result["name"] == "v"


def test_upsert_item_conflict(mock_client, dynamodb_instance):
    from carlogtt_python_library import exceptions

    serializer = mock.Mock()
    serializer.serialize_p_key.return_value = {"pk": {"S": "1"}}
    serializer.serialize_update_items.return_value = (
        "SET #a = :a",
        {"#a": "a"},
        {":a": {"S": "v"}},
    )
    serializer.deserialize_p_key.return_value = ("pk", "1", None, None)
    serializer.deserialize_att.side_effect = lambda v: v
    serializer.normalize_item.side_effect = lambda item: item
    serializer.serialize_att.side_effect = lambda v: {"S": v}
    dynamodb_instance._serializer = serializer

    mock_client.update_item.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "ConditionalCheckFailed", "Message": "fail"}}, "UpdateItem"
    )

    with pytest.raises(exceptions.DynamoDBConflictError):
        dynamodb_instance.upsert_item("table", {"pk": "1"}, name="v")


def test_delete_item_att_success(mock_client, dynamodb_instance):
    serializer = mock.Mock()
    serializer.serialize_p_key.return_value = {"pk": {"S": "1"}}
    serializer.deserialize_att.side_effect = lambda v: v
    dynamodb_instance._serializer = serializer

    mock_client.update_item.return_value = {
        "Attributes": {
            "pk": {"S": "1"},
            "field": {"S": "value"},
        }
    }

    result = dynamodb_instance.delete_item_att("table", "pk", "1", attributes_to_delete=["field"])

    mock_client.update_item.assert_called_once()
    assert result["pk"] == {"S": "1"}
    assert "field" in result
