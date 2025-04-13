# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test_library.py
# Created 11/9/23 - 11:39 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module is only used for testing purposes
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
import logging
import os
import time
from pprint import pprint

# Third Party Library Imports
# import cv2
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

# Type aliases
#


region = "eu-west-1"
profile = "cg_dev"

s3_handler = mylib.S3(region, aws_profile_name=profile)
dyn = mylib.DynamoDB(region, aws_profile_name=profile, caching=True)
cf = mylib.CloudFront(aws_region_name=region, aws_profile_name=profile)
lambdaf = mylib.Lambda(aws_region_name=region, aws_profile_name=profile)
sm = mylib.SecretsManager(aws_region_name=region, aws_profile_name=profile)


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


def s3_list_files():
    url_prefix = "https://dve6lqhlrz3u1.cloudfront.net/"
    bucket_name = 'amzinventorytoolapp-products'
    files = s3_handler.list_files(bucket_name, folder_path="74")
    return [f"{url_prefix}{file}" for file in files]


def s3_get_file():
    bucket_name = 'amzinventorytoolapp-products'
    return s3_handler.get_file(bucket_name, '/299')


def s3_get_url():
    bucket_name = 'amzinventorytoolapp-products'
    return s3_handler.create_presigned_url_for_file(bucket_name, "74/image_1.jpg")


def s3_delete():
    bucket_name = 'amzinventorytoolapp-products'
    response = s3_handler.delete_file(bucket_name, '19/')

    return response


def s3_store_file():
    bucket_name = 'amzinventorytoolapp-products'

    with open('./static/python-logo.png', "rb") as photo:
        read_photo = photo.read()

    return s3_handler.store_file(bucket_name, "carlogtt/test123.jpg", read_photo)


def calc():
    import time

    start = time.perf_counter()
    for i in range(1_000_000_000):
        c = 10**3
    stop = time.perf_counter()
    return f"Execution time: {stop - start}"


def invalidate_cf():
    response = cf.invalidate_distribution(distribution="E32UW9Z0EMSSUV")

    return response


def lambda_test():
    response = lambdaf.invoke('SimTLambdaPython')

    for k, v in response.items():
        print(f"{k}: {v}")
    return response


def phone_tool():
    return mylib.phone_tool_lookup("carlogtt")


def encryption128():
    mycrypto = mylib.Cryptography()
    string = "hello dwddorld!"
    key = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BASE64)
    encrypted = mycrypto.encrypt_string(string, key, mylib.EncryptionAlgorithm.AES_128)
    print("Encrypted:", encrypted)
    decrypted = mycrypto.decrypt_string(encrypted, key, mylib.EncryptionAlgorithm.AES_128)
    print("Decrypted:", decrypted)


def encryption256():
    mycrypto = mylib.Cryptography()
    string = "hello world!"
    key = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    key2 = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    encrypted = mycrypto.encrypt_string(string, key2, mylib.EncryptionAlgorithm.AES_256)
    print("Encrypted:", encrypted)
    decrypted = mycrypto.decrypt_string(encrypted, key2, mylib.EncryptionAlgorithm.AES_256)
    print("Decrypted:", decrypted)


def hash_():
    mycrypto = mylib.Cryptography()
    key1 = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    key3 = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    string = "hello carlo!"
    hashed = mycrypto.hash_string(string, key1)
    print(hashed)

    hash_match = mycrypto.validate_hash_match("hello carlo!", hashed, key1)
    print(hash_match)


def create_key():
    mycrypto = mylib.Cryptography()
    key = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    print(len(key))

    return key


def confirmation_code():
    mycrypto = mylib.Cryptography()
    key = mycrypto.create_key(mylib.KeyType.AES256, mylib.KeyOutputType.BYTES)
    response1 = mycrypto.create_token(9, 300, key)
    response2 = mycrypto.verify_token(response1['token'], response1['ciphertoken'], key)
    print(response1)
    print(response2)
    return ""


def serialize():
    mycrypto = mylib.Cryptography()
    key = mycrypto.create_key(mylib.KeyType.AES128, mylib.KeyOutputType.BASE64)
    ser_key = mycrypto.serialize_key_for_str_storage(key)
    print("ser_key", ser_key, type(ser_key))
    des_key = mycrypto.deserialize_key_from_str_storage(ser_key)
    print("des_key", des_key, type(des_key))
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


def secretsmanager():
    allsectets = sm.get_all_secrets()
    print(allsectets)

    sec = sm.get_secret('macOS_admin_account')
    print(sec)

    secp = sm.get_secret_password('macOS_admin_account')
    print(secp)
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


def generate_thumbnail():
    bucket_name = 'amzinventorytoolapp-products'
    test = s3_handler.list_files(bucket_name)

    thumbnail_size = 60

    # for el in test:
    #     if "_1" in el:
    #         print("\n\n*******\n\n")
    #         id_, image_name = el.split("/")
    #         print(id_, image_name, el)
    #
    #         if int(id_) < 300:
    #             continue
    #
    #         file_obj = s3_handler.get_file(bucket_name, el)['Body']
    #         np_1d_array = np.frombuffer(file_obj.read(), dtype="uint8")
    #         image = cv2.imdecode(np_1d_array, cv2.IMREAD_COLOR)
    #
    #         ratio = image.shape[1] / image.shape[0]
    #         print(image.shape)
    #         print(f"Ratio: {ratio:.2f}")
    #
    #         if ratio > 1:
    #             print(f"New width: {thumbnail_size}.0px")
    #             print(f"New height: {thumbnail_size / ratio:.1f}px")
    #             new_image = cv2.resize(
    #                 image,
    #                 (thumbnail_size, int(thumbnail_size / ratio)),
    #                 interpolation=cv2.INTER_AREA,
    #             )
    #
    #         else:
    #             print(f"New width: {thumbnail_size * ratio:.1f}px")
    #             print(f"New height: {thumbnail_size}.0px")
    #             new_image = cv2.resize(
    #                 image,
    #                 (int(thumbnail_size * ratio), thumbnail_size),
    #                 interpolation=cv2.INTER_AREA,
    #             )
    #
    #         new_image_height, new_image_width = new_image.shape[:2]
    #         x_offset = (thumbnail_size - new_image_width) // 2
    #         y_offset = (thumbnail_size - new_image_height) // 2
    #
    #         white_background = np.full(
    #             (thumbnail_size, thumbnail_size, 3), (255, 255, 255), dtype=np.uint8
    #         )
    #         white_background[
    #             y_offset : y_offset + new_image_height, x_offset : x_offset + new_image_width
    #         ] = new_image
    #
    #         overlay = white_background
    #
    #         _, image_buffer = cv2.imencode(".jpg", overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    #
    #         s3_handler.store_file(bucket_name, f"{id_}/thumbnail.jpg", image_buffer.tobytes())
    #
    # cf.invalidate_distribution("E32UW9Z0EMSSUV")

    return


def work_with_thumbnail():
    bucket_name = 'amzinventorytoolapp-products'
    test = s3_handler.list_files(bucket_name)

    for el in test:
        print(el)

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


def secrets_manager1():
    response = sm.get_all_secrets()

    for r in response:
        print(r)

    return


def redis_cache():
    host = 'testcache-aacd7c.serverless.euw1.cache.amazonaws.com'
    cats = ['general', 'misc']

    r = mylib.RedisCacheManager(host=host, category_keys=cats)

    print(r.set('misc', "key123", 123))
    # print('all_keys:', r.get_all_keys(category='general'))
    # print('all_keys:', r.get_all_keys(category='misc'))

    return


def redis_cache1():
    r = mylib.RedisCacheManager(host='localhost', category_keys=['misc', 'test'], ssl=False)

    cat_misc = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
    }

    k = r.get_keys(category='misc')
    print(f"{k=}")

    v = r.get_values(category='misc')
    print(f"{v=}")

    c = r.get_category(category='misc')
    print(f"{c=}")

    el = r.get(category='misc', key='8:1717866058.6578455')
    print(f"key5={el}", type(el))

    exists = r.has(category='misc', key='1')
    print(f"{exists=}")

    not_exists = r.has(category='misc', key='123')
    print(f"{not_exists=}")

    delete = r.delete(category='misc', key='1')
    print(f"{delete=}")

    kcount = r.keys_count()
    print(f"{kcount=}")

    for el in c:
        print(el)

    # print(f"clear={r.clear()}")

    # for i in range(1, 11):
    #     resp = r.set(category='misc', key=f"{str(i)}:{repr(time.time())}", value=cat_misc)
    #     print(f"set{i}={resp}")

    return


def redis_serializer():
    test_data = {
        'a': set((1, 3, 'da', 5, 6)),
        'b': tuple((1, 4, 56, 7, (1, 2, 3))),
        'c': b"hello!",
        'd': 123,
        'f': [1, 2, 3, 5],
        'g': "hello world!",
        'h': {'a': 1, 'b': tuple((1, 2, 3)), 'c': [1, 2, 3], 'd': set((1, 34, 4))},
    }
    # test_data = "a"

    from carlogtt_library.database.redis_cache_manager import _RedisSerializer

    rs = _RedisSerializer()

    ser = rs.serialize(test_data)
    pprint(ser)

    des = rs.deserialize(ser)
    pprint(des)

    return


if __name__ == '__main__':
    funcs = [
        # s3_delete,
        # inv_db_all,
        # bookings_db_all,
        # get_all_asset_tags,
        # update_ass_tags,
        # s3_list_files,
        # s3_get_file,
        # s3_get_url,
        # s3_store_file,
        # invalidate_cf,
        # lambda_test,
        # phone_tool,
        # encryption128,
        # encryption256,
        # hash_,
        # create_key,
        # serialize,
        # confirmation_code,
        # dynamodb_table,
        # secretsmanager,
        # new_dynamo_db_features,
        # migrate_asset_tags,
        # generate_thumbnail,
        # work_with_thumbnail,
        # add_value_products,
        # update_value_products,
        # get_bookings,
        # sim,
        # update_item_ddb,
        # secrets_manager1,
        # update_product_location,
        # add_created_by_and_on,
        # redis_cache,
        # redis_cache1,
        redis_serializer,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
