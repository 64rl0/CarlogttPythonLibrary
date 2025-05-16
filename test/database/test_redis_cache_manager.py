# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_redis_cache_manager.py
# Created 4/25/25 - 10:32 PM UK Time (London) by carlogtt
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
import fnmatch
from typing import Optional

# Third Party Library Imports
import pytest
import redis
import redis.client

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


class _FakeRedis:
    def __init__(self, **_):
        self._store: dict[str, str] = {}

    # connection --------------------------------------------------------
    def ping(self):
        return True

    # basic KV ----------------------------------------------------------
    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, val: str) -> bool:
        self._store[key] = val
        return True

    def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    # iteration ---------------------------------------------------------
    def scan_iter(self, *, match: str):
        return [k for k in self._store if fnmatch.fnmatch(k, match)]


@pytest.fixture(autouse=True)
def _patch_redis(monkeypatch):
    """
    * Replace redis.Redis and redis.client.Redis with _FakeRedis.
    """

    monkeypatch.setattr(redis, "Redis", _FakeRedis, raising=True)
    monkeypatch.setattr(redis.client, "Redis", _FakeRedis, raising=True)

    yield


@pytest.fixture
def manager():
    from carlogtt_library.database.redis_cache_manager import RedisCacheManager

    return RedisCacheManager(
        host="fake-host",
        ssl=False,  # irrelevant for fake backend
        category_keys=["users", "sessions"],
    )


@pytest.fixture
def serializer():
    from carlogtt_library.database.redis_cache_manager import _RedisSerializer

    return _RedisSerializer()


# ----------------------------------------------------------------------
# Serializer round-trip -------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "value",
    [
        {"a", 1, 2},
        (1, 2, ("x", "y")),
        b"bytes!",
        {"nested": ({1, 2}, (3, 4))},
    ],
)
def test_serializer_roundtrip(serializer, value):
    dumped = serializer.serialize(value)
    loaded = serializer.deserialize(dumped)
    assert loaded == value


# ----------------------------------------------------------------------
# Lazy client cache & invalidation -------------------------------------
# ----------------------------------------------------------------------
def test_lazy_client_creation_and_invalidate(manager):
    # not initialised yet
    assert manager._redis_cached_client is None

    # first access: created & cached
    assert manager.keys_count() == 0
    assert isinstance(manager._redis_cached_client, _FakeRedis)

    # manual invalidation
    manager.invalidate_client_cache()
    assert manager._redis_cached_client is None

    # auto-recreate on next use
    manager.set("users", "u1", 123)
    assert isinstance(manager._redis_cached_client, _FakeRedis)


# ----------------------------------------------------------------------
# CRUD helpers ----------------------------------------------------------
# ----------------------------------------------------------------------
def test_set_get_has_delete(manager):
    assert manager.set("users", "u1", {"name": "Ada"})
    assert manager.has("users", "u1")
    assert manager.get("users", "u1") == {"name": "Ada"}
    assert manager.delete("users", "u1")
    assert not manager.has("users", "u1")
    assert manager.get("users", "u1") is None


# ----------------------------------------------------------------------
# Bulk helpers ----------------------------------------------------------
# ----------------------------------------------------------------------
def test_keys_values_category_helpers(manager):
    manager.set("sessions", "s1", 1)
    manager.set("sessions", "s2", 2)

    assert manager.keys_count("sessions") == 2
    assert set(manager.get_keys("sessions")) == {"s1", "s2"}
    assert set(manager.get_values("sessions")) == {1, 2}
    assert set(manager.get_category("sessions")) == {("s1", 1), ("s2", 2)}


def test_clear_single_and_all(manager):
    manager.set("users", "x", 1)
    manager.set("sessions", "y", 2)

    assert manager.clear("users")
    assert manager.keys_count("users") == 0
    assert manager.keys_count("sessions") == 1

    assert manager.clear()
    assert manager.keys_count() == 0


def test_unknown_category_raises(manager):
    from carlogtt_library.exceptions import RedisCacheManagerError

    with pytest.raises(RedisCacheManagerError):
        manager.set("invalid", "k", 1)


def _make_manager():
    from carlogtt_library.database.redis_cache_manager import RedisCacheManager

    return RedisCacheManager(
        host="fake",
        ssl=False,
        category_keys=["cat"],  # one valid category for positive-case calls
    )


@pytest.mark.parametrize(
    "method, kwargs",
    [
        ("has", dict(key="k")),
        ("get", dict(key="k")),
        ("set", dict(key="k", value=1)),
        ("delete", dict(key="k")),
        ("get_keys", {}),
        ("get_values", {}),
        ("get_category", {}),
        ("clear", {}),
        ("keys_count", {}),
    ],
)
def test_unknown_category_raises(method, kwargs):
    from carlogtt_library.exceptions import RedisCacheManagerError

    m = _make_manager()
    with pytest.raises(RedisCacheManagerError):
        getattr(m, method)("bad_category", **kwargs)

        if method == "get_keys":
            iterator = getattr(m, method)("bad_category", **kwargs)
            for _ in iterator:
                continue


@pytest.mark.parametrize(
    "method, redis_attr, kwargs",
    [
        ("has", "exists", dict(key="k")),
        ("get", "get", dict(key="k")),
        ("set", "set", dict(key="k", value=1)),
        ("delete", "delete", dict(key="k")),
        ("get_keys", "scan_iter", {}),
    ],
)
def test_redis_operation_failure_raises(monkeypatch, method, redis_attr, kwargs):
    from carlogtt_library.exceptions import RedisCacheManagerError

    m = _make_manager()

    # patch the attribute on the *instance* so only this test is affected
    failing = lambda *a, **kw: (_ for _ in ()).throw(Exception("boom"))
    monkeypatch.setattr(m._redis_client, redis_attr, failing, raising=True)

    with pytest.raises(RedisCacheManagerError):
        getattr(m, method)("cat", **kwargs)

        if method == "get_keys":
            iterator = getattr(m, method)("cat", **kwargs)
            for _ in iterator:
                continue


def test_initial_ping_failure(monkeypatch):
    from carlogtt_library.database.redis_cache_manager import RedisCacheManager
    from carlogtt_library.exceptions import RedisCacheManagerError

    class _BadRedis(_FakeRedis):
        def ping(self):
            raise redis.ConnectionError("cannot connect")

    # Patch both redis.Redis & redis.client.Redis to the failing variant
    monkeypatch.setattr(redis, "Redis", _BadRedis, raising=True)
    monkeypatch.setattr(redis.client, "Redis", _BadRedis, raising=True)

    mgr = RedisCacheManager(host="fake", ssl=False, category_keys=["cat"])

    with pytest.raises(RedisCacheManagerError):
        mgr.has("cat", "k")  # triggers lazy client creation / ping
