# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_dynamodb.py
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
import datetime
from pprint import pprint

# Third Party Library Imports
import pytz
from test__entrypoint__ import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)
# master_logger.detach_root_logger()

# Type aliases
#


region = "eu-west-1"
profile = "carlogtt-conduit-dev"

dyn = mylib.DynamoDB(region, aws_profile_name=profile, caching=True)


def inv_db_all():
    response = dyn.get_items('Amz_Inventory_Tool_App_Products')
    counter = 0
    counternot = 0
    for product in response:
        if not product['product_id'].startswith('__'):
            counternot += 1
            if product.get('product_purchase_date'):
                new_product_purchase_date = product['product_purchase_date'] + '+00:00'
                # new_product_purchase_date = product['product_purchase_date'].split("+")[0]
                # print("Updating:", product['product_id'], product['product_purchase_date'], "to", new_product_purchase_date)
                counter += 1
                item = dyn.get_item(
                    'Amz_Inventory_Tool_App_Products', 'product_id', product['product_id']
                )
                print(f"Retrieve Item: {item['product_id']}")
                # dyn.update_item_in_table(
                #     'Amz_Inventory_Tool_App_Products',
                #     {'product_id': product['product_id']},
                #     product_purchase_date=new_product_purchase_date
                # )
    print("Updated:", counter)
    print("Not Updated:", counternot - counter)
    response = dyn.get_items('Amz_Inventory_Tool_App_Products')
    return response


def bookings_db_all():
    response = dyn.get_items('Amz_Inventory_Tool_App_Bookings')
    for product in response:
        if not product['booking_id'].startswith('__'):
            pass
            dyn.update_item(
                'Amz_Inventory_Tool_App_Bookings',
                {'booking_id': product['booking_id']},
                event_location="Europe/Luxembourg",
            )
    return response


def get_all_asset_tags():
    response = dyn.get_items('Amz_Inventory_Tool_App_Products')
    tags = []
    for product in response:
        if not product['product_id'].startswith('__'):
            tag = product['amazon_asset_tag']
            tags.append(tag)
    return tags


def add_value_products():
    response = dyn.get_items('Amz_Inventory_Tool_App_Products')
    tags = []
    for product in response:
        dyn.update_item(
            'Amz_Inventory_Tool_App_Products',
            {'product_id': product['product_id']},
            product_custom_name=None,
        )

    return


def update_value_products():
    response = dyn.get_items('Amz_Inventory_Tool_App_Products')
    for product in response:
        if 'Microphone' in product['product_type']:
            print('updating', product['product_id'])
            dyn.update_item(
                'Amz_Inventory_Tool_App_Products',
                {'product_id': product['product_id']},
                product_type='Microphone',
            )

    return


def dynamodb_table():
    # ddb = mylib.DynamoDB(region)
    table_name = "testTable"
    # response = ddb.put_item_in_table(table=table_name, partition_key_key="id", partition_key_value="2", col1='col1', col2='col2')
    # print(response)
    response = dyn.update_item(table=table_name, partition_key={"id": "2"}, col3="3")
    response = dyn.get_items_count(table=table_name)
    print(response)
    return


def new_dynamo_db_features():
    response = dyn.put_atomic_counter("testTable1")

    response = dyn.put_item(
        "testTable1", "id", auto_generate_partition_key_value=True, col1=1, col2=2, col3=3
    )

    return response


def migrate_asset_tags():
    table = "Amz_Inventory_Tool_App_Products_Asset_Tags"
    existing_assets = {
        "AMZ0",
        "AMZ99",
    }

    # for asset in existing_assets:
    #     print(f"putting {asset}")
    #     dyn.put_item_in_table(table,"asset_tag",asset)

    all_products = dyn.get_items("Amz_Inventory_Tool_App_Products")
    print(*all_products)

    # for prod in all_products:
    #     if not prod['product_id'].startswith('__'):
    #         asset_tag = prod.get('amazon_asset_tag')
    #         if asset_tag:
    #             print(prod['product_id'], asset_tag)
    #             dyn.update_item_in_table("Amz_Inventory_Tool_App_Products_Asset_Tags", {"asset_tag": asset_tag}, product_id=prod['product_id'])

    return


def get_bookings():
    bookings = dyn.get_items("Amz_Inventory_Tool_App_Bookings")
    ids = []
    for booking in bookings:
        ids.append(int(booking['booking_id']))

    ids.sort()
    rang = range(1, 85)
    diff = set(rang) - set(ids)
    print(sorted(list(diff)))

    products = dyn.get_items('Amz_Inventory_Tool_App_Products')

    for product in products:
        for booking_id in diff:
            bookings = product['bookings'] or []
            if str(booking_id) in bookings:
                print(product['product_id'], '=>', booking_id)


def update_item_ddb():
    table = 'Amz_Inventory_Tool_App_Settings_Changes_History'

    for item in dyn.get_items(table=table):
        print(item['history_log_id'])
        resp = dyn.delete_item_att(
            table=table,
            partition_key_key='history_log_id',
            partition_key_value=item['history_log_id'],
            attributes_to_delete=['logged_by', 'timestamp'],
        )
        print(resp)

    return


def update_product_location():
    table = 'Amz_Inventory_Tool_App_Products'

    for item in dyn.get_items(table=table):
        print(f"Updating Product ID: {item['product_id']}")

        product_id = item['product_id']

        if item['product_location'] == 'LHR16.07.804/5 (Studio)':
            dyn.update_item(
                table=table, partition_key={'product_id': product_id}, product_location="2"
            )
            print("product_location: 2")

        elif item['product_location'] == 'LHR16.07.506 (Prep Room)':
            dyn.update_item(
                table=table, partition_key={'product_id': product_id}, product_location="3"
            )
            print("product_location: 3")

        elif item['product_location'] == 'LHR16.02.706 (Storage)':
            dyn.update_item(
                table=table, partition_key={'product_id': product_id}, product_location="1"
            )
            print("product_location: 1")

        else:
            raise ValueError(f"Product location not valid: {item['product_location']}")

    return


def add_created_by_and_on():
    tables = [
        # 'Amz_Inventory_Tool_App_Bookings',
        # 'Amz_Inventory_Tool_App_Locations',
        # 'Amz_Inventory_Tool_App_Bookings_Changes_History',
        # 'Amz_Inventory_Tool_App_Locations_Changes_History',
        # 'Amz_Inventory_Tool_App_Products_Changes_History',
        # 'Amz_Inventory_Tool_App_Settings_Changes_History',
        # 'Amz_Inventory_Tool_App_Products_Checks_History',
        'Amz_Inventory_Tool_App_Products',
        'Amz_Inventory_Tool_App_Settings',
    ]

    table = tables[0]
    id_ = 'history_log_id'

    for item in dyn.get_items(table=table):
        print(f"Updating Table {table} {id_}: {item[id_]}")
        dt = datetime.datetime.utcfromtimestamp(item['last_modified_timestamp'] / 1_000_000_000)
        dt_aware = dt.replace(tzinfo=pytz.UTC)
        print(dt_aware.isoformat())
        # dyn.update_item_in_table(
        #     table=table,
        #     partition_key={id_: item[id_]},
        #     created_by=item['last_modified_by'],
        #     created_on=dt_aware.isoformat(),
        # )

    return


def update_or_insert():
    table = 'testTable1'

    item = dyn.get_item(table=table, partition_key_key='id', partition_key_value='2')
    pprint(item)

    item1 = dyn.update_item(
        table=table, partition_key={'id': '6'}, condition_attribute={'col4': 1}, col4=1
    )
    print(item1)


def delete():
    table = 'testTable1'

    item1 = dyn.upsert_item(table=table, partition_key={'id': '5'}, col4=1)
    print(item1)

    item1_deleted = dyn.delete_item(table=table, partition_key_key='id', partition_key_value='5')
    pprint(item1_deleted)


def atomic_op():

    table = 'testTable1'

    put = []
    for id_ in range(10, 15):
        put.append({
            'TableName': table,
            'PartitionKeyKey': 'id',
            'PartitionKeyValue': str(id_),
            'Items': {'col4': 1},
        })
    put = []

    delete = [{
        'TableName': table,
        'PartitionKey': {'id': '11'},
    }]
    delete = []

    update = [{
        'TableName': table,
        'PartitionKey': {'id': '11'},
        'Items': {'col6': 12},
    }]
    update = []

    upsert = [{
        'TableName': table,
        'PartitionKey': {'id': '11'},
        'Items': {'col6': 12},
    }]
    # upsert = []

    resp = dyn.atomic_writes(put=put, delete=delete, update=update, upsert=upsert)

    pprint(resp)


def delete_att():

    table = 'testTable1'

    item_att = dyn.delete_item_att(
        table=table, partition_key_key='id', partition_key_value='11', attributes_to_delete=['col6']
    )

    pprint(item_att)


def put_it():
    table = 'testTable1'
    resp = dyn.put_item(table=table, partition_key_key='id', partition_key_value='16', col8=12)

    pprint(resp)


if __name__ == '__main__':
    funcs = [
        # inv_db_all,
        # bookings_db_all,
        # get_all_asset_tags,
        # dynamodb_table,
        # new_dynamo_db_features,
        # migrate_asset_tags,
        # add_value_products,
        # update_value_products,
        # get_bookings,
        # update_item_ddb,
        # update_product_location,
        # add_created_by_and_on,
        # update_or_insert,
        # delete,
        # atomic_op,
        # delete_att,
        # put_it,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
