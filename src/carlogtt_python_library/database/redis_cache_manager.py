# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/database/redis_cache_manager.py
# Created 6/7/24 - 10:30 AM UK Time (London) by carlogtt
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
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import json
import logging
from collections.abc import Generator, Iterable, Iterator
from typing import Any, Optional

# Third Party Library Imports
import redis

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'RedisCacheManager',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class RedisCacheManager:
    """
    Cache manager using Redis.

    :param host: The Redis server host.
    :param port: The Redis server port (default is 6379).
    :param username: The username for Redis authentication
        (default is 'default').
    :param password: The password for Redis authentication (optional).
    :param db: The Redis database number (default is 0).
    :param ssl: Whether to use SSL for the Redis connection
        (default is True).
    :param decode_responses: Whether to decode responses from Redis
        (default is True).
    :param category_keys: An iterable of strings representing the
        valid cache categories.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int = 6379,
        username: str = 'default',
        password: Optional[str] = None,
        db: int = 0,
        ssl: bool = True,
        decode_responses=True,
        category_keys: Iterable[str],
        **redis_kwargs: Any,
    ) -> None:
        self._redis_kwargs = {
            'host': host,
            'ssl': ssl,
            'port': port,
            'username': username,
            'password': password,
            'db': db,
            'decode_responses': decode_responses,
            **redis_kwargs,
        }

        self._categories = set(category_keys)
        self._redis_cached_client: Optional[redis.client.Redis] = None
        self._serializer = _RedisSerializer()

    @property
    def _redis_client(self) -> redis.client.Redis:
        """
        Lazily initializes and returns the Redis client.

        :return: The Redis client.
        :raise: RedisCacheManagerError if unable to connect to Redis.
        """

        if not self._redis_cached_client:
            try:
                self._redis_cached_client = redis.Redis(**self._redis_kwargs)
                self._redis_cached_client.ping()

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

        return self._redis_cached_client

    @utils.retry(exception_to_check=exceptions.RedisCacheManagerError, tries=2, delay_secs=1)
    def has(self, category: str, key: str) -> bool:
        """
        Checks if a key exists in the cache.

        :param category: The cache category.
        :param key: The specific key within the category.
        :return: True if the key exists, False otherwise.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_key = self._serializer.serialize_redis_key(category, key)

            try:
                redis_response = self._redis_client.exists(redis_key)

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

            # Returns the number of keys that exist
            exists = redis_response == 1

            return exists

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")

    @utils.retry(exception_to_check=exceptions.RedisCacheManagerError, tries=2, delay_secs=1)
    def get(self, category: str, key: str) -> Optional[Any]:
        """
        Retrieves a value from the cache.

        :param category: The cache category.
        :param key: The specific key within the category.
        :return: The cached value, or None if not found.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_key = self._serializer.serialize_redis_key(category, key)

            try:
                redis_response = self._redis_client.get(redis_key)

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

            if redis_response:
                assert isinstance(redis_response, str)
                response = self._serializer.deserialize(redis_response)

            else:
                response = None

            return response

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")

    @utils.retry(exception_to_check=exceptions.RedisCacheManagerError, tries=2, delay_secs=1)
    def set(self, category: str, key: str, value: Any) -> bool:
        """
        Sets a value in the cache.

        :param category: The cache category.
        :param key: The specific key within the category.
        :param value: The value to cache.
        :return: True if the value was successfully set, False
            otherwise.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_key = self._serializer.serialize_redis_key(category, key)
            redis_value = self._serializer.serialize(value)

            try:
                redis_response = self._redis_client.set(redis_key, redis_value)

                if redis_response:
                    assert isinstance(redis_response, bool)
                    return redis_response

                else:
                    return False

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")

    @utils.retry(exception_to_check=exceptions.RedisCacheManagerError, tries=2, delay_secs=1)
    def delete(self, category: str, key: str) -> bool:
        """
        Invalidates a specific key in the cache.

        :param category: The cache category.
        :param key: The specific key within the category.
        :return: True if the key was successfully invalidated,
            False otherwise.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_key = self._serializer.serialize_redis_key(category, key)

            try:
                redis_response = self._redis_client.delete(redis_key)

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

            # Returns the number of keys invalidated
            invalidated = redis_response == 1

            return invalidated

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")

    def clear(self, category: Optional[str] = None) -> bool:
        """
        Clears all keys in the specified category, or all categories if
        none is specified.

        :param category: The cache category to clear (optional).
        :return: True if all keys were successfully cleared,
            False otherwise.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category:
            if category in self._categories:
                categories = {category}

            else:
                raise exceptions.RedisCacheManagerError(
                    f"[CACHE] - Category {category} not recognized"
                )

        else:
            categories = self._categories

        keys_to_delete = 0
        running_total = 0

        for cat in categories:
            # Check there are keys in the cache
            redis_keys = self.get_keys(category=cat)
            if redis_keys is None:
                continue

            for redis_key in redis_keys:
                keys_to_delete += 1
                if self.delete(category=cat, key=redis_key):
                    running_total += 1

        if running_total == keys_to_delete:
            return True

        else:
            return False

    def keys_count(self, category: Optional[str] = None) -> int:
        """
        Returns the total number of keys in the cache for the specified
        category.

        :param category: (optional) a string representing the name of
            the category. If None, all the available categories will
            be considered.
        :return: An integer representing the total number of keys in
            the cache for the specified category.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category:
            if category in self._categories:
                categories = {category}

            else:
                raise exceptions.RedisCacheManagerError(
                    f"[CACHE] - Category {category} not recognized"
                )

        else:
            categories = self._categories

        running_total = 0

        for cat in categories:
            # Check there are keys in the cache
            redis_keys = self.get_keys(category=cat)
            if redis_keys is None:
                continue

            for _ in redis_keys:
                running_total += 1

        return running_total

    def get_category(self, category: str) -> Optional[Iterator[tuple[str, Any]]]:
        """
        Retrieves key-value pairs for all items in the specified cache
        category.

        :param category: The cache category.
        :return: An iterator of the cached key-value pairs, or None if
            no items in cache.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        redis_keys = self.get_keys(category=category)
        redis_values = self.get_values(category=category)

        if redis_keys is None or redis_values is None:
            return None

        response = zip(redis_keys, redis_values)

        return response

    @utils.retry(exception_to_check=exceptions.RedisCacheManagerError, tries=2, delay_secs=1)
    def get_keys(self, category: str) -> Optional[Iterator[str]]:
        """
        Retrieves all keys in the specified cache category.

        :param category: The cache category.
        :return: An iterator of the cached keys, or None if no keys
            in cache.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_key_pattern = self._serializer.serialize_redis_key(category)

            try:
                redis_response = self._redis_client.scan_iter(match=redis_key_pattern)

            except Exception as ex:
                raise exceptions.RedisCacheManagerError(f"[CACHE] - Redis error: {str(ex)}")

            try:
                first_value = next(redis_response)

            except StopIteration:
                return None

            def gen_wrapper() -> Generator[str, None, None]:
                yield first_value.split(':', 1)[1]

                for value in redis_response:
                    yield value.split(':', 1)[1]

            # This is the iterator we are going to return
            keys = gen_wrapper()

            return keys

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")

    def get_values(self, category: str) -> Optional[Iterator[Any]]:
        """
        Retrieves all values in the specified cache category.

        :param category: The cache category.
        :return: An iterator of the cached values, or None if no values
            in cache.
        :raise: RedisCacheManagerError if an error occurs while
            accessing Redis.
        """

        if category in self._categories:
            redis_keys = self.get_keys(category=category)

            if redis_keys is None:
                return None

            response = (self.get(category=category, key=redis_key) for redis_key in redis_keys)

            return response

        else:
            raise exceptions.RedisCacheManagerError(f"[CACHE] - Category {category} not recognized")


class _RedisEncoder(json.JSONEncoder):
    """
    _RedisEncoder extends the JSONEncoder to support additional
    data types.
    """

    def default(self, obj: Any) -> Any:
        """
        Override the default method to handle additional data types.

        A function that gets called for objects that can’t otherwise
        be serialized. It should return a JSON encodable version of
        the object.

        :param obj: The object to be serialized.
        :return: The serialized form of the object.
        """

        if isinstance(obj, (set, tuple, bytes, complex)):
            return self._default(obj)

        else:
            raise exceptions.RedisCacheManagerError(
                f"Object of type {type(obj)!r} for {obj!r} is not supported by Redis serialization."
            )

    def _default(self, obj: Any) -> Any:
        """
        Custom method to handle serialization recursively of
        specific types.

        :param obj: The object to be serialized.
        :return: The serialized form of the object.
        """

        if isinstance(obj, set):
            return {'__sentinel_type__': 'set', 'data': [self._default(el) for el in obj]}

        elif isinstance(obj, bytes):
            return {'__sentinel_type__': 'bytes', 'data': obj.decode('utf-8')}

        elif isinstance(obj, complex):
            return {'__sentinel_type__': 'complex_num', 'data': [obj.real, obj.imag]}

        # Note to future carlogtt, tuple does not call the default
        # function as they are not seen as unserializable obj, but
        # they are seen as list
        elif isinstance(obj, tuple):
            return {'__sentinel_type__': 'tuple', 'data': [self._default(el) for el in obj]}

        else:
            return obj

    def encode(self, obj: Any) -> str:
        """
        Return a JSON string representation of a Python data
        structure.

        :param obj: The object to be serialized.
        :return: The JSON string representation of the object.
        """

        # Handle tuples because JSON is converting them to lists
        # Note to future carlogtt, not sure set will ever get here
        if isinstance(obj, (dict, set, list, tuple)):
            obj = self._encode(obj)

        return super().encode(o=obj)

    def _encode(self, obj: Any) -> Any:
        """
        Custom method to recursively encode tuple data type.

        :param obj: The object to be serialized.
        :return: The encoded form of the object.
        """

        # The super encode method would convert tuples to lists, so
        # we need to intercept that and convert tuples to dict with
        # a sentinel_value
        # Also dicts and lists can contain tuples
        if isinstance(obj, dict):
            obj = {key: self._encode(value) for key, value in obj.items()}

        elif isinstance(obj, list):
            obj = [self._encode(el) for el in obj]

        elif isinstance(obj, tuple):
            obj = {'__sentinel_type__': 'tuple', 'data': [self._encode(el) for el in obj]}

        # Note to future carlogtt, not sure set will ever get here
        # as they are converted to dict in the above default method
        elif isinstance(obj, set):
            obj = {self._encode(el) for el in obj}

        return obj


class _RedisDecoder(json.JSONDecoder):
    """
    _RedisDecoder extends the JSONDecoder to support the
    deserialization of additional data types encoded by the
    _RedisEncoder.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(dict_obj: dict[str, Any]) -> Any:
        """
        object_hook is an optional function that will be called with
        the result of any object literal decoded (a dict).
        The return value of object_hook will be used instead of the
        dict.

        Custom object hook to convert dictionaries back to original
        data types based on sentinel type.

        :param dict_obj: The dictionary to be converted.
        :return: The deserialized object.
        """

        if '__sentinel_type__' in dict_obj:
            if dict_obj['__sentinel_type__'] == 'set':
                return set(dict_obj['data'])

            elif dict_obj['__sentinel_type__'] == 'tuple':
                return tuple(dict_obj['data'])

            elif dict_obj['__sentinel_type__'] == 'bytes':
                return dict_obj['data'].encode('utf-8')

            elif dict_obj['__sentinel_type__'] == 'complex':
                return complex(dict_obj['data'][0], dict_obj['data'][1])

        return dict_obj


class _RedisSerializer:
    """
    RedisSerializer is a utility class for serializing and deserializing
    complex Python data types to JSON format and back.
    It extends the capabilities of the standard JSON encoder and decoder
    to handle additional data types such as sets, tuples, bytes, and
    complex numbers.

    This class is useful for storing Python objects in a Redis database,
    where data needs to be converted to a JSON-compatible format for
    storage and then back to Python objects when retrieved.
    """

    def serialize(self, obj: Any) -> str:
        """
        Serialize a Python object to a JSON string using the custom
        encoder.

        :param obj: The object to be serialized.
        :return: The JSON string representation of the object.
        """

        return json.dumps(obj=obj, cls=_RedisEncoder)

    def deserialize(self, s: str) -> Any:
        """
        Deserialize a JSON string back to a Python object using the
        custom decoder.

        :param s: The JSON string to be deserialized.
        :return: The deserialized Python object.
        """

        return json.loads(s=s, cls=_RedisDecoder)

    @staticmethod
    def serialize_redis_key(category: str, key: Optional[str] = None) -> str:
        """
        Generates a Redis key with a prefix based on the category.

        :param category: The cache category.
        :param key: The specific key within the category (optional).
        :return: The full Redis key with prefix.
        """

        if key:
            return f"{category}:{key}"

        else:
            return f"{category}:*"
