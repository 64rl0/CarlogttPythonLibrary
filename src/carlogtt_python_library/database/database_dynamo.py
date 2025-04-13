# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/database/database_dynamo.py
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
from typing import Any, Literal, Optional, TypedDict, Union

# Third Party Library Imports
import boto3
import botocore.config
import botocore.exceptions
from mypy_boto3_dynamodb import type_defs
from mypy_boto3_dynamodb.client import DynamoDBClient

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
# Placeholder, replace Any with AttributeValue later
DynamoDbList = Sequence[Any]
DynamoDbListDeserialized = Sequence[Any]
DynamoDbMap = Mapping[str, Any]
DynamoDbMapDeserialized = Mapping[str, Any]

PartitionKeyValue = Union[bytes, str, float]

AttributeValue = Union[
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
    DynamoDbList,
    DynamoDbMap,
    bool,
    None,
]

AttributeValueDeserialized = Union[
    str,
    bytes,
    bytearray,
    int,
    float,
    set[str],
    set[bytes],
    set[int],
    set[float],
    DynamoDbListDeserialized,
    DynamoDbMapDeserialized,
    bool,
    None,
]

# Now replace the placeholders with actual definition
DynamoDbList = Sequence[AttributeValue]  # type: ignore
DynamoDbListDeserialized = Sequence[AttributeValueDeserialized]  # type: ignore
DynamoDbMap = Mapping[str, AttributeValue]  # type: ignore
DynamoDbMapDeserialized = Mapping[str, AttributeValueDeserialized]  # type: ignore

# General DynamoDB type annotations
PartitionKeyTypeDef = TypedDict(
    "PartitionKeyTypeDef",
    {
        "S": str,
        "N": str,
        "B": bytes,
    },
    total=False,
)

PartitionKeyItem = dict[str, PartitionKeyTypeDef]
Item = dict[str, type_defs.AttributeValueTypeDef]


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
    :param aws_session_token: The AWS temporary session token
           corresponding to the provided access key ID. Like the
           access key ID, this parameter is optional and only needed
           if not using a profile.
    :param caching: Determines whether to enable caching for the
           client session. If set to True, the client session will
           be cached to improve performance and reduce the number
           of API calls. Default is False.
    :param client_parameters: A key-value pair object of parameters that
           will be passed to the low-level service client.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        caching: bool = False,
        client_parameters: Optional[dict[str, Any]] = None,
    ) -> None:
        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_session_token = aws_session_token
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._aws_service_name: Literal['dynamodb'] = "dynamodb"
        self._client_parameters = client_parameters if client_parameters else dict()
        self._serializer = DynamoDbSerializer()

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
                aws_session_token=self._aws_session_token,
            )
            client = boto_session.client(
                service_name=self._aws_service_name, **self._client_parameters
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

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
    def get_tables(self) -> list[str]:
        """
        Returns an array of table names associated with the current
        account and endpoint.

        :return: List of table names.
        :raise DynamoDBError: If listing fails.
        """

        try:
            dynamodb_response = self._client.list_tables()

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        # If TableNames is not present then return an empty list
        try:
            response = dynamodb_response['TableNames']

        except KeyError:
            response = []

        return response

    def get_items(self, table: str) -> Generator[dict[str, AttributeValueDeserialized], None, None]:
        """
        Returns an Iterable of deserialized items in the table.

        :param table: DynamoDB table name.
        :return: Generator of deserialized items.
            Iterable of dictionaries of all the columns in DynamoDB
            i.e. {dynamodb_column_name: column_value, ...}
        :raise DynamoDBError: If retrieval fails.
        """

        dynamodb_scan_args: type_defs.ScanInputTypeDef = {'TableName': table}

        try:
            while True:
                try:
                    dynamodb_response = self._scan_with_retry(dynamodb_scan_args)

                except botocore.exceptions.ClientError as ex:
                    raise exceptions.DynamoDBError(str(ex.response))

                except Exception as ex:
                    raise exceptions.DynamoDBError(str(ex))

                if dynamodb_response.get('Items') and len(dynamodb_response['Items']) > 0:
                    # Convert the DynamoDB attribute values to
                    # deserialized values
                    deserialized_items = (
                        {
                            key: self._serializer.deserialize_att(value)
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
            raise exceptions.DynamoDBError(str(ex))

    @utils.retry(exception_to_check=Exception, tries=3, delay_secs=1)
    def _scan_with_retry(
        self, dynamodb_scan_args: type_defs.ScanInputTypeDef
    ) -> type_defs.ScanOutputTypeDef:
        """
        Scan a DynamoDB table with built-in retry logic.

        :param dynamodb_scan_args:
            Dictionary of parameters for the DynamoDB `scan` operation,
            e.g. `{"TableName": "my-table", "FilterExpression": ...}`.
        :return:
            The raw DynamoDB scan response from the Boto3 client. This
            includes items (if any), plus pagination data like
            `LastEvaluatedKey`.
        """

        return self._client.scan(**dynamodb_scan_args)

    def get_items_count(self, table: str) -> int:
        """
        Returns the number of items in a table.

        :param table: DynamoDB table name.
        :return: Item count.
        :raise DynamoDBError: If count fails.
        """

        running_total = 0

        for _ in self.get_items(table):
            running_total += 1

        return running_total

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def get_item(
        self, table: str, partition_key_key: str, partition_key_value: PartitionKeyValue
    ) -> Optional[dict[str, AttributeValueDeserialized]]:
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

        partition_key = self._serializer.serialize_p_key(partition_key_key, partition_key_value)

        try:
            dynamodb_response = self._client.get_item(TableName=table, Key=partition_key)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        dynamodb_item = dynamodb_response.get('Item')

        if not dynamodb_item:
            return None

        # Convert the DynamoDB attribute values to deserialized values
        response = {
            key: self._serializer.deserialize_att(value) for key, value in dynamodb_item.items()
        }

        return response

    def put_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Optional[PartitionKeyValue] = None,
        auto_generate_partition_key_value: Optional[bool] = False,
        **items: AttributeValue,
    ) -> dict[str, AttributeValueDeserialized]:
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
            item_put = self._put_single_item(
                table=table,
                partition_key_key=partition_key_key,
                partition_key_value=partition_key_value,
                **items,
            )

        elif partition_key_value is None and auto_generate_partition_key_value is True:
            # If we need to increment the counter we do it with an
            # atomic write
            # Put new item
            put_in_db: list[dict[str, AttributeValue]] = [
                {
                    'TableName': table,
                    'PartitionKeyKey': partition_key_key,
                    'AutoGeneratePartitionKeyValue': True,
                    'Items': items,
                },
            ]

            atomic_write_response = self.atomic_writes(put=put_in_db)

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
    def update_item(
        self,
        table: str,
        partition_key: dict[str, PartitionKeyValue],
        condition_attribute: Optional[dict[str, Any]] = None,
        **items: AttributeValue,
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
                "No values to update were passed to the DynamoDB update_item_in_table method."
            )

        # Initialize a dictionary with all the arguments to pass into
        # the DynamoDB update_item call
        dynamodb_update_item_args: dict[str, Any] = {'TableName': table, 'ReturnValues': 'ALL_OLD'}

        # Serialize partition key
        # We cant mutate the original dictionary because of the
        # retry decorator will need to run through it again in case
        # of failure
        partition_key_key, partition_key_value = next(iter(partition_key.items()))
        partition_key_serialized = self._serializer.serialize_p_key(
            partition_key_key, partition_key_value
        )

        # Serialize attributes
        update_expression, expression_attribute_names, expression_attribute_values = (
            self._serializer.serialize_update_items(**items)
        )

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
                    f"#{condition_attribute_key} = :condition_attribute_value_placeholder"
                )
            })

            # #condition_attribute_key has to be passed
            # along the ExpressionAttributeNames because is used by the
            # ConditionExpression
            expression_attribute_names[f"#{condition_attribute_key}"] = condition_attribute_key

            # :condition_attribute_value_placeholder has to be passed
            # along the ExpressionAttributeValues because is used by the
            # ConditionExpression
            expression_attribute_values[':condition_attribute_value_placeholder'] = (
                self._serializer.serialize_att(condition_attribute_value)
            )

        # Update DynamoDB call arguments
        dynamodb_update_item_args['Key'] = partition_key_serialized
        dynamodb_update_item_args['UpdateExpression'] = update_expression
        dynamodb_update_item_args['ExpressionAttributeNames'] = expression_attribute_names
        dynamodb_update_item_args['ExpressionAttributeValues'] = expression_attribute_values

        module_logger.debug(dynamodb_update_item_args)

        try:
            dynamodb_response = self._client.update_item(**dynamodb_update_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(f"Conflict Detected! - {str(ex.response)}")

            else:
                raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        # If we get here it means that the item has been updated
        # successfully therefore we return it
        old_item = dynamodb_response.get('Attributes', {})
        old_item_deserialized = {
            key: self._serializer.deserialize_att(value) for key, value in old_item.items()
        }
        updated_item = {**partition_key, **old_item_deserialized, **items}

        return updated_item

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def delete_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Union[PartitionKeyValue, Iterable[PartitionKeyValue]],
    ):
        """
        Deletes item(s) in a table by primary key.

        If a single partition key value is provided, it deletes the
        corresponding item. If multiple partition key values are
        provided, it deletes all the corresponding items.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value or an iterable of values
            of the partition key of the item or items to delete from
            DynamoDB.
        :return: A list of responses from the deletion operations.
        :raise DynamoDBError: If deletion fails.
        """

        # Check if it's only one item to delete or many
        if isinstance(partition_key_value, (str, bytes, int, float)):
            partition_key_values = [partition_key_value]

        else:
            partition_key_values = list(partition_key_value)

        response = []

        for partition_key_value in partition_key_values:
            partition_key = self._serializer.serialize_p_key(partition_key_key, partition_key_value)

            try:
                dynamodb_response = self._client.delete_item(TableName=table, Key=partition_key)

            except botocore.exceptions.ClientError as ex:
                raise exceptions.DynamoDBError(str(ex.response))

            except Exception as ex:
                raise exceptions.DynamoDBError(str(ex))

            response.append(dynamodb_response)

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def delete_item_att(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: PartitionKeyValue,
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

        partition_key = self._serializer.serialize_p_key(partition_key_key, partition_key_value)

        attribute_updates: dict[str, type_defs.AttributeValueUpdateTypeDef] = {
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
                raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        return dynamodb_response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def atomic_writes(
        self,
        put: Optional[Iterable[dict[str, AttributeValue]]] = None,
        update: Optional[Iterable[dict[str, AttributeValue]]] = None,
        delete: Optional[Iterable[dict[str, AttributeValue]]] = None,
        condition_check: Optional[Iterable[dict[str, AttributeValue]]] = None,
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
            'PartitionKeyKey': "string of the PartitionKey key",
            'PartitionKeyValue': "OPTIONAL - partition key value",
            'AutoGeneratePartitionKeyValue': "OPTIONAL - bool",
            'Items': "dict containing all the items to put in DynamoDB",
            }
        :param update: Initiates an UpdateItem operation to update an
            existing item.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
            'Items': "dict containing all the values for items to be
            updated",
            'ConditionAttribute': "OPTIONAL - attribute to matched
            as dict of attribute_to_match {key: value}",
            }
        :param delete: Initiates a DeleteItem operation to delete an
            existing item.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
            }
        :param condition_check: Applies a condition to an item that is
            not being modified by the transaction. The condition must
            be satisfied for the transaction to succeed.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
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
        transact_items: list[type_defs.TransactWriteItemTypeDef] = []

        # Prepare the response object
        response: dict[str, list[dict[str, AttributeValue]]] = {
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
            el_put_serialized: type_defs.PutTypeDef = {
                'TableName': el['TableName'],
                'Item': self._serializer.serialize_put_items(
                    **{el['PartitionKeyKey']: partition_key_value, **el['Items']}
                ),
                'ConditionExpression': f"attribute_not_exists({el['PartitionKeyKey']})",
            }

            # Append the 'put' item to the DynamoDB atomic call
            transact_items.append({'Put': el_put_serialized})

            # Append the 'put' item to the return list
            response['Put'].append({
                key: self._serializer.deserialize_att(value)  # type: ignore
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
                updated_item: dict[str, Any] = {
                    key[1:-12]: self._serializer.deserialize_att(value)  # type: ignore
                    for key, value in counter_update_serialized['ExpressionAttributeValues'].items()
                }
                del updated_item['condition_attribute_value']
                p_key_k, p_key_v = self._serializer.deserialize_p_key(
                    counter_update_serialized['Key']  # type: ignore
                )
                updated_item[p_key_k] = p_key_v
                response['Update'].append(updated_item)

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
            assert isinstance(partition_key_value, (str, bytes, int, float))

            update_expression, expression_attribute_names, expression_attribute_values = (
                self._serializer.serialize_update_items(**el['Items'])
            )

            el_update_serialized: type_defs.UpdateTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serializer.serialize_p_key(partition_key_key, partition_key_value),
                'UpdateExpression': update_expression,
                'ExpressionAttributeNames': expression_attribute_names,
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
                        f"#{condition_att_key} = :condition_attribute_value_placeholder"
                    )
                })

                # #condition_att_key has to be passed
                # along the ExpressionAttributeNames because is used by
                # the ConditionExpression
                expression_attribute_names[f"#{condition_att_key}"] = condition_att_key

                # :condition_attribute_value_placeholder has to be
                # passed along the ExpressionAttributeValues because
                # is used by the ConditionExpression
                expression_attribute_values[':condition_attribute_value_placeholder'] = (
                    self._serializer.serialize_att(condition_att_value)
                )

            # Append the 'update' item to the DynamoDB atomic call
            transact_items.append({'Update': el_update_serialized})

            # Append the 'update' item to the return list
            updated_item = {
                key[1:-12]: self._serializer.deserialize_att(value)
                for key, value in expression_attribute_values.items()
            }
            if el.get('ConditionAttribute') is not None:
                del updated_item['condition_attribute_value']
            p_key_k, p_key_v = self._serializer.deserialize_p_key(
                el_update_serialized['Key'],  # type: ignore
            )
            updated_item[p_key_k] = p_key_v
            response['Update'].append(updated_item)

        # Normalize each delete item in the list for DynamoDB
        # transactional call
        for el in delete:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['PartitionKey'], MutableMapping)

            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            partition_key_key, partition_key_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(partition_key_value, (str, bytes, int, float))

            el_delete_serialized: type_defs.DeleteTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serializer.serialize_p_key(partition_key_key, partition_key_value),
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
            assert isinstance(partition_key_value, (str, bytes, int, float))

            el_condition_check_serialized: type_defs.ConditionCheckTypeDef = {
                'TableName': el['TableName'],
                'Key': self._serializer.serialize_p_key(partition_key_key, partition_key_value),
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
                raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        return response

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def put_atomic_counter(
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
        partition_key = self._serializer.serialize_p_key("pk_id", "__PK_VALUE_COUNTER__")

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
                raise exceptions.DynamoDBError(str(ex.response))

            except Exception as ex:
                raise exceptions.DynamoDBError(str(ex))

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        if not counter:
            self.put_item(
                table=sys_table,
                partition_key_key="pk_id",
                partition_key_value="__PK_VALUE_COUNTER__",
                current_counter_value=0,
                last_modified_timestamp=time.time_ns(),
            )

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def _put_single_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Optional[PartitionKeyValue] = None,
        **items: AttributeValue,
    ) -> dict[str, AttributeValueDeserialized]:
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

        assert isinstance(partition_key_value, (str, bytes, int, float))

        partition_key = self._serializer.serialize_p_key(partition_key_key, partition_key_value)
        additional_items = self._serializer.serialize_put_items(**items)
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
                raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        # If we get here it means that the item has been added
        # successfully therefore we return it
        item_put = {
            key: self._serializer.deserialize_att(value)
            for key, value in all_items_serialized.items()
        }

        return item_put

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
            item = self.get_item(
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
                f" '{self.put_atomic_counter.__name__}' to create one."
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
                    f" call '{self.put_atomic_counter.__name__}('{table}')' to create one."
                )

            else:
                raise

        return current_counter_value, last_modified_timestamp

    def _set_atomic_counter(
        self, table: str, counter_value: int, last_modified_timestamp: int
    ) -> type_defs.UpdateTypeDef:
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
        update_expression, expression_attribute_names, expression_attribute_values = (
            self._serializer.serialize_update_items(**{
                'current_counter_value': counter_value,
                'last_modified_timestamp': time.time_ns(),
            })
        )

        # :condition_attribute_value_placeholder has to be
        # passed along the ExpressionAttributeValues because
        # is used by the ConditionExpression
        expression_attribute_values[':condition_attribute_value_placeholder'] = (
            self._serializer.serialize_att(last_modified_timestamp)
        )

        el_update_serialized: type_defs.UpdateTypeDef = {
            'TableName': sys_table,
            'Key': self._serializer.serialize_p_key("pk_id", "__PK_VALUE_COUNTER__"),
            'UpdateExpression': update_expression,
            'ExpressionAttributeNames': expression_attribute_names,
            'ExpressionAttributeValues': expression_attribute_values,
            'ConditionExpression': (
                "#last_modified_timestamp = :condition_attribute_value_placeholder"
            ),
        }

        return el_update_serialized

    @utils.retry(exceptions.DynamoDBError, 3, 1)
    def _get_pk_type(self, table: str) -> Union[type[bytes], type[str], type[float]]:
        """
        Scan the table and return the type of the PartitionKeyItem Key.

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
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

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
            raise exceptions.DynamoDBError("PartitionKey Key Type not found")


class DynamoDbSerializer:
    """
    DynamoDbSerializer is a utility class for serializing and
    deserializing Python data types to DynamoDB compatible formats and
    vice versa.
    It provides methods for converting Python objects to DynamoDB
    attributes and for converting DynamoDB attributes back to Python
    objects.

    This class is useful for preparing data for storage in a DynamoDB
    table, and for reading data back into Python objects.
    """

    def __init__(self):
        self.string_utils = utils.StringUtils()

    def serialize_att(self, attribute_value: AttributeValue) -> type_defs.AttributeValueTypeDef:
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

        elif isinstance(attribute_value, (numbers.Real, decimal.Decimal)):
            return {"N": str(attribute_value)}

        elif isinstance(attribute_value, set):
            # Check the set contains at least one element
            try:
                set_el_sample = next(iter(attribute_value))

            except StopIteration:
                raise exceptions.DynamoDBError(
                    f"Object of type {type(attribute_value)!r} for {attribute_value!r} is not"
                    f" supported by DynamoDB serialization because {type(attribute_value)!r} empty."
                )

            # Check if set is homogeneous
            if not all(isinstance(el, type(set_el_sample)) for el in attribute_value):
                raise exceptions.DynamoDBError(
                    f"Object of type {type(attribute_value)!r} for {attribute_value!r} is not"
                    f" supported by DynamoDB serialization because {type(attribute_value)!r} must"
                    " be homogeneous."
                )

            if isinstance(set_el_sample, str):
                return {"SS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, bytes):
                return {"BS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, (numbers.Real, decimal.Decimal)):
                return {"NS": [str(el) for el in attribute_value]}

            else:
                raise exceptions.DynamoDBError(
                    f"Object of type {type(attribute_value)!r} for {attribute_value!r} is not"
                    f" supported by DynamoDB {type(attribute_value)!r}."
                    f" {type(attribute_value)!r} must be homogeneous of [str | bytes | int | float]"
                )

        elif isinstance(attribute_value, Sequence):
            list_value = list(attribute_value)
            for idx, el in enumerate(list_value):
                list_value[idx] = self.serialize_att(el)
            return {"L": list_value}

        elif isinstance(attribute_value, MutableMapping):
            dict_value = dict(attribute_value)
            for key, val in dict_value.items():
                dict_value[key] = self.serialize_att(val)
            return {"M": dict_value}

        else:
            raise exceptions.DynamoDBError(
                f"Object of type {type(attribute_value)!r} for {attribute_value!r} is not supported"
                " by DynamoDB serialization."
            )

    def deserialize_att(
        self,
        dynamodb_attribute: Union[type_defs.AttributeValueTypeDef, PartitionKeyTypeDef],
    ) -> AttributeValueDeserialized:
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
        # deserialization process. The unique ensures that the
        # sentinel is not accidentally found in `dynamodb_attribute`
        # dictionary values. Utilizing sentinel helps in distinguishing
        # between a None value and absence of a key. During the
        # deserialization, if the `.get()` method returns the sentinel,
        # it implies the key was not found in `dynamodb_attribute`;
        # otherwise, it returns the actual value (which might be None
        # or other falsy values) related to the looked-up key.
        sentinel = object()

        if dynamodb_attribute.get("NULL", sentinel) is not sentinel:
            return None

        elif dynamodb_attribute.get("BOOL", sentinel) is not sentinel:
            return bool(dynamodb_attribute["BOOL"])  # type: ignore

        elif dynamodb_attribute.get("S", sentinel) is not sentinel:
            return str(dynamodb_attribute["S"])

        elif dynamodb_attribute.get("B", sentinel) is not sentinel:
            return dynamodb_attribute["B"]

        elif dynamodb_attribute.get("N", sentinel) is not sentinel:
            if '.' in dynamodb_attribute["N"]:
                return float(dynamodb_attribute["N"])
            else:
                return int(dynamodb_attribute["N"])

        elif dynamodb_attribute.get("SS", sentinel) is not sentinel:
            return set(dynamodb_attribute["SS"])  # type: ignore

        elif dynamodb_attribute.get("BS", sentinel) is not sentinel:
            return set(dynamodb_attribute["BS"])  # type: ignore

        elif dynamodb_attribute.get("NS", sentinel) is not sentinel:
            if "." in dynamodb_attribute["NS"][0]:  # type: ignore
                return {float(el) for el in dynamodb_attribute["NS"]}  # type: ignore
            else:
                return {int(el) for el in dynamodb_attribute["NS"]}  # type: ignore

        elif dynamodb_attribute.get("L", sentinel) is not sentinel:
            return [self.deserialize_att(el) for el in dynamodb_attribute["L"]]  # type: ignore

        elif dynamodb_attribute.get("M", sentinel) is not sentinel:
            return {
                key: self.deserialize_att(val)
                for key, val in dynamodb_attribute["M"].items()  # type: ignore
            }

        else:
            raise exceptions.DynamoDBError(
                f"Object {dynamodb_attribute!r} of type {type(dynamodb_attribute)!r} is not"
                " supported for DynamoDB deserialization."
            )

    def serialize_p_key(
        self, partition_key_key: str, partition_key_value: PartitionKeyValue
    ) -> PartitionKeyItem:
        """
        Return a serialized DynamoDB partition key.

        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :return: Serialized partition key.
            i.e. {"id": {"S": "string"}}
        """

        partition_key_attribute = self.serialize_att(partition_key_value)
        partition_key: PartitionKeyItem = {partition_key_key: partition_key_attribute}

        return partition_key

    def deserialize_p_key(
        self, partition_key_serialized: PartitionKeyItem
    ) -> tuple[str, PartitionKeyValue]:
        """
        Deserialize a serialized DynamoDB partition key.

        :param partition_key_serialized: The serialized partition key.
            For example, {"id": {"S": "string"}}.
        :return: A tuple containing the partition key and its value.
        """

        partition_key_key, partition_key_value_serialized = next(
            iter(partition_key_serialized.items())
        )
        partition_key_value = self.deserialize_att(partition_key_value_serialized)
        assert isinstance(partition_key_value, (str, bytes, int, float))

        return partition_key_key, partition_key_value

    def serialize_put_items(self, **items: AttributeValue) -> Item:
        """
        Returns a dictionary of additional items with keys and values
        serialized for DynamoDB put_item call.

        :param items: Key-value pairs to serialize.
        :return: Items ready for put_item.
            i.e. {"col1": {"S": "value1"}, "col2": {"S": "value2"},
            "col3": {"S": "value3"}, ...}
        """

        additional_items: Item = {}

        for key, value in items.items():
            normalized_key = self.string_utils.snake_case(key)
            dynamodb_attribute = self.serialize_att(value)

            # Now add it to the additional_items serialized dictionary
            additional_items[normalized_key] = dynamodb_attribute

        return additional_items

    def serialize_update_items(self, **items: AttributeValue) -> tuple[str, dict[str, str], Item]:
        """
        Returns a tuple containing the UpdateExpression and the
        ExpressionAttributeValues ready to be passed to the DynamoDB
        update_item call.

        :param items: Key-value pairs to serialize.
        :return: A tuple with UpdateExpression, ExpressionAttributeNames
            and ExpressionAttributeValues.
        """

        update_expression = "SET "

        # In DynamoDB operations(such as UpdateItem, Query, or Scan),
        # you can use ExpressionAttributeNames to provide alternate
        # names for attributes in your expressions.This is most
        # commonly used to work around DynamoDB's reserved keywords or
        # to use attribute names that contain special characters not
        # allowed in expressions.
        expression_attribute_names: dict[str, str] = {}

        # In DynamoDB API, the ExpressionAttributeValues dictionary is
        # used to pass in placeholders for values that will be used in
        # your UpdateExpression and ConditionExpression. The keys for
        # these placeholders should start with a : and should not be
        # confused with actual column names.
        expression_attribute_values: Item = {}

        for key, value in items.items():
            normalized_key = self.string_utils.snake_case(key)
            dynamodb_attribute = self.serialize_att(value)

            # Add to the update_expression string
            update_expression += f"#{normalized_key} = :{normalized_key}_placeholder, "

            # Add to the expression_attribute_names dict
            expression_attribute_names[f"#{normalized_key}"] = normalized_key

            # Add to the expression_attribute_values serialized dict
            expression_attribute_values[f":{normalized_key}_placeholder"] = dynamodb_attribute

        # Removing the trailing ", " from the update_expression string
        update_expression = update_expression[:-2]

        return update_expression, expression_attribute_names, expression_attribute_values
