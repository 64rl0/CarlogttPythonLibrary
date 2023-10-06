# MODULE NAME ----------------------------------------------------------------------------------------------------------
# dynamodb.py
# ----------------------------------------------------------------------------------------------------------------------

"""
Module description
"""
# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging
import os
from collections.abc import Sequence
from enum import Enum, auto
from numbers import Number
from typing import Any

# Third Party Library Imports ------------------------------------------------------------------------------------------
import boto3
from botocore.client import BaseClient
from botocore.exceptions import EndpointConnectionError

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------
from .. import _config, utils
from ..exceptions import db_exceptions

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


class NormalizeMethod(Enum):
    Store = auto()
    Update = auto()


def _dev_only_create_table():
    client = _get_boto_dynamo_db_client()

    response = client.create_table(
        TableName='JWT_Revoked_Identity_Tokens',
        KeySchema=[{"AttributeName": "jti", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "jti", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 50, "WriteCapacityUnits": 50},
    )

    return response


def _get_dynamo_db_attribute_type(value: Any) -> str:
    dynamo_db_attribute_type = {
        bytes: "B",
        bool: "BOOL",
        str: "S",
        Number: "N",
        Sequence: "SS",
    }

    type_is_a_match = []

    for type_ in dynamo_db_attribute_type.keys():
        if isinstance(value, type_):
            type_is_a_match.append(dynamo_db_attribute_type[type_])

    if not type_is_a_match:
        raise TypeError(f"Type {type(value)!r} for value {value} not defined in get_dynamo_db_attribute_type")

    elif len(type_is_a_match) > 1:
        with utils.redirect_stdout_to_stderr():
            print(
                f"Type for value {value!r} has multiple matches {type_is_a_match} in get_dynamo_db_attribute_type. "
                f"Selected: {type_is_a_match[0]!r}"
            )

    return type_is_a_match[0]


def _normalize_value_for_dynamo_db(value: Any) -> Any:
    if isinstance(value, Number):
        value = str(value)

    elif isinstance(value, Sequence):
        value = list(value)

    return value


def _serialize_additional_items(method: NormalizeMethod, **items: Any) -> dict[str, dict[str, Any]]:
    additional_items = {}

    for key, value in items.items():
        normalized_key = utils.snake_case(key)
        type_identifier = _get_dynamo_db_attribute_type(value)
        normalized_value = _normalize_value_for_dynamo_db(value)

        # Now add it to the additional_items serialized dictionary
        if method is NormalizeMethod.Store:
            additional_items[normalized_key] = {type_identifier: normalized_value}

        elif method is NormalizeMethod.Update:
            additional_items[normalized_key] = {"Value": {type_identifier: normalized_value}}

    return additional_items


def _get_boto_dynamo_db_client() -> BaseClient:
    """Create a low-level dynamodb client"""

    try:
        boto_session: boto3.session.Session

        boto_session = boto3.session.Session(profile_name=_config.AWS_ENVIRONMENT)
        client = boto_session.client(service_name='dynamodb')

        # This will raise a EndpointConnectionError if there is a network error with the database
        client.describe_endpoints()

        return client

    except EndpointConnectionError as e:
        raise db_exceptions.DynamoDBConnectionError(str(e)) from e


def get_all_tables() -> list[str]:
    client = _get_boto_dynamo_db_client()

    response = client.list_tables()

    return response['TableNames']


def get_all_items_from_table(table: str) -> list[dict[str, dict[str, str]]]:
    client = _get_boto_dynamo_db_client()

    response = client.scan(TableName=table, Select='ALL_ATTRIBUTES')

    return response['Items']


def get_item_from_table(
    table: str, partition_key_key: str, partition_key_value: Any
) -> dict[str, dict[str, Any]] | None:
    client = _get_boto_dynamo_db_client()

    partition_key_value_type = _get_dynamo_db_attribute_type(partition_key_value)
    partition_key = {partition_key_key: {partition_key_value_type: partition_key_value}}

    response = client.get_item(TableName=table, Key=partition_key)

    return response.get('Item')


def store_item_in_table(table: str, partition_key_key: str, partition_key_value: Any, **items: Any):
    client = _get_boto_dynamo_db_client()

    partition_key_value_type = _get_dynamo_db_attribute_type(partition_key_value)
    additional_items = _serialize_additional_items(method=NormalizeMethod.Store, **items)
    all_items_normalized = {partition_key_key: {partition_key_value_type: partition_key_value}, **additional_items}

    response = client.put_item(
        TableName=table, Item=all_items_normalized, ConditionExpression=f"attribute_not_exists({partition_key_key})"
    )

    return response


def update_item_in_table(table: str, partition_key_key: str, partition_key_value: Any, **items: Any):
    client = _get_boto_dynamo_db_client()

    partition_key_value_type = _get_dynamo_db_attribute_type(partition_key_value)
    attribute_updates = _serialize_additional_items(method=NormalizeMethod.Update, **items)
    partition_key = {partition_key_key: {partition_key_value_type: partition_key_value}}

    response = client.update_item(TableName=table, Key=partition_key, AttributeUpdates=attribute_updates)

    return response


def delete_items_from_table(table: str, partition_key_key: str, *items: Any):
    response = []

    for item in items:
        client = _get_boto_dynamo_db_client()

        item_type = _get_dynamo_db_attribute_type(item)
        partition_key = {partition_key_key: {item_type: item}}
        deleted = client.delete_item(TableName=table, Key=partition_key)

        response.append(deleted)

    return response


def delete_item_values_from_table(table: str, partition_key_key: str, partition_key_value: Any, *item_values: str):
    client = _get_boto_dynamo_db_client()

    partition_key_value_type = _get_dynamo_db_attribute_type(partition_key_value)
    partition_key = {partition_key_key: {partition_key_value_type: partition_key_value}}
    attribute_updates = {item_value: {'Action': 'DELETE'} for item_value in item_values}

    response = client.update_item(TableName=table, Key=partition_key, AttributeUpdates=attribute_updates)

    return response
