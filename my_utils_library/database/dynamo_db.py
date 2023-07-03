# MODULE NAME ----------------------------------------------------------------------------------------------------------
# dynamodb.py
# ----------------------------------------------------------------------------------------------------------------------

"""
Module description
"""
# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import os
from enum import Enum, auto
from numbers import Number
from typing import Any

# Third Party Library Imports ------------------------------------------------------------------------------------------
import boto3
from botocore.client import BaseClient
from botocore.exceptions import EndpointConnectionError

# Local Folder (Relative) Imports --------------------------------------------------------------------------------------
from .. import config
from ..exceptions import db_exceptions
from ..logger import master_logger

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
my_app_logger = master_logger.get_child_logger(__name__)


class NormalizeMethod(Enum):
    Store = auto()
    Update = auto()


def _dev_only_create_table():
    client = _get_boto_dynamo_client()

    response = client.create_table(
        TableName='JWT_Revoked_Identity_Tokens',
        KeySchema=[{"AttributeName": "jti", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "jti", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 50, "WriteCapacityUnits": 50},
    )

    return response


def _normalize_additional_items(method: NormalizeMethod, **items: Any) -> dict[str, dict[str, Any]]:
    additional_items = {}

    for k, v in items.items():
        k = k.strip().replace(" ", "_").casefold()
        if isinstance(v, str):
            ty = "S"
        elif isinstance(v, bool):
            ty = "BOOL"
        elif isinstance(v, Number):
            ty = "N"
            v = str(v)
        elif isinstance(v, bytes):
            ty = "B"
        elif isinstance(v, list):
            ty = "SS"
        if method == NormalizeMethod.Store:
            additional_items.update({k: {ty: v}})
        elif method == NormalizeMethod.Update:
            additional_items.update({k: {"Value": {ty: v}}})

    return additional_items


def _get_ty(partition_key_value: str | int | float | bytes) -> str:
    if isinstance(partition_key_value, str):
        ty = "S"
    elif isinstance(partition_key_value, int | float):
        ty = "N"
    elif isinstance(partition_key_value, bytes):
        ty = "B"

    return ty


def _get_boto_dynamo_client() -> BaseClient:
    """Create a low-level dynamodb client"""

    try:
        boto_session: boto3.session.Session

        boto_session = boto3.session.Session(profile_name=config.AWS_ENVIRONMENT)
        client = boto_session.client(service_name='dynamodb')

        # This will raise a EndpointConnectionError if there is a network error with the database
        client.describe_endpoints()

        return client

    except EndpointConnectionError as e:
        raise db_exceptions.DynamoDBConnectionError(str(e)) from e


def get_all_tables() -> list[str, ...]:
    client = _get_boto_dynamo_client()

    response = client.list_tables()

    return response['TableNames']


def get_all_items_from_table(table: str) -> list[dict[str, dict[str, str]], ...]:
    client = _get_boto_dynamo_client()

    response = client.scan(TableName=table, Select='ALL_ATTRIBUTES')

    return response['Items']


def get_item_from_table(
    table: str, partition_key_key: str, partition_key_value: str | int | float | bytes
) -> dict[str, dict[str, Any]] | None:
    client = _get_boto_dynamo_client()

    ty = _get_ty(partition_key_value)
    key = {partition_key_key: {ty: partition_key_value}}

    response = client.get_item(TableName=table, Key=key)

    return response.get('Item')


def item_exists_in_table(table: str, partition_key_key: str, partition_key_value: str | int | float | bytes) -> bool:
    client = _get_boto_dynamo_client()

    ty = _get_ty(partition_key_value)
    key = {partition_key_key: {ty: partition_key_value}}

    response = client.get_item(TableName=table, Key=key)

    return bool(response.get('Item'))


def store_item_in_table(
    table: str, partition_key_key: str, partition_key_value: str | int | float | bytes, **items: Any
):
    client = _get_boto_dynamo_client()

    ty = _get_ty(partition_key_value)
    additional_items = _normalize_additional_items(method=NormalizeMethod.Store, **items)
    all_items_normalized = {partition_key_key: {ty: partition_key_value}, **additional_items}

    response = client.put_item(
        TableName=table, Item=all_items_normalized, ConditionExpression=f"attribute_not_exists({partition_key_key})"
    )

    return response


def update_item_in_table(
    table: str, partition_key_key: str, partition_key_value: str | int | float | bytes, **items: Any
):
    client = _get_boto_dynamo_client()

    ty = _get_ty(partition_key_value)
    attribute_updates = _normalize_additional_items(method=NormalizeMethod.Update, **items)
    key = {partition_key_key: {ty: partition_key_value}}

    response = client.update_item(TableName=table, Key=key, AttributeUpdates=attribute_updates)

    return response


def delete_items_from_table(table: str, partition_key_key: str, *items: str | int | float | bytes):
    response = []

    for username in items:
        client = _get_boto_dynamo_client()

        ty = _get_ty(username)
        key = {partition_key_key: {ty: username}}
        deleted = client.delete_item(TableName=table, Key=key)

        response.append(deleted)

    return response


def delete_item_values_from_table(
    table: str, partition_key_key: str, partition_key_value: str | int | float | bytes, *item_values: str
):
    client = _get_boto_dynamo_client()

    ty = _get_ty(partition_key_value)
    key = {partition_key_key: {ty: partition_key_value}}
    attribute_updates = {item_value: {'Action': 'DELETE'} for item_value in item_values}

    response = client.update_item(TableName=table, Key=key, AttributeUpdates=attribute_updates)

    return response


if __name__ == '__main__':
    pass
    # AWS_ENVIRONMENT = "cg_dev"
    # _dev_only_create_table()
    # print(get_all_tables())
    # print(get_all_items_from_table('Users'))
    # print(update_item_in_table(table="Users",
    #                            username="carlo3",
    #                            hashed_password=b'$2b$12$Ny/Kcyv5j8SJi8MNjU1lKOutKTxQYCoiqoWBPRRtm80NrXkw/KHCW',
    #                            reset_code="1234asdf",
    #                            new_key="new_value"))
    # print(get_all_items_from_table('Users'))
    # print(item_exists_in_table('Users', 'carlo'))
