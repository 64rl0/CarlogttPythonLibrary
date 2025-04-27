# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_s3.py
# Created 4/25/25 - 8:53 PM UK Time (London) by carlogtt
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
def s3_instance():
    import carlogtt_library as mylib

    return mylib.S3(aws_region_name="us-east-1", caching=True)


@pytest.fixture
def mock_boto3():
    with mock.patch("carlogtt_library.aws_boto3.s3.boto3") as mock_boto3:
        yield mock_boto3


@pytest.fixture
def mock_client():
    with mock.patch("carlogtt_library.aws_boto3.s3.S3._client") as mock_client:
        yield mock_client


def test_client_caching(mock_boto3, s3_instance):
    mock_session = mock.Mock()
    mock_client = mock.Mock()
    mock_session.client.return_value = mock_client
    mock_boto3.session.Session.return_value = mock_session

    client1 = s3_instance._client
    client2 = s3_instance._client

    assert client1 is client2


def test_invalidate_client_cache(s3_instance):
    s3_instance._cache['client'] = "fake_client"
    s3_instance.invalidate_client_cache()
    assert s3_instance._cache['client'] is None


def test_invalidate_client_cache_without_caching():
    import carlogtt_library as mylib

    instance = mylib.S3(aws_region_name="us-east-1", caching=False)
    with pytest.raises(Exception) as excinfo:
        instance.invalidate_client_cache()
    assert "Session caching is not enabled" in str(excinfo.value)


def test_list_files(mock_client, s3_instance):
    mock_client.list_objects_v2.return_value = {
        "Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}]
    }
    files = s3_instance.list_files("bucket")
    assert files == ["file1.txt", "file2.txt"]


def test_list_files_empty(mock_client, s3_instance):
    mock_client.list_objects_v2.return_value = {}
    files = s3_instance.list_files("bucket")
    assert files == []


def test_get_file(mock_client, s3_instance):
    mock_client.get_object.return_value = {"Body": "file-content"}
    result = s3_instance.get_file("bucket", "file1.txt")
    assert result["Body"] == "file-content"


def test_store_file(mock_client, s3_instance):
    mock_client.put_object.return_value = {"ETag": "some-etag"}
    result = s3_instance.store_file("bucket", "file1.txt", b"data")
    assert "ETag" in result


def test_delete_file(mock_client, s3_instance):
    mock_client.delete_object.return_value = {"DeleteMarker": True}
    result = s3_instance.delete_file("bucket", "file1.txt")
    assert result["DeleteMarker"] is True


def test_create_presigned_url_for_file(mock_client, s3_instance):
    mock_client.generate_presigned_url.return_value = "https://s3.amazon.com/file1.txt"
    url = s3_instance.create_presigned_url_for_file("bucket", "file1.txt")
    assert url.startswith("https://")
