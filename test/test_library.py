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
from pprint import pprint

# Third Party Library Imports
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
cf = mylib.CloudFront(aws_region_name=region, aws_profile_name=profile)
lambdaf = mylib.Lambda(aws_region_name=region, aws_profile_name=profile)
sm = mylib.SecretsManager(aws_region_name=region, aws_profile_name=profile)


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


def secretsmanager():
    allsectets = sm.get_all_secrets()
    print(allsectets)

    sec = sm.get_secret('macOS_admin_account')
    print(sec)

    secp = sm.get_secret_password('macOS_admin_account')
    print(secp)
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
        # secretsmanager,
        # generate_thumbnail,
        # work_with_thumbnail,
        # secrets_manager1,
        # redis_cache,
        # redis_cache1,
        # redis_serializer,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
