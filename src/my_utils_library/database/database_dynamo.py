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
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from typing import Any, Optional, Union

# Third Party Library Imports
import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef as DynamoDBAttribute
from mypy_boto3_dynamodb.type_defs import AttributeValueUpdateTypeDef as DynamoDBAttributeUpdate

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'DynamoDB',
]

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
        self._aws_service_name = "dynamodb"

    @property
    def _client(self) -> DynamoDBClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_dynamodb_client()
            return self._cache['client']

        else:
            return self._get_boto_dynamodb_client()

    @staticmethod
    def _serialize_attribute(attribute_value: DynamoDBAttributeValue) -> DynamoDBAttribute:
        """
        Serialize a Python data type into a format suitable for
        AWS DynamoDB.
        Transforms a Python data type into a format that is compatible
        with AWS DynamoDB by mapping it into its corresponding DynamoDB
        data type.

        :param attribute_value: The attribute value to be serialized.
               It can be any data type defined in the
               DynamoDBAttributeValue Union.
        :return: A dictionary containing the serialized attribute and
                 its corresponding DynamoDB data type descriptor.
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

        elif (
            isinstance(attribute_value, set)
            and len(attribute_value) > 0
            and all(isinstance(el, type(next(iter(attribute_value)))) for el in attribute_value)
        ):
            set_el_sample = next(iter(attribute_value))

            if isinstance(set_el_sample, str):
                return {"SS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, bytes):
                return {"BS": list(attribute_value)}  # type: ignore

            elif isinstance(set_el_sample, numbers.Real):
                return {"NS": [str(el) for el in attribute_value]}

            else:
                raise exceptions.DynamoDBError(
                    f"Value type for {attribute_value!r} is not supported by DynamoDB set. Set must"
                    " be homogeneous."
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
                f"Value type {type(attribute_value)!r} for {attribute_value!r} is not supported by "
                "DynamoDB serialization."
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
        :return: The deserialized Python data type, which can be any of
                 the types defined in DynamoDBAttributeValueDeserialized
                 Union.
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

        if dynamodb_attribute.get("NULL", sentinel) is not sentinel:
            return None

        elif dynamodb_attribute.get("BOOL", sentinel) is not sentinel:
            return bool(dynamodb_attribute["BOOL"])

        elif dynamodb_attribute.get("S", sentinel) is not sentinel:
            return str(dynamodb_attribute["S"])

        elif dynamodb_attribute.get("B", sentinel) is not sentinel:
            return dynamodb_attribute["B"]

        elif dynamodb_attribute.get("N", sentinel) is not sentinel:
            if '.' in dynamodb_attribute["N"]:
                return decimal.Decimal(dynamodb_attribute["N"])
            else:
                return int(dynamodb_attribute["N"])

        elif dynamodb_attribute.get("SS", sentinel) is not sentinel:
            return set(dynamodb_attribute["SS"])

        elif dynamodb_attribute.get("BS", sentinel) is not sentinel:
            return set(dynamodb_attribute["BS"])

        elif dynamodb_attribute.get("NS", sentinel) is not sentinel:
            if "." in dynamodb_attribute["NS"][0]:
                return {decimal.Decimal(el) for el in dynamodb_attribute["NS"]}
            else:
                return {int(el) for el in dynamodb_attribute["NS"]}

        elif dynamodb_attribute.get("L", sentinel) is not sentinel:
            return [DynamoDB._deserialize_attribute(el) for el in dynamodb_attribute["L"]]

        elif dynamodb_attribute.get("M", sentinel) is not sentinel:
            return {
                key: DynamoDB._deserialize_attribute(val)
                for key, val in dynamodb_attribute["M"].items()
            }

        else:
            raise exceptions.DynamoDBError(
                f"Value {dynamodb_attribute!r} is not supported for DynamoDB deserialization."
            )

    def _serialize_partition_key_for_dynamodb(
        self, partition_key_key: str, partition_key_value: DynamoDBPartitionKeyValue
    ) -> DynamoDBItem:
        """
        Return a serialized DynamoDB partition key.
        """

        partition_key_attribute = self._serialize_attribute(partition_key_value)
        partition_key = {partition_key_key: partition_key_attribute}

        return partition_key

    def _serialize_items_for_put(self, **items: DynamoDBAttributeValue) -> DynamoDBItem:
        """
        Returns a dictionary of additional items with keys and values
        serialized for DynamoDB put_item call.
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

        # Removing the leading , and space from the update_attributes
        # string
        update_attributes = update_attributes[:-2]

        return update_attributes, expression_attribute_values

    def _get_atomic_counter_value(self, table: str, partition_key_key: str) -> int:
        """
        In Amazon DynamoDB, there isn't an in-built auto-increment
        functionality like in SQL databases for generating record IDs
        (Primary Key values). However, you can achieve a similar outcome
        by managing an atomic counter. This method will get the value of
        the atomic counter
        """

        item = self.get_item_from_table(
            table=table, partition_key_key=partition_key_key, partition_key_value="__COUNTER__"
        )

        try:
            current_counter_value = item['current_counter_value']  # type: ignore
            assert isinstance(
                current_counter_value, int
            ), "'current_counter_value' should be an 'int'"

        except (AssertionError, TypeError, KeyError):
            raise exceptions.DynamoDBError(
                f"table: {table!r} doesn't have the '__COUNTER__' item, "
                "or the key of the counter value is not named 'current_counter_value'."
            )

        return current_counter_value

    def _update_atomic_counter_value(
        self, table: str, partition_key_key: str, new_counter_value: int
    ) -> None:
        """
        In Amazon DynamoDB, there isn't an in-built auto-increment
        functionality like in SQL databases for generating record IDs
        (Primary Key values). However, you can achieve a similar outcome
        by managing an atomic counter. This method will update the
        atomic counter.
        """

        self.update_item_in_table(
            table=table,
            partition_key={partition_key_key: "__COUNTER__"},
            current_counter_value=new_counter_value,
        )

    def _get_boto_dynamodb_client(self) -> DynamoDBClient:
        """
        Create a low-level dynamodb client.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
            )
            client = boto_session.client(service_name=self._aws_service_name)  # type: ignore

            return client

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

    def create_table_on_db(self):
        """
        Create a DynamoDB table.
        """
        # TODO: method to be implemented

        # response = self.client.create_table(
        #     TableName='JWT_Revoked_Identity_Tokens',
        #     KeySchema=[{"AttributeName": "jti", "KeyType": "HASH"}],
        #     AttributeDefinitions=[{"AttributeName": "jti",
        #     "AttributeType": "S"}],
        #     ProvisionedThroughput={"ReadCapacityUnits": 50,
        #     "WriteCapacityUnits": 50},
        # )

        return "NotImplemented"

    def get_all_tables(self) -> list[str]:
        """
        Returns an array of table names associated with the current
        account and endpoint.
        """

        try:
            dynamodb_response = self._client.list_tables()

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        response = dynamodb_response['TableNames']

        return response

    def get_all_items_in_table(
        self, table: str
    ) -> Generator[dict[str, DynamoDBAttributeValueDeserialized], None, None]:
        """
        Returns an Iterable of deserialized items in the table.

        :return: Iterable of dictionaries of all the columns in DynamoDB
                  i.e. {dynamodb_column_name: column_value, ...}
        """

        dynamodb_scan_args: dict[str, Any] = {'TableName': table}

        try:
            while True:
                dynamodb_response = self._client.scan(**dynamodb_scan_args)

                if dynamodb_response.get('Items') and len(dynamodb_response['Items']) > 0:
                    # Convert the DynamoDB attribute values to
                    # deserialized values
                    generate_deserialized_items = (
                        {
                            key: self._deserialize_attribute(value)
                            for key, value in dynamodb_item.items()
                        }
                        for dynamodb_item in dynamodb_response['Items']
                    )

                    yield from generate_deserialized_items

                # If LastEvaluatedKey is present then we need to scan
                # for more items
                if dynamodb_response.get('LastEvaluatedKey'):
                    dynamodb_scan_args['ExclusiveStartKey'] = dynamodb_response.get(
                        'LastEvaluatedKey'
                    )

                # If no LastEvaluatedKey then break out of the while
                # loop as we're done
                else:
                    break

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

    def get_count_of_all_items_in_table(self, table: str) -> int:
        """
        Returns the number of items in a table
        """

        response = len(list(self.get_all_items_in_table(table)))

        return response

    def get_item_from_table(
        self, table: str, partition_key_key: str, partition_key_value: DynamoDBPartitionKeyValue
    ) -> Optional[dict[str, DynamoDBAttributeValueDeserialized]]:
        """
        The get_item_from_table operation returns a dictionary of
        deserialized attribute values for the item with the given
        primary key. If there is no matching item, get_item_from_table
        returns None.
        """

        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        try:
            dynamodb_response = self._client.get_item(TableName=table, Key=partition_key)

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

        :return: The stored DynamoDB Item deserialized.
        """

        if partition_key_value is not None and auto_generate_partition_key_value is True:
            raise exceptions.DynamoDBError(
                "If a partition_key_value is passed, auto_generate_partition_key_value MUST be"
                " disabled."
            )

        elif partition_key_value is not None and auto_generate_partition_key_value is False:
            # This is the case where
            # partition_key_value = partition_key_value
            pass

        elif partition_key_value is None and auto_generate_partition_key_value is True:
            # This is the case where
            # partition_key_value = generate auto id
            current_item_id = self._get_atomic_counter_value(
                table=table, partition_key_key=partition_key_key
            )
            auto_generated_partition_key_value = current_item_id + 1
            # Convert the item_id to str as the primary partition key
            # in DynamoDB is set as type string
            auto_generated_partition_key_value_string = str(auto_generated_partition_key_value)

        elif partition_key_value is None and auto_generate_partition_key_value is False:
            raise exceptions.DynamoDBError(
                "If auto_generate_partition_key_value is disabled, a partition_key_value MUST be"
                " passed."
            )

        else:
            raise exceptions.DynamoDBError(
                "Unable to determine a valid operation with the provided 'partition_key_value' and"
                " 'auto_generate_partition_key_value'."
            )

        partition_key_final_value = partition_key_value or auto_generated_partition_key_value_string
        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_final_value
        )
        additional_items = self._serialize_items_for_put(**items)
        all_items_serialized = {**partition_key, **additional_items}

        try:
            self._client.put_item(
                TableName=table,
                Item=all_items_serialized,
                ConditionExpression=f"attribute_not_exists({partition_key_key})",
            )

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # If the new item was put successfully in DynamoDB, then update
        # the atomic counter
        if auto_generate_partition_key_value:
            try:
                self._update_atomic_counter_value(
                    table=table,
                    partition_key_key=partition_key_key,
                    new_counter_value=auto_generated_partition_key_value,
                )

            except exceptions.DynamoDBError:
                try:
                    # Failed to update the atomic counter, so we need to
                    # delete the item just put in DynamoDB
                    self.delete_items_from_table(
                        table, partition_key_key, auto_generated_partition_key_value_string
                    )

                    # If the deletion of the item from the db is
                    # successful then we raise the exception we are
                    # handling as we failed to update the atomic counter
                    raise

                # If the deletion of the item from the db fails there is
                # nothing else we can do if not request human action to
                # realign the __COUNTER__ with the total items in the db
                # THIS IS A CRITICAL ERROR!
                except exceptions.DynamoDBError:
                    message = "DynamoDB misaligned __COUNTER__ item. The __COUNTER__ is behind by 1"
                    logging.log(logging.CRITICAL, message)
                    raise exceptions.DynamoDBError(f"[CRITICAL ERROR] {message}")

        # If we get here it means that the item has been added
        # successfully therefore we retrieve and return it
        response = self.get_item_from_table(
            table=table,
            partition_key_key=partition_key_key,
            partition_key_value=partition_key_final_value,
        )

        # Check the response actually exists and is returned from the
        # request
        if response is None:
            raise exceptions.DynamoDBError("Operation failed!")

        return response

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
        dynamodb_update_item_args: dict[str, Any] = {'TableName': table}

        # Serialize partition key
        partition_key_key, partition_key_value = partition_key.popitem()
        partition_key_serialized = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        # Serialize attributes
        update_attributes, expression_attribute_values = self._serialize_items_for_update(**items)

        # Check if a condition is required
        if condition_attribute is not None:
            # Unpack condition attribute dictionary
            condition_attribute_key, condition_attribute_value = condition_attribute.popitem()

            # If condition attribute exists pass it to the DynamoDB call
            dynamodb_update_item_args.update(
                {
                    'ConditionExpression': (
                        f"{condition_attribute_key} = :condition_attribute_value_placeholder"
                    )
                }
            )
            # :condition_attribute_value_placeholder has to be passed
            # along the ExpressionAttributeValues because is used by the
            # ConditionExpression
            expression_attribute_values[
                ':condition_attribute_value_placeholder'
            ] = self._serialize_attribute(condition_attribute_value)

        # Update DynamoDB call arguments
        dynamodb_update_item_args.update(
            {
                'Key': partition_key_serialized,
                'UpdateExpression': update_attributes,
                'ExpressionAttributeValues': expression_attribute_values,
            }
        )

        logging.log(logging.DEBUG, dynamodb_update_item_args)

        try:
            self._client.update_item(**dynamodb_update_item_args)

        except Exception as ex:
            if "ConditionalCheckFailedException" in str(ex):
                raise exceptions.DynamoDBUpdateConflictError(f"Conflict Detected! - {str(ex)}")

            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        # If we get here it means that the item has been updated
        # successfully therefore we retrieve and return it
        response = self.get_item_from_table(
            table=table,
            partition_key_key=partition_key_key,
            partition_key_value=partition_key_value,
        )

        # Check the response actually exists and is returned from the
        # request
        if response is None:
            raise exceptions.DynamoDBError("Operation failed!")

        return response

    def delete_items_from_table(
        self, table: str, partition_key_key: str, *partition_key_values: DynamoDBPartitionKeyValue
    ):
        """
        Deletes item(s) in a table by primary key.
        """

        response = []

        try:
            for partition_key_value in partition_key_values:
                partition_key = self._serialize_partition_key_for_dynamodb(
                    partition_key_key, partition_key_value
                )

                dynamodb_response = self._client.delete_item(TableName=table, Key=partition_key)
                response.append(dynamodb_response)

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        return response

    def delete_item_values_from_table(
        self,
        table: str,
        partition_key_key: str,
        partition_key_value: DynamoDBPartitionKeyValue,
        *item_values: str,
    ):
        """
        Deletes item(s) specific value in a table by primary key.
        """

        partition_key = self._serialize_partition_key_for_dynamodb(
            partition_key_key, partition_key_value
        )

        attribute_updates: dict[str, DynamoDBAttributeUpdate] = {
            item_value: {'Action': "DELETE"} for item_value in item_values
        }
        try:
            dynamodb_response = self._client.update_item(
                TableName=table, Key=partition_key, AttributeUpdates=attribute_updates
            )

        except Exception as ex:
            raise exceptions.DynamoDBError(f"Operation failed! - {str(ex)}")

        return dynamodb_response
