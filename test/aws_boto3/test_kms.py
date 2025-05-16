# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/CarlogttLibrary/test/aws_boto3/test_kms.py
# Created 5/12/25 - 3:08 PM UK Time (London) by carlogtt
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
from unittest import mock

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


@pytest.fixture
def kms_instance():
    import carlogtt_library as mylib

    return mylib.KMS(aws_region_name="us-east-1", caching=True)


@pytest.fixture
def mock_boto3():
    with mock.patch("carlogtt_library.aws_boto3.aws_service_base.boto3") as mock_boto3:
        yield mock_boto3


@pytest.fixture
def mock_client():
    with mock.patch("carlogtt_library.aws_boto3.kms.KMS._client") as mock_client:
        yield mock_client


def test_client_caching(mock_boto3, kms_instance):
    mock_session = mock.Mock()
    mock_client = mock.Mock()
    mock_session.client.return_value = mock_client
    mock_boto3.session.Session.return_value = mock_session

    client1 = kms_instance._client
    client2 = kms_instance._client

    assert client1 is client2


def test_invalidate_client_cache(kms_instance):
    kms_instance._cache['client'] = "fake_client"
    kms_instance.invalidate_client_cache()
    assert kms_instance._cache['client'] is None


def test_invalidate_client_cache_without_caching():
    import carlogtt_library as mylib

    instance = mylib.KMS(aws_region_name="us-east-1", caching=False)
    with pytest.raises(Exception) as excinfo:
        instance.invalidate_client_cache()
    assert "Session caching is not enabled" in str(excinfo.value)
