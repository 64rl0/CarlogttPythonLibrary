# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# database_dynamo.py
# Created 9/30/23 - 4:38 PM UK Time (London) by carlogtt
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
import decimal
import logging
import numbers
import time
from collections.abc import Generator, Iterable, Mapping, MutableMapping, Sequence
from typing import Any, Literal, Optional, Union

# Third Party Library Imports
import boto3
import botocore.exceptions
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef as DynamoDBAttribute
from mypy_boto3_dynamodb.type_defs import AttributeValueUpdateTypeDef as DynamoDBAttributeUpdate
from mypy_boto3_dynamodb.type_defs import (
    ConditionCheckTypeDef,
    DeleteTypeDef,
    PutTypeDef,
    TransactWriteItemTypeDef,
    UpdateTypeDef,
)

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'DynamoDB',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
# A list is just a list of attribute values
# Placeholder, replace Any with DynamoDBAttributeValue later
DynamoDBList = Sequence[Any]
DynamoDBListSerialized = Sequence[Any]
DynamoDBListDeserialized = Sequence[Any]

# A map is a string-to-attribute-value dictionary
# Placeholder, replace Any with DynamoDBAttributeValue later
DynamoDBMap = Mapping[str, Any]
DynamoDBMapSerialized = Mapping[str, Any]
DynamoDBMapDeserialized = Mapping[str, Any]

# All accepted types for DynamoDB attribute value
DynamoDBAttributeValue = Union[
    str,
    bytes,
    bytearray,
    int,
    float,
    decimal.Decimal,
    set[str],
    set[bytes],
    set[int],
    set[float],
    set[decimal.Decimal],
    DynamoDBList,
    DynamoDBMap,
    bool,
    None,
]

DynamoDBAttributeValueSerialized = Union[
    str,
    bytes,
    bytearray,
    set[str],
    set[bytes],
    DynamoDBListSerialized,
    DynamoDBMapSerialized,
    bool,
]

DynamoDBAttributeValueDeserialized = Union[
    str,
    bytes,
    bytearray,
    int,
    decimal.Decimal,
    set[str],
    set[bytes],
    set[int],
    set[decimal.Decimal],
    DynamoDBListDeserialized,
    DynamoDBMapDeserialized,
    bool,
    None,
]

# Now replace the placeholders with actual definition
DynamoDBList = Sequence[DynamoDBAttributeValue]  # type: ignore
DynamoDBMap = Mapping[str, DynamoDBAttributeValue]  # type: ignore

DynamoDBListSerialized = Sequence[DynamoDBAttributeValueSerialized]  # type: ignore
DynamoDBMapSerialized = Mapping[str, DynamoDBAttributeValueSerialized]  # type: ignore

DynamoDBListDeserialized = Sequence[DynamoDBAttributeValueDeserialized]  # type: ignore
DynamoDBMapDeserialized = Mapping[str, DynamoDBAttributeValueDeserialized]  # type: ignore

# General DynamoDB type annotations
DynamoDBItem = dict[str, DynamoDBAttribute]
DynamoDBPartitionKeyValue = Union[bytes, str, float]


class DynamoDB:
    """
    The DynamoDB class provides a simplified interface for interacting
    with Amazon DynamoDB services within a Python application.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    :param aws_region_name: The name of the AWS region where the
           service is to be used. This parameter is required to
           configure the AWS client.
    :param aws_profile_name: The name of the AWS profile to use for
           credentials. This is useful if you have multiple profiles
           configured in your AWS credentials file.
           Default is None, which means the default profile or
           environment variables will be used if not provided.
    :param aws_access_key_id: The AWS access key ID for
           programmatically accessing AWS services. This parameter
           is optional and only needed if not using a profile from
           the AWS credentials file.
    :param aws_secret_access_key: The AWS secret access key
           corresponding to the provided access key ID. Like the
           access key ID, this parameter is optional and only needed
           if not using a profile.
    :param caching: Determines whether to enable caching for the
           client session. If set to True, the client session will
           be cached to improve performance and reduce the number
           of API calls. Default is False.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        caching: bool = False,
    ) -> None:
        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._aws_service_name: Literal['dynamodb'] = "dynamodb"

    @property
    def _client(self) -> DynamoDBClient:
        """
        Returns a DynamoDB client.
        Caches the client if caching is enabled.

        :return: The DynamoDBClient.
        """

        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_client()
            return self._cache['client']

        else:
            return self._get_boto_client()

    def _get_boto_client(self) -> DynamoDBClient:
        """
        Create a low-level DynamoDB client.

        :return: The DynamoDBClient.
        :raise DynamoDBError: If operation fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
            )
            client = boto_session.client(service_name=self._aws_service_name)

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise DynamoDBError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.DynamoDBError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def get_all_tables(self) -> list[str]:
        """
        Returns an array of table names associated with the current
        account and endpoint.

        :return: List of table names.
        :raise DynamoDBError: If listing fails.
        """

        try:
            dynamodb_response = self._client.list_tables()

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # If TableNames is not present then return an empty list
        try:
            response = dynamodb_response['TableNames']

        except KeyError:
            response = []

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def get_all_items_in_table(
        self, table: str
    ) -> Generator[dict[str, DynamoDBAttributeValueDeserialized], None, None]:
        """
        Returns an Iterable of deserialized items in the table.

        :param table: DynamoDB table name.
        :return: Generator of deserialized items.
            Iterable of dictionaries of all the columns in DynamoDB
            i.e. {dynamodb_column_name: column_value, ...}
        :raise DynamoDBError: If retrieval fails.
        """

        dynamodb_scan_args: dict[str, Any] = {'TableName': table}

        try:
            while True:
                try:
                    dynamodb_response = self._client.scan(**dynamodb_scan_args)

                except botocore.exceptions.ClientError as ex:
                    raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

                except Exception as ex:
                    raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

                if dynamodb_response.get('Items') and len(dynamodb_response['Items']) > 0:
                    # Convert the DynamoDB attribute values to
                    # deserialized values
                    deserialized_items = (
                        {
                            key: self._deserialize_attribute(value)
                            for key, value in dynamodb_item.items()
                        }
                        for dynamodb_item in dynamodb_response['Items']
                    )

                    yield from deserialized_items

                # If LastEvaluatedKey is present then we need to scan
                # for more items
                if dynamodb_response.get('LastEvaluatedKey'):
                    dynamodb_scan_args['ExclusiveStartKey'] = dynamodb_response['LastEvaluatedKey']

                # If no LastEvaluatedKey then break out of the while
                # loop as we're done
                else:
                    break

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

    def get_count_of_all_items_in_table(self, table: str) -> int:
        """
        Returns the number of items in a table.

        :param table: DynamoDB table name.
        :return: Item count.
        :raise DynamoDBError: If count fails.
        """

        response = len(list(self.get_all_items_in_table(table)))

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def get_item_from_table(
        self, table: str, partition_key_key: str, partition_key_value: DynamoDBPartitionKeyValue
    ) -> Optional[dict[str, DynamoDBAttributeValueDeserialized]]:
        """
        The get_item_from_table operation returns a dictionary of
        deserialized attribute values for the item with the given
        primary key. If there is no matching item, get_item_from_table
        returns None.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.:
        :return: Deserialized item or None.
        :raise DynamoDBError: If retrieval fails.
        """

        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        try:
            dynamodb_response = self._client.get_item(TableName=table, Key=partition_key)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        dynamodb_item = dynamodb_response.get('Item')

        if not dynamodb_item:
            return None

        # Convert the DynamoDB attribute values to deserialized values
        response = {key: self._deserialize_attribute(value) for key, value in dynamodb_item.items()}

        return response

    def put_item_in_table(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Optional[DynamoDBPartitionKeyValue] = None,
        auto_generate_partition_key_value: Optional[bool] = False,
        **items: DynamoDBAttributeValue,
    ) -> dict[str, DynamoDBAttributeValueDeserialized]:
        """
        Creates a new item. If an item that has the same primary key as
        the new item already exists in the specified table, the
        operation will fail.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :param auto_generate_partition_key_value: If set to True, this
            option instructs DynamoDB to automatically generate a
            partition key value based on a counter mechanism.
            For this to work, your table must contain a special item
            with its partition key value set to '__PK_VALUE_COUNTER__'.
            This item should have a numerical attribute named
            'current_counter_value', which will be used and incremented
            as the basis for generating new partition key values.
        :param items: Additional items to add.
        :return: The stored DynamoDB Item deserialized.
        :raise DynamoDBError: If operation fails.
        :raise DynamoDBConflictError: If put item fails due to a
            conflict.
        """

        if partition_key_value is not None and auto_generate_partition_key_value is True:
            raise exceptions.DynamoDBError(
                "If auto_generate_partition_key_value is enabled, a partition_key_value MUST NOT be"
                " passed in."
            )

        elif partition_key_value is None and auto_generate_partition_key_value is False:
            raise exceptions.DynamoDBError(
                "If auto_generate_partition_key_value is disabled, a partition_key_value MUST be"
                " passed in."
            )

        elif partition_key_value is not None and auto_generate_partition_key_value is False:
            # If we don't need to increment the counter we just put the
            # item in the table
            item_put = self._put_single_item_in_table(
                table=table,
                partition_key_key=partition_key_key,
                partition_key_value=partition_key_value,
                **items,
            )

        elif partition_key_value is None and auto_generate_partition_key_value is True:
            # If we need to increment the counter we do it with an
            # atomic write
            # Put new item
            put_in_db: list[dict[str, DynamoDBAttributeValue]] = [
                {
                    'TableName': table,
                    'PartitionKeyKey': partition_key_key,
                    'AutoGeneratePartitionKeyValue': True,
                    'Items': items,
                },
            ]

            atomic_write_response = self.atomic_writes_in_table(put=put_in_db)

            # If we get here it means that the item has been added
            # successfully therefore we return it
            item_put = atomic_write_response['Put'][0]

        else:
            raise exceptions.DynamoDBError(
                "Unable to determine a valid operation with the provided 'partition_key_value' and"
                " 'auto_generate_partition_key_value'."
            )

        return item_put

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def _put_single_item_in_table(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Optional[DynamoDBPartitionKeyValue] = None,
        **items: DynamoDBAttributeValue,
    ) -> dict[str, DynamoDBAttributeValueDeserialized]:
        """
        Put the item in the table.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :param items: Additional items to add.
        :return: The stored DynamoDB Item deserialized.
        :raise DynamoDBError: If operation fails.
        :raise DynamoDBConflictError: If put item fails due to a
            conflict.
        """

        assert isinstance(partition_key_value, (bytes, str, float))

        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )
        additional_items = self._serialize_items_for_put(**items)
        all_items_serialized = {**partition_key, **additional_items}

        try:
            self._client.put_item(
                TableName=table,
                Item=all_items_serialized,
                ConditionExpression=f"attribute_not_exists({partition_key_key})",
            )

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(f"Conflict Detected! - {str(ex.response)}")

            else:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # If we get here it means that the item has been added
        # successfully therefore we return it
        item_put = {
            key: self._deserialize_attribute(value) for key, value in all_items_serialized.items()
        }

        return item_put

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def update_item_in_table(
        self,
        table: str,
        partition_key: dict[str, DynamoDBPartitionKeyValue],
        condition_attribute: Optional[dict[str, Any]] = None,
        **items: DynamoDBAttributeValue,
    ):
        """
        Edits an existing item’s attributes. If
        condition_attribute_value is passed, the item will be updated
        only if condition_attribute_value is a match with the value
        stored in DynamoDB under last_modified_timestamp.

        :param table: DynamoDB table name.
        :param partition_key: DynamoDB partition key as dict of
            partition_key {key: value}.
        :param condition_attribute: DynamoDB attribute to matched as
            dict of attribute_to_match {key: value}. When sent to
            DynamoDB, the attribute will be as a condition to match.
        :param items: Values for items to be updated.
        :return: The updated DynamoDB Item deserialized.
        :raise DynamoDBError: If update fails.
        :raise DynamoDBConflictError: If update fails due to a conflict.
        """

        # items is an optional parameter by default as using the **
        # However, if no values are passed as **items we raise an
        # exception as there is nothing to update
        if not items:
            raise exceptions.DynamoDBError(
                "Operation failed! - No values to update were passed to the DynamoDB"
                " update_item_in_table method."
            )

        # Initialize a dictionary with all the arguments to pass into
        # the DynamoDB update_item call
        dynamodb_update_item_args: dict[str, Any] = {'TableName': table, 'ReturnValues': 'ALL_OLD'}

        # Serialize partition key
        # We cant mutate the original dictionary because of the
        # retry decorator will need to run through it again in case
        # of failure
        partition_key_key, partition_key_value = next(iter(partition_key.items()))
        partition_key_serialized = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        # Serialize attributes
        update_attributes, expression_attribute_values = self._serialize_items_for_update(**items)

        # Check if a condition is required
        if condition_attribute is not None:
            # Unpack condition attribute dictionary
            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            condition_attribute_key, condition_attribute_value = next(
                iter(condition_attribute.items())
            )

            # If condition attribute exists pass it to the DynamoDB call
            dynamodb_update_item_args.update({
                'ConditionExpression': (
                    f"{condition_attribute_key} = :condition_attribute_value_placeholder"
                )
            })
            # :condition_attribute_value_placeholder has to be passed
            # along the ExpressionAttributeValues because is used by the
            # ConditionExpression
            expression_attribute_values[':condition_attribute_value_placeholder'] = (
                self._serialize_attribute(condition_attribute_value)
            )

        # Update DynamoDB call arguments
        dynamodb_update_item_args['Key'] = partition_key_serialized
        dynamodb_update_item_args['UpdateExpression'] = update_attributes
        dynamodb_update_item_args['ExpressionAttributeValues'] = expression_attribute_values

        module_logger.debug(dynamodb_update_item_args)

        try:
            dynamodb_response = self._client.update_item(**dynamodb_update_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(f"Conflict Detected! - {str(ex.response)}")

            else:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # If we get here it means that the item has been updated
        # successfully therefore we return it
        old_item = dynamodb_response.get('Attributes', {})
        old_item_deserialized = {
            key: self._deserialize_attribute(value) for key, value in old_item.items()
        }
        updated_item = {**partition_key, **old_item_deserialized, **items}

        return updated_item

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def delete_items_from_table(
        self, table: str, partition_key_key: str, *partition_key_values: DynamoDBPartitionKeyValue
    ):
        """
        Deletes item(s) in a table by primary key.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_values: The values of the partition key of
            the items to delete from DynamoDB
        :return: Response from deletion.
        :raise DynamoDBError: If deletion fails.
        """

        response = []

        for partition_key_value in partition_key_values:
            partition_key = self._serialize_partition_key_for_dynamodb(
                partition_key_key, partition_key_value
            )

            try:
                dynamodb_response = self._client.delete_item(TableName=table, Key=partition_key)

            except botocore.exceptions.ClientError as ex:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

            except Exception as ex:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

            response.append(dynamodb_response)

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def delete_item_values_from_table(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: DynamoDBPartitionKeyValue,
        attributes_to_delete: Iterable[str],
    ):
        """
        Deletes item specific values in a table by primary key.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :param attributes_to_delete: An iterable of specific attributes
            that are to be deleted from DynamoDB.
        :return: Response from deletion.
        :raise DynamoDBError: If deletion fails.
        """

        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        attribute_updates: dict[str, DynamoDBAttributeUpdate] = {
            item_value: {'Action': "DELETE"} for item_value in attributes_to_delete
        }

        try:
            dynamodb_response = self._client.update_item(
                TableName=table, Key=partition_key, AttributeUpdates=attribute_updates
            )

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(f"Conflict Detected! - {str(ex.response)}")

            else:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        return dynamodb_response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def atomic_writes_in_table(
        self,
        put: Optional[Iterable[dict[str, DynamoDBAttributeValue]]] = None,
        update: Optional[Iterable[dict[str, DynamoDBAttributeValue]]] = None,
        delete: Optional[Iterable[dict[str, DynamoDBAttributeValue]]] = None,
        condition_check: Optional[Iterable[dict[str, DynamoDBAttributeValue]]] = None,
        **kwargs,
    ):
        """
        A synchronous write operation that groups up to 100 action
        requests. These actions can target items in different tables.
        The actions are completed atomically so that either all of them
        succeed, or all of them fail.

        :param put: Initiates a PutItem operation to write a new item.
            schema = {
                'TableName': "string DynamoDB Table Name",
                'PartitionKeyKey': "string of the Partition key key",
                'PartitionKeyValue': "OPTIONAL - partition key value",
                'AutoGeneratePartitionKeyValue': "OPTIONAL - bool",
                'Items': "dict containing all the items to put in
                    DynamoDB",
                }
        :param update: Initiates an UpdateItem operation to update an
            existing item.
            schema = {
                'TableName': "string DynamoDB Table Name",
                'PartitionKey': "The partition key as dict of
                    partition_key {key: value}",
                'Items': "dict containing all the values for items to be
                    updated",
                'ConditionAttribute': "OPTIONAL - attribute to matched
                    as dict of attribute_to_match {key: value}",
                }
        :param delete: Initiates a DeleteItem operation to delete an
            existing item.
            schema = {
                'TableName': "string DynamoDB Table Name",
                'PartitionKey': "The partition key as dict of
                    partition_key {key: value}",
                }
        :param condition_check: Applies a condition to an item that is
            not being modified by the transaction. The condition must
            be satisfied for the transaction to succeed.
            schema = {
                'TableName': "string DynamoDB Table Name",
                'PartitionKey': "The partition key as dict of
                    partition_key {key: value}",
                }
        :return: A dictionary with keys
            'Put', 'Update', 'Delete', 'ConditionCheck',
            and a list of items writes to the DynamoDB in the same
            order as they were passed in.
            schema = {
                'Put': "list of items writes to DynamoDB",
                'Update': "list of items writes to DynamoDB",
                'Delete': "list of items writes to DynamoDB",
                'ConditionCheck': "list of items writes to DynamoDB",
                }
        :raise DynamoDBError: If atomic writes fail.
        :raise DynamoDBConflictError: If atomic writes fail due to a
            conflict.
        """

        # Initialize missing arguments
        put = put or {}
        update = update or {}
        delete = delete or {}
        condition_check = condition_check or {}

        # Prepare the list of transactional items to be passed to the
        # DynamoDB call
        transact_items: list[TransactWriteItemTypeDef] = []

        # Prepare the response object
        response: dict[str, list[dict[str, DynamoDBAttributeValue]]] = {
            'Put': [],
            'Update': [],
            'Delete': [],
            'ConditionCheck': [],
        }

        module_logger.debug(
            f"Atomic Writes in Table - Put: {put}, Update: {update}, Delete: {delete},"
            f" ConditionCheck: {condition_check}"
        )

        # Normalize each put item in the list for DynamoDB
        # transactional call
        for el in put:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['Items'], Mapping)
            assert isinstance(el['PartitionKeyKey'], str)

            if (
                el.get('PartitionKeyValue') is not None
                and el.get('AutoGeneratePartitionKeyValue', False) is True
            ):
                raise exceptions.DynamoDBError(
                    "If AutoGeneratePartitionKeyValue is enabled, a PartitionKeyValue MUST NOT be"
                    " passed in."
                )

            elif (
                el.get('PartitionKeyValue') is not None
                and el.get('AutoGeneratePartitionKeyValue', False) is False
            ):
                # This is the case where
                # el['PartitionKeyValue'] = el['PartitionKeyValue']
                pass

            elif (
                el.get('PartitionKeyValue') is None
                and el.get('AutoGeneratePartitionKeyValue', False) is True
            ):
                # This is the case where we auto generate the id
                current_counter_value, last_modified_timestamp = self._get_atomic_counter(
                    table=el['TableName']
                )
                new_counter_value = current_counter_value + 1

                # Check what is the type of the PartitionKey key of
                # the table
                pk_type = self._get_pk_type(table=el['TableName'])

                if issubclass(pk_type, str):
                    auto_generate_pk_value: Union[str, bytes, float] = str(new_counter_value)

                elif issubclass(pk_type, bytes):
                    auto_generate_pk_value = str(new_counter_value).encode()

                elif issubclass(pk_type, float):
                    auto_generate_pk_value = new_counter_value

            elif (
                el.get('PartitionKeyValue') is None
                and el.get('AutoGeneratePartitionKeyValue', False) is False
            ):
                raise exceptions.DynamoDBError(
                    "If AutoGeneratePartitionKeyValue is disabled, a PartitionKeyValue MUST be"
                    " passed in."
                )

            else:
                raise exceptions.DynamoDBError(
                    "Unable to determine a valid operation with the provided PartitionKeyValue and"
                    " AutoGeneratePartitionKeyValue."
                )

            partition_key_value = el.get('PartitionKeyValue') or auto_generate_pk_value

            # If we don't need to increment the counter we just put the
            # item in the table
            el_put_serialized: PutTypeDef = {
                'TableName': el['TableName'],
                'Item': self._serialize_items_for_put(
                    **{el['PartitionKeyKey']: partition_key_value, **el['Items']}
                ),
                'ConditionExpression': f"attribute_not_exists({el['PartitionKeyKey']})",
            }

            # Append the 'put' item to the DynamoDB atomic call
            transact_items.append({'Put': el_put_serialized})

            # Append the 'put' item to the return list
            response['Put'].append({
                key: self._deserialize_attribute(value)  # type: ignore
                for key, value in el_put_serialized['Item'].items()
            })

            # If we need to increment the counter we update the counter
            if el.get('AutoGeneratePartitionKeyValue'):
                # Update the counter
                counter_update_serialized = self._set_atomic_counter(
                    table=el['TableName'],
                    counter_value=new_counter_value,
                    last_modified_timestamp=last_modified_timestamp,
                )

                # Append the 'update' item to the DynamoDB atomic call
                transact_items.append({'Update': counter_update_serialized})

                # Append the 'update' item to the return list
                updated_item = {
                    key[1:-12]: self._deserialize_attribute(value)  # type: ignore
                    for key, value in counter_update_serialized['ExpressionAttributeValues'].items()
                }
                del updated_item['condition_attribute_value']
                p_key_key, p_key_value = dict(counter_update_serialized['Key']).popitem()
                updated_item[p_key_key] = self._deserialize_attribute(p_key_value)  # type: ignore
                response['Update'].append(updated_item)  # type: ignore

        # Normalize each update item in the list for DynamoDB
        # transactional call
        for el in update:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['Items'], Mapping)
            assert isinstance(el['PartitionKey'], MutableMapping)

            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            partition_key_key, partition_key_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(partition_key_value, (bytes, str, float))

            update_attributes, expression_attribute_values = self._serialize_items_for_update(
                **el['Items']
            )

            el_update_serialized: UpdateTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serialize_partition_key_for_dynamodb(
                    partition_key_key, partition_key_value
                ),
                'UpdateExpression': update_attributes,
                'ExpressionAttributeValues': expression_attribute_values,
            }

            # Check if a condition is passed in
            if el.get('ConditionAttribute') is not None:
                # Unpack condition attribute dictionary
                assert isinstance(el['ConditionAttribute'], MutableMapping)
                # We cant mutate the original dictionary because of the
                # retry decorator will need to run through it again in
                # case of failure
                condition_att_key, condition_att_value = next(
                    iter(el['ConditionAttribute'].items())
                )

                # If condition attribute exists pass it to the DynamoDB
                # call
                el_update_serialized.update({
                    'ConditionExpression': (
                        f"{condition_att_key} = :condition_attribute_value_placeholder"
                    )
                })
                # :condition_attribute_value_placeholder has to be
                # passed along the ExpressionAttributeValues because
                # is used by the ConditionExpression
                expression_attribute_values[':condition_attribute_value_placeholder'] = (
                    self._serialize_attribute(condition_att_value)
                )

            # Append the 'update' item to the DynamoDB atomic call
            transact_items.append({'Update': el_update_serialized})

            # Append the 'update' item to the return list
            updated_item = {
                key[1:-12]: self._deserialize_attribute(value)
                for key, value in expression_attribute_values.items()
            }
            if el.get('ConditionAttribute') is not None:
                del updated_item['condition_attribute_value']
            p_key_key, p_key_value = dict(el_update_serialized['Key']).popitem()
            updated_item[p_key_key] = self._deserialize_attribute(p_key_value)  # type: ignore
            response['Update'].append(updated_item)  # type: ignore

        # Normalize each delete item in the list for DynamoDB
        # transactional call
        for el in delete:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['PartitionKey'], MutableMapping)

            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            partition_key_key, partition_key_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(partition_key_value, (bytes, str, float))

            el_delete_serialized: DeleteTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serialize_partition_key_for_dynamodb(
                    partition_key_key, partition_key_value
                ),
            }

            # Append the 'delete' item to the DynamoDB atomic call
            transact_items.append({'Delete': el_delete_serialized})

            # Append the 'delete' item to the return list
            response['Delete'].append({partition_key_key: partition_key_value})

        # Normalize each conditional check item in the list for DynamoDB
        # transactional call
        for el in condition_check:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['PartitionKey'], MutableMapping)

            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            partition_key_key, partition_key_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(partition_key_value, (bytes, str, float))

            el_condition_check_serialized: ConditionCheckTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serialize_partition_key_for_dynamodb(
                    partition_key_key, partition_key_value
                ),
                # TODO(carlogtt): not sure how to use the below yet
                'ConditionExpression': 'string',
                'ExpressionAttributeNames': {'string': 'string'},
                'ExpressionAttributeValues': {},
            }

            # Append the 'condition_check' item to the DynamoDB atomic
            # call
            transact_items.append({'ConditionCheck': el_condition_check_serialized})

            # Append the 'condition_check' item to the return list
            response['ConditionCheck'].append({partition_key_key: partition_key_value})

        # Make the DynamoDB atomic api call
        try:
            self._client.transact_write_items(TransactItems=transact_items, **kwargs)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(f"Conflict Detected! - {str(ex.response)}")

            else:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def put_atomic_counter_in_table(
        self,
        table: str,
    ):
        """
        In Amazon DynamoDB, there isn't an in-built auto-increment
        functionality like in SQL databases for generating record IDs
        (Primary Key values). However, we can achieve a similar outcome
        by managing an atomic counter.
        This method put the initial __PK_VALUE_COUNTER__ item in the
        table and set the value to 0.
        If the __PK_VALUE_COUNTER__ item already exists in the table
        then it does nothing.

        :param table: DynamoDB table name.
        :return: None
        :raise DynamoDBError: If operation fails.
        """

        # Using the tableName_SysItems table for lookup
        sys_table = table + "_SysItems"
        partition_key = self._serialize_partition_key_for_dynamodb("pk_id", "__PK_VALUE_COUNTER__")

        try:
            dynamodb_response = self._client.get_item(TableName=sys_table, Key=partition_key)
            counter = dynamodb_response.get('Item')

        except self._client.exceptions.ResourceNotFoundException:
            module_logger.debug(f"Table: {sys_table} not found in DynamoDB, Creating it.")

            try:
                self._client.create_table(
                    TableName=sys_table,
                    BillingMode='PAY_PER_REQUEST',
                    AttributeDefinitions=[{
                        'AttributeName': 'pk_id',
                        'AttributeType': 'S',
                    }],
                    KeySchema=[{
                        'AttributeName': 'pk_id',
                        'KeyType': 'HASH',
                    }],
                    DeletionProtectionEnabled=True,
                )

                # Give it time to create the table
                time.sleep(15)

                # Setting the counter to None, so we can put the counter
                # item in the newly created table
                counter = None

            except botocore.exceptions.ClientError as ex:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

            except Exception as ex:
                raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        if not counter:
            self.put_item_in_table(
                table=sys_table,
                partition_key_key="pk_id",
                partition_key_value="__PK_VALUE_COUNTER__",
                current_counter_value=0,
                last_modified_timestamp=time.time_ns(),
            )

    def _get_atomic_counter(self, table: str) -> tuple[int, int]:
        """
        This method will get the value of the atomic counter.

        :param table: DynamoDB table name.
        :return: Counter value and last_modified_timestamp as tuple.
        :raise DynamoDBError: If counter not found.
        """

        # Using the tableName_SysItems table for lookup
        sys_table = table + "_SysItems"

        try:
            item = self.get_item_from_table(
                table=sys_table,
                partition_key_key="pk_id",
                partition_key_value="__PK_VALUE_COUNTER__",
            )
            assert item is not None

            current_counter_value = item['current_counter_value']
            assert isinstance(current_counter_value, int)

            last_modified_timestamp = item['last_modified_timestamp']
            assert isinstance(last_modified_timestamp, int)

        except AssertionError:
            raise exceptions.DynamoDBError(
                f"table: {table!r} doesn't have the '__PK_VALUE_COUNTER__' item, call"
                f" '{self.put_atomic_counter_in_table.__name__}' to create one."
            )

        except (TypeError, KeyError):
            raise exceptions.DynamoDBError(
                f"Item '__PK_VALUE_COUNTER__' in table: {table!r} is missing some or all of the"
                " mandatory attributes: 'current_counter_value' and 'last_modified_timestamp'."
            )

        except Exception as ex:
            if "ResourceNotFoundException" in str(ex):
                raise exceptions.DynamoDBError(
                    f"'__PK_VALUE_COUNTER__' not found as table: '{table}_SysItems' doesn't exists,"
                    f" call '{self.put_atomic_counter_in_table.__name__}('{table}')' to create one."
                )

            else:
                raise

        return current_counter_value, last_modified_timestamp

    def _set_atomic_counter(
        self, table: str, counter_value: int, last_modified_timestamp: int
    ) -> UpdateTypeDef:
        """
        This method will prepare an atomic update dictionary.

        :param table: DynamoDB table name.
        :param counter_value: The new value to se to the counter.
        :param last_modified_timestamp: The last modified timestamp to
            use as condition expression.
        :return: An atomic update dictionary.
        :raise DynamoDBError: If operation fails.
        """

        # Using the tableName_SysItems table for lookup
        sys_table = table + "_SysItems"

        # Update the counter
        update_attributes, expression_attribute_values = self._serialize_items_for_update(**{
            'current_counter_value': counter_value,
            'last_modified_timestamp': time.time_ns(),
        })

        # :condition_attribute_value_placeholder has to be
        # passed along the ExpressionAttributeValues because
        # is used by the ConditionExpression
        expression_attribute_values[':condition_attribute_value_placeholder'] = (
            self._serialize_attribute(last_modified_timestamp)
        )

        el_update_serialized: UpdateTypeDef = {
            'TableName': sys_table,
            'Key': self._serialize_partition_key_for_dynamodb("pk_id", "__PK_VALUE_COUNTER__"),
            'UpdateExpression': update_attributes,
            'ConditionExpression': (
                "last_modified_timestamp = :condition_attribute_value_placeholder"
            ),
            'ExpressionAttributeValues': expression_attribute_values,
        }

        return el_update_serialized

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def _get_pk_type(self, table: str) -> Union[type[bytes], type[str], type[float]]:
        """
        Scan the table and return the type of the PartitionKey Key.

        :param table: DynamoDB table name.
        :return: The type of the PartitionKey key.
        :raise DynamoDBError: If operation fails.
        """

        # Initialize values to prevent UnboundLocalError
        partition_key_key = ""
        partition_key_key_type = ""

        try:
            dynamodb_response = self._client.describe_table(TableName=table)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex.response)}")

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # Get the PartitionKey Key
        for idx, schemas in enumerate(dynamodb_response['Table']['KeySchema']):
            for k, v in schemas.items():
                if k == 'KeyType' and v == 'HASH':
                    partition_key_key = dynamodb_response['Table']['KeySchema'][idx][
                        'AttributeName'
                    ]

        # Get the PartitionKey Key Type
        for idx, attributes in enumerate(dynamodb_response['Table']['AttributeDefinitions']):
            for k, v in attributes.items():
                if k == 'AttributeName' and v == partition_key_key:
                    partition_key_key_type = dynamodb_response['Table']['AttributeDefinitions'][
                        idx
                    ]['AttributeType']

        # Convert to Python type and return
        if partition_key_key_type == 'S':
            return str

        elif partition_key_key_type == 'B':
            return bytes

        elif partition_key_key_type == 'N':
            return float

        else:
            raise exceptions.DynamoDBError("Operation failed! - PartitionKey Key Type not found")

    @staticmethod
    def _serialize_attribute(attribute_value: DynamoDBAttributeValue) -> DynamoDBAttribute:
        """
        Serialize a Python data type into a format suitable for
        AWS DynamoDB.
        Transforms a Python data type into a format that is compatible
        with AWS DynamoDB by mapping it into its corresponding DynamoDB
        data type.

        :param attribute_value: The attribute value to be serialized.
        :return: A dictionary containing the serialized attribute and
            its corresponding DynamoDB data type descriptor.
            i.e. "string" -> {"S": "string"}
        :raise DynamoDBError: If the provided attribute_value type is
            not supported.
        """

        if attribute_value is None:
            return {"NULL": True}

        elif isinstance(attribute_value, bool):
            return {"BOOL": attribute_value}

        elif isinstance(attribute_value, str):
            return {"S": attribute_value}

        elif isinstance(attribute_value, bytes) or isinstance(attribute_value, bytearray):
            return {"B": attribute_value}

        elif isinstance(attribute_value, numbers.Real) or isinstance(
            attribute_value, decimal.Decimal
        ):
            return {"N": str(attribute_value)}

        elif isinstance(attribute_value, set) and len(attribute_value) > 0:
            set_el_sample = next(iter(attribute_value))

            # Check if set is homogeneous
            if not all(isinstance(el, type(set_el_sample)) for el in attribute_value):
                raise exceptions.DynamoDBError(
                    f"Value type for {attribute_value!r} is not supported by DynamoDB set. Set must"
                    " be homogeneous."
                )

            if isinstance(set_el_sample, str):
                return {"SS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, bytes):
                return {"BS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, numbers.Real):
                return {"NS": [str(el) for el in attribute_value]}

            else:
                raise exceptions.DynamoDBError(
                    f"Value type for {attribute_value!r} is not supported by DynamoDB set."
                )

        elif isinstance(attribute_value, Sequence):
            list_value = list(attribute_value)
            for idx, el in enumerate(list_value):
                list_value[idx] = DynamoDB._serialize_attribute(el)
            return {"L": list_value}

        elif isinstance(attribute_value, MutableMapping):
            dict_value = dict(attribute_value)
            for key, val in dict_value.items():
                dict_value[key] = DynamoDB._serialize_attribute(val)
            return {"M": dict_value}

        else:
            raise exceptions.DynamoDBError(
                f"Value of type {type(attribute_value)!r} for {attribute_value!r} is not supported"
                " by DynamoDB serialization."
            )

    @staticmethod
    def _deserialize_attribute(
        dynamodb_attribute: DynamoDBAttribute,
    ) -> DynamoDBAttributeValueDeserialized:
        """
        Deserialize an AWS DynamoDB data type into its corresponding
        Python data type. Transforms an AWS DynamoDB attribute into a
        Python data type by identifying the DynamoDB data type
        descriptor and mapping it to its corresponding Python data type.

        :param dynamodb_attribute: The DynamoDB attribute to be
            deserialized. It should be a dictionary containing the
            DynamoDB data type descriptor and the attribute value.
        :return: The deserialized Python data type.
            i.e. i.e. {"S": "string"} -> "string"
        :raise DynamoDBError: If the provided dynamodb_attribute is not
            supported for deserialization.
        """

        # The sentinel value is a unique object identifier used as a
        # default fallback when querying dictionary keys during the
        # deserialization process. The `id(object())` generates a unique
        # id by creating a new generic object, which ensures that the
        # sentinel is not accidentally found in `dynamodb_attribute`
        # dictionary values. Utilizing sentinel helps in distinguishing
        # between a None value and absence of a key. During the
        # deserialization, if the `.get()` method returns the sentinel,
        # it implies the key was not found in `dynamodb_attribute`;
        # otherwise, it returns the actual value (which might be None
        # or other falsy values) related to the looked-up key.
        sentinel = id(object())

        if dynamodb_attribute.get("NULL", sentinel) != sentinel:
            return None

        elif dynamodb_attribute.get("BOOL", sentinel) != sentinel:
            return bool(dynamodb_attribute["BOOL"])

        elif dynamodb_attribute.get("S", sentinel) != sentinel:
            return str(dynamodb_attribute["S"])

        elif dynamodb_attribute.get("B", sentinel) != sentinel:
            return dynamodb_attribute["B"]

        elif dynamodb_attribute.get("N", sentinel) != sentinel:
            if '.' in dynamodb_attribute["N"]:
                return decimal.Decimal(dynamodb_attribute["N"])
            else:
                return int(dynamodb_attribute["N"])

        elif dynamodb_attribute.get("SS", sentinel) != sentinel:
            return set(dynamodb_attribute["SS"])

        elif dynamodb_attribute.get("BS", sentinel) != sentinel:
            return set(dynamodb_attribute["BS"])

        elif dynamodb_attribute.get("NS", sentinel) != sentinel:
            if "." in dynamodb_attribute["NS"][0]:
                return {decimal.Decimal(el) for el in dynamodb_attribute["NS"]}
            else:
                return {int(el) for el in dynamodb_attribute["NS"]}

        elif dynamodb_attribute.get("L", sentinel) != sentinel:
            return [DynamoDB._deserialize_attribute(el) for el in dynamodb_attribute["L"]]

        elif dynamodb_attribute.get("M", sentinel) != sentinel:
            return {
                key: DynamoDB._deserialize_attribute(val)
                for key, val in dynamodb_attribute["M"].items()
            }

        else:
            raise exceptions.DynamoDBError(
                f"Value {dynamodb_attribute!r} of type {type(dynamodb_attribute)!r} is not"
                " supported for DynamoDB deserialization."
            )

    def _serialize_partition_key_for_dynamodb(
        self, partition_key_key: str, partition_key_value: DynamoDBPartitionKeyValue
    ) -> DynamoDBItem:
        """
        Return a serialized DynamoDB partition key.

        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :return: Serialized partition key.
            i.e. {"id": {"S": "string"}}
        """

        partition_key_attribute = self._serialize_attribute(partition_key_value)
        partition_key = {partition_key_key: partition_key_attribute}

        return partition_key

    def _serialize_items_for_put(self, **items: DynamoDBAttributeValue) -> DynamoDBItem:
        """
        Returns a dictionary of additional items with keys and values
        serialized for DynamoDB put_item call.

        :param items: Key-value pairs to serialize.
        :return: Items ready for put_item.
            i.e. {"col1": {"S": "value1"}, "col2": {"S": "value2"},
            "col3": {"S": "value3"}, ...}
        """

        additional_items: DynamoDBItem = {}

        for key, value in items.items():
            normalized_key = utils.snake_case(key)
            dynamodb_attribute = self._serialize_attribute(value)

            # Now add it to the additional_items serialized dictionary
            additional_items[normalized_key] = dynamodb_attribute

        return additional_items

    def _serialize_items_for_update(
        self, **items: DynamoDBAttributeValue
    ) -> tuple[str, DynamoDBItem]:
        """
        Returns a tuple containing the UpdateExpression and the
        ExpressionAttributeValues ready to be passed to the DynamoDB
        update_item call.

        :param items: Key-value pairs to serialize.
        :return: UpdateExpression and ExpressionAttributeValues.
        """

        update_attributes = "SET "

        # In DynamoDB API, the ExpressionAttributeValues dictionary is
        # used to pass in placeholders for values that will be used in
        # your UpdateExpression and ConditionExpression. The keys for
        # these placeholders should start with a : and should not be
        # confused with actual column names.
        expression_attribute_values: DynamoDBItem = {}

        for key, value in items.items():
            normalized_key = utils.snake_case(key)
            normalized_key_dynamodb_placeholder = ":" + normalized_key + "_placeholder"
            dynamodb_attribute = self._serialize_attribute(value)

            # Add to the update_attributes string
            update_attributes += f"{normalized_key} = {normalized_key_dynamodb_placeholder}, "

            # Add to the expression_attribute_values serialized
            # dictionary
            expression_attribute_values[normalized_key_dynamodb_placeholder] = dynamodb_attribute

        # Removing the trailing ", " from the update_attributes string
        update_attributes = update_attributes[:-2]

        return update_attributes, expression_attribute_values
