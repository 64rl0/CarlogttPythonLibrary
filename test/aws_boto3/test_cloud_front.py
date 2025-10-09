# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/CarlogttLibrary/test/aws_boto3/test_cloud_front.py
# Created 5/12/25 - 3:12 PM UK Time (London) by carlogtt
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
from typing import Any, Dict

# Third Party Library Imports
import botocore.exceptions
import pytest

# My Library Imports
from carlogtt_python_library import exceptions as lib_exc
from carlogtt_python_library.aws_boto3.cloud_front import CloudFront

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


class _FakeCloudFront:
    """Pretends to be mypy_boto3_cloudfront.client.CloudFrontClient."""

    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []

    def create_invalidation(self, **payload):  # noqa: D401
        """Mimic the happy-path response from the real API."""
        self.calls.append(payload)
        return {"Invalidation": {"Id": "INV123", "Status": "InProgress"}}


class _FakeBotoSession:
    """Pretends to be `boto3.session.Session` (only what we need)."""

    def __init__(self, **init_kw) -> None:
        self.init_kw = init_kw
        self._client = _FakeCloudFront()

    def client(self, service_name: str, **_kw):
        # allow tests to simulate failures by asking for a special service name
        if service_name == "RAISE_CLIENT_ERROR":
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "Boom", "Message": "nope"}}, "CreateInvalidation"
            )
        if service_name == "RAISE_GENERIC":
            raise RuntimeError("bang")
        return self._client


@pytest.fixture(autouse=True)
def _patch_boto(monkeypatch):
    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    yield


class _CF(CloudFront):
    @property
    def client(self):
        return self._client


@pytest.mark.parametrize(
    "caching",
    [
        False,
        True,
    ],
)
def test_client_caching(caching):
    cf = _CF("us-east-1", caching=caching)
    first = cf.client
    second = cf.client
    if caching:
        assert first is second
    else:
        assert first is not second


def test_invalidate_distribution_success():
    cf = _CF("eu-west-1", caching=True)
    resp = cf.invalidate_distribution("DISTRIB123", path="/foo*")

    # response bubbled back
    assert resp["Invalidation"]["Id"] == "INV123"
    # correct payload reached the fake low-level client
    payload = cf.client.calls[-1]
    assert payload["DistributionId"] == "DISTRIB123"
    assert payload["InvalidationBatch"]["Paths"]["Items"] == ["/foo*"]


def test_invalidate_distribution_client_error_raises_custom():
    cf = _CF("eu-west-1", caching=False)
    #  force the fake boto session to explode with ClientError
    cf._aws_service_name = "RAISE_CLIENT_ERROR"

    with pytest.raises(lib_exc.CloudFrontError):
        cf.invalidate_distribution("BADID")


def test_invalidate_distribution_generic_error_raises_custom():
    cf = _CF("eu-west-1", caching=False)
    cf._aws_service_name = "RAISE_GENERIC"

    with pytest.raises(lib_exc.CloudFrontError):
        cf.invalidate_distribution("BADID")
