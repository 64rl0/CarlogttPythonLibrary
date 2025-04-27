# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_redis.py
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

# Special Imports
from __future__ import annotations

# Standard Library Imports
import fnmatch

# Third Party Library Imports
import pytest
import redis
import redis.client
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


# ----------------------------------------------------------------------
# Lightweight in-memory substitute for redis.Redis ----------------------
# ----------------------------------------------------------------------
class _FakeRedis:
    def __init__(self, **_):
        self._store: dict[str, str] = {}

    # connection --------------------------------------------------------
    def ping(self):
        return True

    # basic KV ----------------------------------------------------------
    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, val: str) -> bool:
        self._store[key] = val
        return True

    def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    # iteration ---------------------------------------------------------
    def scan_iter(self, *, match: str):
        return [k for k in self._store if fnmatch.fnmatch(k, match)]


# ----------------------------------------------------------------------
# Global monkey-patches applied to every test ---------------------------
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_redis_and_retry(monkeypatch):
    """
    * Replace redis.Redis and redis.client.Redis with _FakeRedis.
    * Turn utils.retry into a no-op decorator and context-manager.
    """

    monkeypatch.setattr(redis, "Redis", _FakeRedis, raising=True)
    monkeypatch.setattr(redis.client, "Redis", _FakeRedis, raising=True)

    # --------------------------------------------------------------------
    # utils.retry  –  no-op decorator **and** context-manager
    # --------------------------------------------------------------------
    class _NoopRetry:
        """Acts as decorator *and* context-manager, does absolutely nothing."""

        # --- decorator ---------------------------------------------------
        def __call__(self, fn):
            return fn  # just hand the function back unchanged

        # --- context-manager --------------------------------------------
        def __enter__(self):
            # when used in a with-statement we must return a *callable*
            # that proxies straight through to the wrapped function
            return lambda func, *a, **kw: func(*a, **kw)

        def __exit__(self, exc_type, exc, tb):
            # never swallow exceptions
            return False

    def _patched_retry(*_args, **_kwargs):
        """
        Keeps the original call signature (accepts the same args/kwargs),
        but always returns an instance of the multi-purpose helper above.
        """
        return _NoopRetry()

    import carlogtt_library.utils as utils_mod

    monkeypatch.setattr(utils_mod, "retry", _patched_retry, raising=True)

    yield


# ----------------------------------------------------------------------
# Fixtures for the system under test -----------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def manager():
    return mylib.RedisCacheManager(
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


# ----------------------------------------------------------------------
# Error paths -----------------------------------------------------------
# ----------------------------------------------------------------------
def test_unknown_category_raises(manager):
    with pytest.raises(mylib.RedisCacheManagerError):
        manager.set("invalid", "k", 1)


# --------------------------------------------------------------------------------------
# Helper to build a fresh manager for each test
# --------------------------------------------------------------------------------------
def _make_manager():
    return mylib.RedisCacheManager(
        host="fake",
        ssl=False,
        category_keys=["cat"],  # one valid category for positive-case calls
    )


# --------------------------------------------------------------------------------------
# 1) Unknown-category raises on *all* public methods that take one
# --------------------------------------------------------------------------------------
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
    m = _make_manager()
    with pytest.raises(mylib.RedisCacheManagerError):
        getattr(m, method)("bad_category", **kwargs)

        if method == "get_keys":
            iterator = getattr(m, method)("bad_category", **kwargs)
            for _ in iterator:
                continue


# --------------------------------------------------------------------------------------
# 2) Underlying redis failure surfaces as RedisCacheManagerError
#    – we monkey-patch the specific redis call used by each wrapper
# --------------------------------------------------------------------------------------
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
    m = _make_manager()

    # patch the attribute on the *instance* so only this test is affected
    failing = lambda *a, **kw: (_ for _ in ()).throw(Exception("boom"))
    monkeypatch.setattr(m._redis_client, redis_attr, failing, raising=True)

    with pytest.raises(mylib.RedisCacheManagerError):
        getattr(m, method)("cat", **kwargs)

        if method == "get_keys":
            iterator = getattr(m, method)("cat", **kwargs)
            for _ in iterator:
                continue


# --------------------------------------------------------------------------------------
# 3) Connection (ping) failure when client is first created
# --------------------------------------------------------------------------------------
def test_initial_ping_failure(monkeypatch):
    class _BadRedis(_FakeRedis):
        def ping(self):
            raise redis.ConnectionError("cannot connect")

    # Patch both redis.Redis & redis.client.Redis to the failing variant
    monkeypatch.setattr(redis, "Redis", _BadRedis, raising=True)
    monkeypatch.setattr(redis.client, "Redis", _BadRedis, raising=True)

    mgr = mylib.RedisCacheManager(host="fake", ssl=False, category_keys=["cat"])

    with pytest.raises(mylib.RedisCacheManagerError):
        mgr.has("cat", "k")  # triggers lazy client creation / ping
