# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/CarlogttLibrary/test/aws_boto3/test_aws_service_base.py
# Created 5/12/25 - 10:21 AM UK Time (London) by carlogtt
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
from typing import Any

# Third Party Library Imports
import botocore.exceptions
import pytest

# My Library Imports
from carlogtt_library import exceptions
from carlogtt_library.aws_boto3.aws_service_base import AwsServiceBase

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


class FakeLowLevelClient:
    def __init__(self, **kw: Any) -> None:
        self.kw = kw


class FakeBotoSession:
    """Pretends to be boto3.session.Session."""

    def __init__(self, **init_kw: Any) -> None:  # noqa: D401
        # keep the args so tests can inspect them
        self.init_kw = init_kw

    def client(self, service_name: str, **client_kw: Any) -> FakeLowLevelClient:
        # mimic the boto contract
        if service_name == "raise-aws-error":
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "Unauthorized", "Message": "nope"}}, "SomeOp"
            )
        if service_name == "raise-generic":
            raise RuntimeError("boom")

        # otherwise return a fake botocore client
        return FakeLowLevelClient(service_name=service_name, **client_kw)


class DummyAwsError(exceptions.CarlogttLibraryError):
    """Custom error to verify the mapping logic."""


class DummyService(AwsServiceBase[FakeLowLevelClient]):
    """Bind the generic base to the fake client type."""

    # expose the protected client for test visibility
    @property
    def client(self) -> FakeLowLevelClient:  # type: ignore[override]
        return self._client


@pytest.fixture(autouse=True)
def _patch_boto(monkeypatch):
    """
    Replace boto3.session.Session with :class:`FakeBotoSession`
    for *every* test in this file.
    """
    import boto3.session  # imported here so it exists in sys.modules

    monkeypatch.setattr(boto3.session, "Session", FakeBotoSession)

    yield


@pytest.mark.parametrize(
    "caching",
    [
        False,
        True,
    ],
)
def test_client_is_returned_and_cached(caching):
    svc = DummyService(
        "eu-west-1",
        aws_service_name="s3",
        exception_type=DummyAwsError,
        caching=caching,
    )

    first = svc.client
    assert isinstance(first, FakeLowLevelClient)

    # When caching=True, the very same instance must be returned
    second = svc.client
    if caching:
        assert first is second
    else:
        assert first is not second


def test_invalidate_client_cache_works():
    svc = DummyService(
        "eu-west-1",
        aws_service_name="s3",
        exception_type=DummyAwsError,
        caching=True,
    )

    a = svc.client
    svc.invalidate_client_cache()
    b = svc.client

    assert a is not b  # new client after invalidation


def test_invalidate_without_cache_raises():
    svc = DummyService(
        "eu-west-1",
        aws_service_name="s3",
        exception_type=DummyAwsError,
        caching=False,
    )

    with pytest.raises(DummyAwsError):
        svc.invalidate_client_cache()


def test_client_error_is_mapped_to_custom_exception():
    svc = DummyService(
        "eu-west-1",
        aws_service_name="raise-aws-error",
        exception_type=DummyAwsError,
    )

    with pytest.raises(DummyAwsError) as exc:
        _ = svc.client

    assert "Unauthorized" in str(exc.value)


def test_generic_exception_is_mapped_to_custom_exception():
    svc = DummyService(
        "eu-west-1",
        aws_service_name="raise-generic",
        exception_type=DummyAwsError,
    )

    with pytest.raises(DummyAwsError):
        _ = svc.client


def test_extra_client_parameters_are_forwarded():
    extra = {"endpoint_url": "http://localhost:9000", "verify": False}
    svc = DummyService(
        "us-east-1",
        aws_service_name="s3",
        exception_type=DummyAwsError,
        client_parameters=extra,
    )

    assert svc.client.kw["endpoint_url"] == "http://localhost:9000"
    assert svc.client.kw["verify"] is False
