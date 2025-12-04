# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/database/database_dynamo.py
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
from typing import Any, Optional, TypedDict, Union

# Third Party Library Imports
import botocore.config
import botocore.exceptions
import mypy_boto3_dynamodb
from mypy_boto3_dynamodb import type_defs

# Local Folder (Relative) Imports
from .. import aws_boto3, exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'DynamoDB',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
DynamoDBClient = mypy_boto3_dynamodb.client.DynamoDBClient

# Placeholder, replace Any with AttributeValue later
DynamoDbList = Sequence[Any]
DynamoDbListDeserialized = Sequence[Any]
DynamoDbMap = Mapping[str, Any]
DynamoDbMapDeserialized = Mapping[str, Any]

PartitionKeyValue = Union[bytes, str, float]
SortKeyValue = Union[bytes, str, float]

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


class DynamoDB(aws_boto3.aws_service_base.AwsServiceBase[DynamoDBClient]):
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
        super().__init__(
            aws_region_name=aws_region_name,
            aws_profile_name=aws_profile_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            caching=caching,
            client_parameters=client_parameters,
            aws_service_name="dynamodb",
            exception_type=exceptions.DynamoDBError,
        )
        self._serializer = DynamoDbSerializer()

    @utils.retry(exception_to_check=exceptions.DynamoDBError, delay_secs=1)
    def get_tables(self) -> list[str]:
        """
        Returns an array of table names associated with the current
        account and endpoint.

        :return: List of table names.
        :raise DynamoDBError: If listing fails.
        """

        try:
            ddb_response = self._client.list_tables()

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        # If TableNames is not present then return an empty list
        try:
            response = ddb_response['TableNames']

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

        ddb_scan_args: type_defs.ScanInputTypeDef = {'TableName': table}

        try:
            while True:
                try:
                    with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                        ddb_response = retryer(self._client.scan, **ddb_scan_args)

                except botocore.exceptions.ClientError as ex:
                    raise exceptions.DynamoDBError(str(ex.response))

                except Exception as ex:
                    raise exceptions.DynamoDBError(str(ex))

                if ddb_response.get('Items') and len(ddb_response['Items']) > 0:
                    # Convert the DynamoDB attribute values to
                    # deserialized values
                    deser_items = (
                        {
                            key: self._serializer.deserialize_att(value)
                            for key, value in ddb_item.items()
                        }
                        for ddb_item in ddb_response['Items']
                    )

                    yield from deser_items

                else:
                    # Nothing to yield
                    yield from ()

                # If LastEvaluatedKey is present then we need to scan
                # for more items
                if ddb_response.get('LastEvaluatedKey'):
                    ddb_scan_args['ExclusiveStartKey'] = ddb_response['LastEvaluatedKey']

                # If no LastEvaluatedKey then break out of the while
                # loop as we're done
                else:
                    break

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

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

    def get_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: PartitionKeyValue,
        sort_key_key: Optional[str] = None,
        sort_key_value: Optional[SortKeyValue] = None,
    ) -> Optional[dict[str, AttributeValueDeserialized]]:
        """
        The get_item_from_table operation returns a dictionary of
        deserialized attribute values for the item with the given
        primary key. If there is no matching item, get_item_from_table
        returns None.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.:
        :param sort_key_key: The key of the sort key.
        :param sort_key_value: The value of the sort key.
        :return: Deserialized item or None.
        :raise DynamoDBError: If retrieval fails.
        """

        pk = self._serializer.serialize_p_key(
            pk_key=partition_key_key,
            pk_value=partition_key_value,
            sk_key=sort_key_key,
            sk_value=sort_key_value,
        )

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                ddb_response = retryer(self._client.get_item, TableName=table, Key=pk)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        ddb_item = ddb_response.get('Item')

        if not ddb_item:
            return None

        # Convert the DynamoDB attribute values to deserialized values
        response = {key: self._serializer.deserialize_att(value) for key, value in ddb_item.items()}

        return response

    def put_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Optional[PartitionKeyValue] = None,
        sort_key_key: Optional[str] = None,
        sort_key_value: Optional[SortKeyValue] = None,
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
        :param sort_key_key: The key of the sort key.
        :param sort_key_value: The value of the sort key.
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
            try:
                item_put = self._put_single_item(
                    table=table,
                    partition_key_key=partition_key_key,
                    partition_key_value=partition_key_value,
                    sort_key_key=sort_key_key,
                    sort_key_value=sort_key_value,
                    **items,
                )

            except Exception as ex:
                raise exceptions.DynamoDBError(str(ex)) from None

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

    def update_item(
        self,
        table: str,
        partition_key: dict[str, PartitionKeyValue],
        sort_key: Optional[dict[str, SortKeyValue]] = None,
        condition_attribute: Optional[dict[str, Any]] = None,
        **items: AttributeValue,
    ) -> dict[str, AttributeValueDeserialized]:
        """
        Performs a strict update on an existing item in DynamoDB.

        This method enforces that the item with the specified partition
        key must already exist before updating. If the item does not
        exist, or if any specified condition does not match, the update
        fails with a `DynamoDBConflictError`. No new item is created in
        this scenario.

        Edits an existing item’s attributes. If
        condition_attribute_value is passed, the item will be updated
        only if condition_attribute_value is a match with the value
        stored in DynamoDB.

        :param table: DynamoDB table name.
        :param partition_key: DynamoDB partition key as dict of
            partition_key {key: value}.
        :param sort_key: DynamoDB sort key as dict of sort_key
            {key: value}.
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
        ddb_update_item_args: dict[str, Any] = {
            'TableName': table,
            'ReturnValues': 'ALL_OLD',
        }

        # Serialize partition key
        pk_key, pk_value = next(iter(partition_key.items()))
        sk_key, sk_value = next(iter(sort_key.items())) if sort_key is not None else (None, None)

        pk_ser = self._serializer.serialize_p_key(
            pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
        )

        # Serialize attributes
        exp, exp_att_names, exp_att_values = self._serializer.serialize_update_items(**items)

        # Build a condition expression for “strict update”
        ddb_update_item_args.update({'ConditionExpression': f"attribute_exists(#{pk_key})"})
        exp_att_names.update({f"#{pk_key}": pk_key})

        # Check if a condition is required
        if condition_attribute is not None:
            # Unpack condition attribute dictionary
            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            cond_att_key, cond_att_value = next(iter(condition_attribute.items()))

            # If condition attribute exists pass it to the DynamoDB call
            ddb_update_item_args.update({
                'ConditionExpression': (
                    f"{ddb_update_item_args['ConditionExpression']} AND"
                    f" #{cond_att_key} = :condition_attribute_value_placeholder"
                )
            })

            # #condition_attribute_key has to be passed
            # along the ExpressionAttributeNames because is used by the
            # ConditionExpression
            exp_att_names[f"#{cond_att_key}"] = cond_att_key

            # :condition_attribute_value_placeholder has to be passed
            # along the ExpressionAttributeValues because is used by the
            # ConditionExpression
            exp_att_values[':condition_attribute_value_placeholder'] = (
                self._serializer.serialize_att(cond_att_value)
            )

        # Update DynamoDB call arguments
        ddb_update_item_args['Key'] = pk_ser
        ddb_update_item_args['UpdateExpression'] = exp
        ddb_update_item_args['ExpressionAttributeNames'] = exp_att_names
        ddb_update_item_args['ExpressionAttributeValues'] = exp_att_values

        module_logger.debug(ddb_update_item_args)

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                ddb_response = retryer(self._client.update_item, **ddb_update_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(str(ex.response)) from None
            else:
                raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        # If we get here it means that the item has been updated
        # successfully therefore we return it
        item = ddb_response.get('Attributes', {})
        item_deser = {key: self._serializer.deserialize_att(value) for key, value in item.items()}
        pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
        updated_item = {**item_deser, **items, **{pk_key: pk_value}}
        if sk_key is not None:
            updated_item.update({sk_key: sk_value})

        # Because the **items in the updated_item dict is not serialized
        # we need to normalize the whole dict before returning a dict of
        # type dict[str, AttributeValueDeserialized]
        updated_item_deser = self._serializer.normalize_item(updated_item)

        return updated_item_deser

    def upsert_item(
        self,
        table: str,
        partition_key: dict[str, PartitionKeyValue],
        sort_key: Optional[dict[str, SortKeyValue]] = None,
        condition_attribute: Optional[dict[str, Any]] = None,
        **items: AttributeValue,
    ) -> dict[str, AttributeValueDeserialized]:
        """
        Upsert-like operation.

        1. Tries to update an existing item (strict update).
        2. If that update fails because the item does not exist, it
            puts a brand-new item.

        :param table: DynamoDB table name.
        :param partition_key: DynamoDB partition key as dict of
            partition_key {key: value}.
        :param sort_key: DynamoDB sort key as dict of sort_key
            {key: value}.
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
        ddb_update_item_args: dict[str, Any] = {
            'TableName': table,
            'ReturnValues': 'ALL_OLD',
        }

        # Serialize partition key
        pk_key, pk_value = next(iter(partition_key.items()))
        sk_key, sk_value = next(iter(sort_key.items())) if sort_key is not None else (None, None)

        pk_ser = self._serializer.serialize_p_key(
            pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
        )

        # Serialize attributes
        exp, exp_att_names, exp_att_values = self._serializer.serialize_update_items(**items)

        # Check if a condition is required
        if condition_attribute is not None:
            # Unpack condition attribute dictionary
            # We cant mutate the original dictionary because of the
            # retry decorator will need to run through it again in case
            # of failure
            cond_att_key, cond_att_value = next(iter(condition_attribute.items()))

            # If condition attribute exists pass it to the DynamoDB call
            ddb_update_item_args.update(
                {'ConditionExpression': f"#{cond_att_key} = :condition_attribute_value_placeholder"}
            )

            # #condition_attribute_key has to be passed
            # along the ExpressionAttributeNames because is used by the
            # ConditionExpression
            exp_att_names[f"#{cond_att_key}"] = cond_att_key

            # :condition_attribute_value_placeholder has to be passed
            # along the ExpressionAttributeValues because is used by the
            # ConditionExpression
            exp_att_values[':condition_attribute_value_placeholder'] = (
                self._serializer.serialize_att(cond_att_value)
            )

        # Update DynamoDB call arguments
        ddb_update_item_args['Key'] = pk_ser
        ddb_update_item_args['UpdateExpression'] = exp
        ddb_update_item_args['ExpressionAttributeNames'] = exp_att_names
        ddb_update_item_args['ExpressionAttributeValues'] = exp_att_values

        module_logger.debug(ddb_update_item_args)

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                ddb_response = retryer(self._client.update_item, **ddb_update_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(str(ex.response)) from None
            else:
                raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        # If we get here it means that the item has been updated
        # successfully therefore we return it
        item = ddb_response.get('Attributes', {})
        item_deser = {key: self._serializer.deserialize_att(value) for key, value in item.items()}
        pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
        updated_item = {**item_deser, **items, **{pk_key: pk_value}}
        if sk_key is not None:
            updated_item.update({sk_key: sk_value})

        # Because the **items in the updated_item dict is not serialized
        # we need to normalize the whole dict before returning a dict of
        # type dict[str, AttributeValueDeserialized]
        updated_item_deser = self._serializer.normalize_item(updated_item)

        return updated_item_deser

    def delete_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: Union[PartitionKeyValue, Iterable[PartitionKeyValue]],
        sort_key_key: Optional[str] = None,
        sort_key_value: Optional[Union[SortKeyValue, Iterable[SortKeyValue]]] = None,
    ) -> list[dict[str, AttributeValueDeserialized]]:
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
        :param sort_key_key: The key of the sort key.
        :param sort_key_value: The value or an iterable of values
            of the sort key of the item or items to delete from
            DynamoDB.
        :return: A list of deleted DynamoDB Items deserialized.
        :raise DynamoDBError: If deletion fails.
        """

        if (sort_key_key is None) ^ (sort_key_value is None):
            raise exceptions.DynamoDBError(
                "Both sort_key_key and sort_key_value must be provided or both must be None."
            )
        has_sk = sort_key_key is not None and sort_key_value is not None

        # Check if it's only one item to delete or many
        pk_values: list[PartitionKeyValue] = []
        if isinstance(partition_key_value, (str, bytes, int, float)):
            pk_values.append(partition_key_value)
        else:
            pk_values.extend(partition_key_value)

        sk_values: list[Optional[SortKeyValue]] = []
        if has_sk:
            assert sort_key_value is not None
            if isinstance(sort_key_value, (str, bytes, int, float)):
                sk_values.append(sort_key_value)
            else:
                sk_values.extend(sort_key_value)
        else:
            sk_values.extend([None] * len(pk_values))

        if len(pk_values) != len(sk_values):
            raise exceptions.DynamoDBError(
                "The number of partition key values and sort key values must be the same."
            )

        # Prepare response list
        response: list[dict[str, AttributeValueDeserialized]] = []

        for pk_val, sk_val in zip(pk_values, sk_values):
            pk_ser = self._serializer.serialize_p_key(
                pk_key=partition_key_key, pk_value=pk_val, sk_key=sort_key_key, sk_value=sk_val
            )

            # Initialize a dictionary with all the arguments to pass
            # into the DynamoDB delete_item call
            ddb_delete_item_args: dict[str, Any] = {
                'TableName': table,
                'Key': pk_ser,
                'ReturnValues': 'ALL_OLD',
            }

            try:
                with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                    ddb_response = retryer(self._client.delete_item, **ddb_delete_item_args)

            except botocore.exceptions.ClientError as ex:
                raise exceptions.DynamoDBError(str(ex.response)) from None

            except Exception as ex:
                raise exceptions.DynamoDBError(str(ex)) from None

            # If we get here it means that the item has been deleted
            # successfully therefore we return it
            item = ddb_response.get('Attributes', {})
            item_deser = {
                key: self._serializer.deserialize_att(value) for key, value in item.items()
            }
            pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
            deleted_item = {**item_deser, **{pk_key: pk_value}}
            if sk_key is not None:
                deleted_item.update({sk_key: sk_value})

            response.append(deleted_item)

        return response

    def delete_item_att(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: PartitionKeyValue,
        attributes_to_delete: Iterable[str],
        sort_key_key: Optional[str] = None,
        sort_key_value: Optional[SortKeyValue] = None,
    ) -> dict[str, AttributeValueDeserialized]:
        """
        Deletes item specific values in a table by primary key.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :param sort_key_key: The key of the sort key.
        :param sort_key_value: The value of the sort key.
        :param attributes_to_delete: An iterable of specific attributes
            that are to be deleted from DynamoDB.
        :return: The updated DynamoDB Item deserialized.
        :raise DynamoDBError: If deletion fails.
        """

        pk_ser = self._serializer.serialize_p_key(
            pk_key=partition_key_key,
            pk_value=partition_key_value,
            sk_key=sort_key_key,
            sk_value=sort_key_value,
        )

        att_updates: dict[str, type_defs.AttributeValueUpdateTypeDef] = {
            item_value: {'Action': "DELETE"} for item_value in attributes_to_delete
        }

        ddb_update_item_args: dict[str, Any] = {
            'TableName': table,
            'Key': pk_ser,
            'AttributeUpdates': att_updates,
            'ReturnValues': 'ALL_NEW',
        }

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                ddb_response = retryer(self._client.update_item, **ddb_update_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(str(ex.response)) from None
            else:
                raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        # If we get here it means that the item has been updated
        # successfully therefore we return it
        item = ddb_response.get('Attributes', {})
        item_deser = {key: self._serializer.deserialize_att(value) for key, value in item.items()}

        return item_deser

    def atomic_writes(
        self,
        put: Optional[Iterable[dict[str, AttributeValue]]] = None,
        update: Optional[Iterable[dict[str, AttributeValue]]] = None,
        upsert: Optional[Iterable[dict[str, AttributeValue]]] = None,
        delete: Optional[Iterable[dict[str, AttributeValue]]] = None,
        condition_check: Optional[Iterable[dict[str, AttributeValue]]] = None,
        **kwargs,
    ) -> dict[str, list[dict[str, AttributeValueDeserialized]]]:
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
            'SortKeyKey': "OPTIONAL - string of the SortKey key",
            'SortKeyValue': "OPTIONAL - sort key value",
            'AutoGeneratePartitionKeyValue': "OPTIONAL - bool",
            'Items': "dict containing all the items to put in DynamoDB",
            }
        :param update: Initiates an UpdateItem operation to update an
            existing item.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
            'SortKey': "OPTIONAL - The sort key as dict of sort_key
            {key: value}",
            'Items': "dict containing all the values for items to be
            updated",
            'ConditionAttribute': "OPTIONAL - attribute to matched
            as dict of attribute_to_match {key: value}",
            }
        :param upsert: Initiates an UpdateOrInsertItem operation to
            update an existing item or insert if not in the table.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
            'SortKey': "OPTIONAL - The sort key as dict of sort_key
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
            'SortKey': "OPTIONAL - The sort key as dict of sort_key
            {key: value}",
            }
        :param condition_check: Applies a condition to an item that is
            not being modified by the transaction. The condition must
            be satisfied for the transaction to succeed.
            schema = {
            'TableName': "string DynamoDB Table Name",
            'PartitionKey': "The partition key as dict of partition_key
            {key: value}",
            'SortKey': "OPTIONAL - The sort key as dict of sort_key
            {key: value}",
            }
        :return: A dictionary with keys
            'Put', 'Update', 'Delete', 'ConditionCheck',
            and a list of items writes to the DynamoDB in the same
            order as they were passed in.
            schema = {
            'Put': "list of items writes to DynamoDB",
            'Update': "list of items writes to DynamoDB",
            'Upsert': "list of items writes to DynamoDB",
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
        upsert = upsert or {}
        delete = delete or {}
        condition_check = condition_check or {}

        # Prepare the list of transactional items to be passed to the
        # DynamoDB call
        transact_items: list[type_defs.TransactWriteItemTypeDef] = []

        # Prepare the response object
        response: dict[str, list[dict[str, AttributeValueDeserialized]]] = {
            'Put': [],
            'Update': [],
            'Upsert': [],
            'Delete': [],
            'ConditionCheck': [],
        }

        module_logger.debug(
            f"Atomic Writes in Table initial request - Put: {put}, Update: {update}, Delete:"
            f" {delete}, ConditionCheck: {condition_check}"
        )

        transact_items, response = self._atomic_writes_put(
            put=put,
            transact_items=transact_items,
            response=response,
        )

        transact_items, response = self._atomic_writes_update(
            update=update,
            transact_items=transact_items,
            response=response,
        )

        transact_items, response = self._atomic_writes_upsert(
            upsert=upsert,
            transact_items=transact_items,
            response=response,
        )

        transact_items, response = self._atomic_writes_delete(
            delete=delete,
            transact_items=transact_items,
            response=response,
        )

        transact_items, response = self._atomic_writes_condition_check(
            condition_check=condition_check,
            transact_items=transact_items,
            response=response,
        )

        module_logger.debug(f"Atomic Writes in Table serialized request - {transact_items}")

        # Make the DynamoDB atomic api call
        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                retryer(self._client.transact_write_items, TransactItems=transact_items, **kwargs)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(str(ex.response)) from None
            else:
                raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        return response

    def _atomic_writes_put(
        self,
        put: Iterable[dict[str, AttributeValue]],
        transact_items: list[type_defs.TransactWriteItemTypeDef],
        response: dict[str, list[dict[str, AttributeValueDeserialized]]],
    ) -> tuple[
        list[type_defs.TransactWriteItemTypeDef],
        dict[str, list[dict[str, AttributeValueDeserialized]]],
    ]:
        """
        A helper method to prepare the atomic writes for put items.

        :param put: A list of put items.
        :param transact_items:
        :param response:
        :return:
        """

        # Normalize each put item in the list for DynamoDB
        # transactional call
        for el in put:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['Items'], Mapping)
            assert isinstance(el['PartitionKeyKey'], str)

            pk_value = el.get('PartitionKeyValue')
            ag_pk_value = el.get('AutoGeneratePartitionKeyValue', False)

            if pk_value is not None and ag_pk_value is True:
                raise exceptions.DynamoDBError(
                    "If AutoGeneratePartitionKeyValue is enabled, a PartitionKeyValue MUST NOT be"
                    " passed in."
                )

            elif pk_value is not None and ag_pk_value is False:
                # This is the case where we use el['PartitionKeyValue']
                # as 'PartitionKeyValue'
                pass

            elif pk_value is None and ag_pk_value is True:
                # This is the case where we auto generate the
                # PartitionKeyValue
                cur_counter, last_mod_timestamp = self._get_atomic_counter(table=el['TableName'])
                new_counter = cur_counter + 1

                # Check what is the type of the PartitionKey key of
                # the table
                pk_type = self._get_pk_type(table=el['TableName'])

                if issubclass(pk_type, str):
                    auto_generate_pk_value: PartitionKeyValue = str(new_counter)

                elif issubclass(pk_type, bytes):
                    auto_generate_pk_value = str(new_counter).encode()

                elif issubclass(pk_type, float):
                    auto_generate_pk_value = new_counter

            elif pk_value is None and ag_pk_value is False:
                raise exceptions.DynamoDBError(
                    "If AutoGeneratePartitionKeyValue is disabled, a PartitionKeyValue MUST be"
                    " passed in."
                )

            else:
                raise exceptions.DynamoDBError(
                    "Unable to determine a valid operation with the provided PartitionKeyValue and"
                    " AutoGeneratePartitionKeyValue."
                )

            pk_value_resolved = el.get('PartitionKeyValue') or auto_generate_pk_value
            assert isinstance(pk_value_resolved, (str, bytes, int, float))
            pk: dict[str, PartitionKeyValue] = {el['PartitionKeyKey']: pk_value_resolved}

            if (el.get('SortKeyKey') is None) ^ (el.get('SortKeyValue') is None):
                raise exceptions.DynamoDBError(
                    "Both SortKeyKey and SortKeyValue must be provided or both must be None."
                )
            has_sk = el.get('SortKeyKey') is not None and el.get('SortKeyValue') is not None

            sk: dict[str, PartitionKeyValue] = {}
            if has_sk:
                sk_key = el['SortKeyKey']
                sk_value = el['SortKeyValue']
                assert isinstance(sk_key, str)
                assert isinstance(sk_value, (str, bytes, int, float))
                sk = {sk_key: sk_value}

            # If we don't need to increment the counter we just put the
            # item in the table
            el_put_ser: type_defs.PutTypeDef = {
                'TableName': el['TableName'],
                'Item': self._serializer.serialize_put_items(**pk, **sk, **el['Items']),
                'ConditionExpression': f"attribute_not_exists({el['PartitionKeyKey']})",
            }

            # Append the 'put' item to the DynamoDB atomic call
            transact_items.append({'Put': el_put_ser})

            # Append the 'put' item to the return list
            response['Put'].append({
                key: self._serializer.deserialize_att(value)  # type: ignore
                for key, value in el_put_ser['Item'].items()
            })

            # If we need to increment the counter we update the counter
            if ag_pk_value:
                # Update the counter
                counter_update_ser = self._set_atomic_counter(
                    table=el['TableName'],
                    counter_value=new_counter,
                    last_modified_timestamp=last_mod_timestamp,
                )

                # Append the 'update' item to the DynamoDB atomic call
                transact_items.append({'Update': counter_update_ser})

                # Append the 'update' item to the return list
                updated_item: dict[str, Any] = {
                    key[1:-12]: self._serializer.deserialize_att(value)  # type: ignore
                    for key, value in counter_update_ser['ExpressionAttributeValues'].items()
                }
                del updated_item['condition_attribute_value']
                # Ignoring sk because _set_atomic_counter is not
                # using it
                p_key_k, p_key_v, *_ = self._serializer.deserialize_p_key(
                    counter_update_ser['Key']  # type: ignore
                )
                updated_item[p_key_k] = p_key_v
                response['Update'].append(updated_item)

        return transact_items, response

    def _atomic_writes_update(
        self,
        update: Iterable[dict[str, AttributeValue]],
        transact_items: list[type_defs.TransactWriteItemTypeDef],
        response: dict[str, list[dict[str, AttributeValueDeserialized]]],
    ) -> tuple[
        list[type_defs.TransactWriteItemTypeDef],
        dict[str, list[dict[str, AttributeValueDeserialized]]],
    ]:
        # Normalize each update item in the list for DynamoDB
        # transactional call
        for el in update:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['Items'], Mapping)
            assert isinstance(el['PartitionKey'], MutableMapping)

            pk_key, pk_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(pk_value, (str, bytes, int, float))

            # Check if a sort_key is passed in
            if el.get('SortKey') is not None:
                # Unpack sort_key attribute dictionary
                assert isinstance(el['SortKey'], MutableMapping)
                sk_key, sk_value = next(iter(el['SortKey'].items()))
                assert isinstance(sk_value, (str, bytes, int, float))
            else:
                sk_key, sk_value = (None, None)

            pk_ser = self._serializer.serialize_p_key(
                pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
            )

            exp, exp_att_names, exp_att_values = self._serializer.serialize_update_items(
                **el['Items']
            )

            # Build a condition expression for “strict update”
            cond_exp = f"attribute_exists(#{pk_key})"
            exp_att_names.update({f"#{pk_key}": pk_key})

            el_update_ser: type_defs.UpdateTypeDef = {
                'TableName': el['TableName'],
                'Key': pk_ser,
                'ConditionExpression': cond_exp,
                'UpdateExpression': exp,
                'ExpressionAttributeNames': exp_att_names,
                'ExpressionAttributeValues': exp_att_values,
            }

            # Check if a condition is passed in
            if el.get('ConditionAttribute') is not None:
                # Unpack condition attribute dictionary
                assert isinstance(el['ConditionAttribute'], MutableMapping)
                # We cant mutate the original dictionary because of the
                # retry decorator will need to run through it again in
                # case of failure
                cond_att_key, cond_att_value = next(iter(el['ConditionAttribute'].items()))

                # If condition attribute exists pass it to the DynamoDB
                # call
                el_update_ser.update({
                    'ConditionExpression': (
                        f"{el_update_ser['ConditionExpression']} AND"
                        f" #{cond_att_key} = :condition_attribute_value_placeholder"
                    )
                })

                # #condition_att_key has to be passed
                # along the ExpressionAttributeNames because is used by
                # the ConditionExpression
                exp_att_names[f"#{cond_att_key}"] = cond_att_key

                # :condition_attribute_value_placeholder has to be
                # passed along the ExpressionAttributeValues because
                # is used by the ConditionExpression
                exp_att_values[':condition_attribute_value_placeholder'] = (
                    self._serializer.serialize_att(cond_att_value)
                )

            # Append the 'update' item to the DynamoDB atomic call
            transact_items.append({'Update': el_update_ser})

            # Append the 'update' item to the return list
            updated_item = {
                key[1:-12]: self._serializer.deserialize_att(value)
                for key, value in exp_att_values.items()
            }
            if el.get('ConditionAttribute') is not None:
                del updated_item['condition_attribute_value']
            pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
            updated_item[pk_key] = pk_value
            if sk_key is not None:
                updated_item[sk_key] = sk_value
            response['Update'].append(updated_item)

        return transact_items, response

    def _atomic_writes_upsert(
        self,
        upsert: Iterable[dict[str, AttributeValue]],
        transact_items: list[type_defs.TransactWriteItemTypeDef],
        response: dict[str, list[dict[str, AttributeValueDeserialized]]],
    ) -> tuple[
        list[type_defs.TransactWriteItemTypeDef],
        dict[str, list[dict[str, AttributeValueDeserialized]]],
    ]:
        # Normalize each upsert item in the list for DynamoDB
        # transactional call
        for el in upsert:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['Items'], Mapping)
            assert isinstance(el['PartitionKey'], MutableMapping)

            pk_key, pk_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(pk_value, (str, bytes, int, float))

            # Check if a sort_key is passed in
            if el.get('SortKey') is not None:
                # Unpack sort_key attribute dictionary
                assert isinstance(el['SortKey'], MutableMapping)
                sk_key, sk_value = next(iter(el['SortKey'].items()))
                assert isinstance(sk_value, (str, bytes, int, float))
            else:
                sk_key, sk_value = (None, None)

            pk_ser = self._serializer.serialize_p_key(
                pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
            )

            exp, exp_att_names, exp_att_values = self._serializer.serialize_update_items(
                **el['Items']
            )

            el_upsert_ser: type_defs.UpdateTypeDef = {
                'TableName': el['TableName'],
                'Key': pk_ser,
                'UpdateExpression': exp,
                'ExpressionAttributeNames': exp_att_names,
                'ExpressionAttributeValues': exp_att_values,
            }

            # Check if a condition is passed in
            if el.get('ConditionAttribute') is not None:
                # Unpack condition attribute dictionary
                assert isinstance(el['ConditionAttribute'], MutableMapping)
                # We cant mutate the original dictionary because of the
                # retry decorator will need to run through it again in
                # case of failure
                cond_att_key, cond_att_value = next(iter(el['ConditionAttribute'].items()))

                # If condition attribute exists pass it to the DynamoDB
                # call
                el_upsert_ser.update({
                    'ConditionExpression': (
                        f"#{cond_att_key} = :condition_attribute_value_placeholder"
                    )
                })

                # #condition_att_key has to be passed
                # along the ExpressionAttributeNames because is used by
                # the ConditionExpression
                exp_att_names[f"#{cond_att_key}"] = cond_att_key

                # :condition_attribute_value_placeholder has to be
                # passed along the ExpressionAttributeValues because
                # is used by the ConditionExpression
                exp_att_values[':condition_attribute_value_placeholder'] = (
                    self._serializer.serialize_att(cond_att_value)
                )

            # Append the 'update' item to the DynamoDB atomic call
            transact_items.append({'Update': el_upsert_ser})

            # Append the 'upsert' item to the return list
            upsert_item = {
                key[1:-12]: self._serializer.deserialize_att(value)
                for key, value in exp_att_values.items()
            }
            if el.get('ConditionAttribute') is not None:
                del upsert_item['condition_attribute_value']
            pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
            upsert_item[pk_key] = pk_value
            if sk_key is not None:
                upsert_item[sk_key] = sk_value
            response['Upsert'].append(upsert_item)

        return transact_items, response

    def _atomic_writes_delete(
        self,
        delete: Iterable[dict[str, AttributeValue]],
        transact_items: list[type_defs.TransactWriteItemTypeDef],
        response: dict[str, list[dict[str, AttributeValueDeserialized]]],
    ) -> tuple[
        list[type_defs.TransactWriteItemTypeDef],
        dict[str, list[dict[str, AttributeValueDeserialized]]],
    ]:
        # Normalize each delete item in the list for DynamoDB
        # transactional call
        for el in delete:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['PartitionKey'], MutableMapping)

            pk_key, pk_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(pk_value, (str, bytes, int, float))

            # Check if a sort_key is passed in
            if el.get('SortKey') is not None:
                # Unpack sort_key attribute dictionary
                assert isinstance(el['SortKey'], MutableMapping)
                sk_key, sk_value = next(iter(el['SortKey'].items()))
                assert isinstance(sk_value, (str, bytes, int, float))
            else:
                sk_key, sk_value = (None, None)

            pk_ser = self._serializer.serialize_p_key(
                pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
            )

            el_delete_ser: type_defs.DeleteTypeDef = {
                'TableName': el['TableName'],
                'Key': pk_ser,
            }

            # Append the 'delete' item to the DynamoDB atomic call
            transact_items.append({'Delete': el_delete_ser})

            # Append the 'delete' item to the return list
            deleted_item: dict[str, AttributeValueDeserialized] = {}
            pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
            deleted_item[pk_key] = pk_value
            if sk_key is not None:
                deleted_item[sk_key] = sk_value
            response['Delete'].append(deleted_item)

        return transact_items, response

    def _atomic_writes_condition_check(
        self,
        condition_check: Iterable[dict[str, AttributeValue]],
        transact_items: list[type_defs.TransactWriteItemTypeDef],
        response: dict[str, list[dict[str, AttributeValueDeserialized]]],
    ) -> tuple[
        list[type_defs.TransactWriteItemTypeDef],
        dict[str, list[dict[str, AttributeValueDeserialized]]],
    ]:
        # Normalize each conditional check item in the list for DynamoDB
        # transactional call
        for el in condition_check:
            assert isinstance(el['TableName'], str)
            assert isinstance(el['PartitionKey'], MutableMapping)

            pk_key, pk_value = next(iter(el['PartitionKey'].items()))
            assert isinstance(pk_value, (str, bytes, int, float))

            # Check if a sort_key is passed in
            if el.get('SortKey') is not None:
                # Unpack sort_key attribute dictionary
                assert isinstance(el['SortKey'], MutableMapping)
                sk_key, sk_value = next(iter(el['SortKey'].items()))
                assert isinstance(sk_value, (str, bytes, int, float))
            else:
                sk_key, sk_value = (None, None)

            pk_ser = self._serializer.serialize_p_key(
                pk_key=pk_key, pk_value=pk_value, sk_key=sk_key, sk_value=sk_value
            )

            el_cond_check_ser: type_defs.ConditionCheckTypeDef = {
                'TableName': el['TableName'],
                'Key': pk_ser,
                # TODO(carlogtt): not sure how to use the below yet
                'ConditionExpression': 'string',
                'ExpressionAttributeNames': {'string': 'string'},
                'ExpressionAttributeValues': {},
            }

            # Append the 'condition_check' item to the DynamoDB atomic
            # call
            transact_items.append({'ConditionCheck': el_cond_check_ser})

            # Append the 'condition_check' item to the return list
            cond_check_item: dict[str, AttributeValueDeserialized] = {}
            pk_key, pk_value, sk_key, sk_value = self._serializer.deserialize_p_key(pk_ser)
            cond_check_item[pk_key] = pk_value
            if sk_key is not None:
                cond_check_item[sk_key] = sk_value
            response['ConditionCheck'].append(cond_check_item)

        return transact_items, response

    @utils.retry(exception_to_check=exceptions.DynamoDBError, delay_secs=1)
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
        pk_ser = self._serializer.serialize_p_key(pk_key="pk_id", pk_value="__PK_VALUE_COUNTER__")

        try:
            ddb_response = self._client.get_item(TableName=sys_table, Key=pk_ser)
            counter = ddb_response.get('Item')

        except self._client.exceptions.ResourceNotFoundException:
            module_logger.debug(f"Table: {sys_table} not found in DynamoDB, Creating it.")

            # Initialize a dictionary with all the arguments to pass
            # into the DynamoDB put_item call
            ddb_create_table_args: dict[str, Any] = {
                'TableName': sys_table,
                'BillingMode': 'PAY_PER_REQUEST',
                'AttributeDefinitions': [{
                    'AttributeName': 'pk_id',
                    'AttributeType': 'S',
                }],
                'KeySchema': [{
                    'AttributeName': 'pk_id',
                    'KeyType': 'HASH',
                }],
                'DeletionProtectionEnabled': True,
            }

            try:
                self._client.create_table(**ddb_create_table_args)

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
            raise exceptions.DynamoDBError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex)) from None

        if not counter:
            self.put_item(
                table=sys_table,
                partition_key_key="pk_id",
                partition_key_value="__PK_VALUE_COUNTER__",
                current_counter_value=0,
                last_modified_timestamp=time.time_ns(),
            )

    def _put_single_item(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: PartitionKeyValue,
        sort_key_key: Optional[str] = None,
        sort_key_value: Optional[SortKeyValue] = None,
        **items: AttributeValue,
    ) -> dict[str, AttributeValueDeserialized]:
        """
        Put the item in the table.

        :param table: DynamoDB table name.
        :param partition_key_key: The key of the partition key.
        :param partition_key_value: The value of the partition key.
        :param sort_key_key: The key of the sort key.
        :param sort_key_value: The value of the sort key.
        :param items: Additional items to add.
        :return: The stored DynamoDB Item deserialized.
        :raise DynamoDBError: If operation fails.
        :raise DynamoDBConflictError: If put item fails due to a
            conflict.
        """

        pk_ser = self._serializer.serialize_p_key(
            pk_key=partition_key_key,
            pk_value=partition_key_value,
            sk_key=sort_key_key,
            sk_value=sort_key_value,
        )
        additional_items = self._serializer.serialize_put_items(**items)
        items_ser = {**additional_items, **pk_ser}

        # Initialize a dictionary with all the arguments to pass into
        # the DynamoDB put_item call
        ddb_put_item_args: dict[str, Any] = {
            'TableName': table,
            'Item': items_ser,
            'ConditionExpression': f"attribute_not_exists({partition_key_key})",
        }

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                retryer(self._client.put_item, **ddb_put_item_args)

        except botocore.exceptions.ClientError as ex:
            if "ConditionalCheckFailed" in str(ex):
                raise exceptions.DynamoDBConflictError(str(ex.response))
            else:
                raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        # If we get here it means that the item has been added
        # successfully therefore we return it
        item_put = {
            key: self._serializer.deserialize_att(value) for key, value in items_ser.items()
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
        exp, exp_att_names, exp_att_values = self._serializer.serialize_update_items(**{
            'current_counter_value': counter_value,
            'last_modified_timestamp': time.time_ns(),
        })

        # :condition_attribute_value_placeholder has to be
        # passed along the ExpressionAttributeValues because
        # is used by the ConditionExpression
        exp_att_values[':condition_attribute_value_placeholder'] = self._serializer.serialize_att(
            last_modified_timestamp
        )

        pk_ser = self._serializer.serialize_p_key(pk_key="pk_id", pk_value="__PK_VALUE_COUNTER__")

        el_update_ser: type_defs.UpdateTypeDef = {
            'TableName': sys_table,
            'Key': pk_ser,
            'UpdateExpression': exp,
            'ExpressionAttributeNames': exp_att_names,
            'ExpressionAttributeValues': exp_att_values,
            'ConditionExpression': (
                "#last_modified_timestamp = :condition_attribute_value_placeholder"
            ),
        }

        return el_update_ser

    def _get_pk_type(self, table: str) -> Union[type[bytes], type[str], type[float]]:
        """
        Scan the table and return the type of the PartitionKeyItem Key.

        :param table: DynamoDB table name.
        :return: The type of the PartitionKey key.
        :raise DynamoDBError: If operation fails.
        """

        # Initialize values to prevent UnboundLocalError
        pk_key = ""
        pk_key_type = ""

        try:
            with utils.retry(exception_to_check=Exception, delay_secs=1) as retryer:
                ddb_response = retryer(self._client.describe_table, TableName=table)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.DynamoDBError(str(ex.response))

        except Exception as ex:
            raise exceptions.DynamoDBError(str(ex))

        # Get the PartitionKey Key
        for idx, schemas in enumerate(ddb_response['Table']['KeySchema']):
            for k, v in schemas.items():
                if k == 'KeyType' and v == 'HASH':
                    pk_key = ddb_response['Table']['KeySchema'][idx]['AttributeName']

        # Get the PartitionKey Key Type
        for idx, attributes in enumerate(ddb_response['Table']['AttributeDefinitions']):
            for k, v in attributes.items():
                if k == 'AttributeName' and v == pk_key:
                    pk_key_type = ddb_response['Table']['AttributeDefinitions'][idx][
                        'AttributeType'
                    ]

        # Convert to Python type and return
        if pk_key_type == 'S':
            return str

        elif pk_key_type == 'B':
            return bytes

        elif pk_key_type == 'N':
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
        self,
        pk_key: str,
        pk_value: PartitionKeyValue,
        sk_key: Optional[str] = None,
        sk_value: Optional[SortKeyValue] = None,
    ) -> PartitionKeyItem:
        """
        Return a serialized DynamoDB partition key.

        :param pk_key: The key of the partition key.
        :param pk_value: The value of the partition key.
        :param sk_key: The key of the sort key.
        :param sk_value: The value of the sort key.
        :return: Serialized partition key.
            i.e. {"id": {"S": "string"}, "sortKey": {"S": "string"}}
        """

        if (sk_key is None) ^ (sk_value is None):
            raise exceptions.DynamoDBError(
                "Both sort_key_key and sort_key_value must be provided or both must be None."
            )
        has_sk = sk_key is not None and sk_value is not None

        pk_ser: PartitionKeyItem = {pk_key: self.serialize_att(pk_value)}

        if has_sk:
            assert sk_key is not None
            pk_ser[sk_key] = self.serialize_att(sk_value)

        return pk_ser

    def deserialize_p_key(
        self, pk_serialized: PartitionKeyItem
    ) -> tuple[str, PartitionKeyValue, Optional[str], Optional[SortKeyValue]]:
        """
        Deserialize a serialized DynamoDB partition key.

        :param pk_serialized: The serialized partition key.
            i.e., {"id": {"S": "string"}, "sortKey": {"S": "string"}}.
        :return: A tuple containing the partition key and its value.
        """

        iter_pk_ser = iter(pk_serialized.items())

        pk_key, pk_value_ser = next(iter_pk_ser)
        try:
            sk_key, sk_value_ser = next(iter_pk_ser)
        except StopIteration:
            sk_key, sk_value_ser = (None, None)

        pk_value = self.deserialize_att(pk_value_ser)
        assert isinstance(pk_value, (str, bytes, int, float))

        if sk_value_ser is not None:
            sk_value = self.deserialize_att(sk_value_ser)
            assert isinstance(sk_value, (str, bytes, int, float))
        else:
            sk_value = None

        return pk_key, pk_value, sk_key, sk_value

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
            ddb_attribute = self.serialize_att(value)

            # Now add it to the additional_items serialized dictionary
            additional_items[normalized_key] = ddb_attribute

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

        update_exp = "SET "

        # In DynamoDB operations(such as UpdateItem, Query, or Scan),
        # you can use ExpressionAttributeNames to provide alternate
        # names for attributes in your expressions.This is most
        # commonly used to work around DynamoDB's reserved keywords or
        # to use attribute names that contain special characters not
        # allowed in expressions.
        exp_att_names: dict[str, str] = {}

        # In DynamoDB API, the ExpressionAttributeValues dictionary is
        # used to pass in placeholders for values that will be used in
        # your UpdateExpression and ConditionExpression. The keys for
        # these placeholders should start with a : and should not be
        # confused with actual column names.
        exp_att_values: Item = {}

        for key, value in items.items():
            normalized_key = self.string_utils.snake_case(key)
            ddb_attribute = self.serialize_att(value)

            # Add to the update_expression string
            update_exp += f"#{normalized_key} = :{normalized_key}_placeholder, "

            # Add to the expression_attribute_names dict
            exp_att_names[f"#{normalized_key}"] = normalized_key

            # Add to the expression_attribute_values serialized dict
            exp_att_values[f":{normalized_key}_placeholder"] = ddb_attribute

        # Removing the trailing ", " from the update_expression string
        update_exp = update_exp[:-2]

        return update_exp, exp_att_names, exp_att_values

    def normalize_item(self, item: dict[str, Any]) -> dict[str, AttributeValueDeserialized]:
        """
        Serialize a Python item to DynamoDB format and then deserialize
        it back to ensure a fully consistent DynamoDB-deserialized
        structure.

        :param item: A dict of Python data, possibly partially
            deserialized or in raw Python format.
        :return: A dict representing the item in full
            DynamoDB-deserialized format
            (i.e., matching AttributeValueDeserialized).
        """

        item_ser = {key: self.serialize_att(value) for key, value in item.items()}

        item_deser = {key: self.deserialize_att(value) for key, value in item_ser.items()}

        return item_deser
