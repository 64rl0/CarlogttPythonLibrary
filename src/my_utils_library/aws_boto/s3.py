# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# s3.py
# Created 11/9/23 - 10:00 AM UK Time (London) by carlogtt
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
from typing import Any, Optional

# Third Party Library Imports
import boto3
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import (
    DeleteObjectOutputTypeDef,
    GetObjectOutputTypeDef,
    ListObjectsV2RequestRequestTypeDef,
    PutObjectOutputTypeDef,
)

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'S3',
]

# Type aliases


class S3:
    """
    The S3 class provides a simplified interface for interacting with
    Amazon S3 services within a Python application.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        caching: bool = False,
    ) -> None:
        """
        aws_profile and aws_region are injected locally for local
        development testing through Brazil. When running on NAWS this
        env variable is not set.
        """

        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self.caching = caching
        self.cache: dict[str, Any] = dict()
        self._aws_service_name = "s3"

    @property
    def _client(self) -> S3Client:
        if self.caching:
            if self.cache.get('client') is None:
                self.cache['client'] = self._get_boto_s3_client()
            return self.cache['client']

        else:
            return self._get_boto_s3_client()

    def _get_boto_s3_client(self) -> S3Client:
        """
        Create a low-level s3 client.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
            )
            client = boto_session.client(service_name=self._aws_service_name)  # type: ignore

            return client

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def list_files(self, bucket: str, folder_path: str = "") -> list[str]:
        """
        List all the files in the bucket.

        :param bucket: The name of the S3 bucket.
        :param folder_path: The prefix to the path of the folder to
               list. Leave default to list all the files in the bucket.
               (Default: "").
        :return: A list of the files in the bucket.
        :raise S3Error: If operation fails.
        """
        try:
            while True:
                filenames_list: list[str] = []

                list_objects_v2_params: ListObjectsV2RequestRequestTypeDef = {
                    'Bucket': bucket,
                    'Prefix': folder_path,
                }
                s3_response = self._client.list_objects_v2(**list_objects_v2_params)

                for file in s3_response.get('Contents', {}):
                    try:
                        filenames_list.append(file['Key'])

                    except KeyError:
                        continue

                # If ContinuationToken is present in the response then
                # we need to scan for more files
                if s3_response.get('ContinuationToken'):
                    list_objects_v2_params['ContinuationToken'] = s3_response['ContinuationToken']

                else:
                    break

            return filenames_list

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def get_file(self, bucket: str, filename: str) -> GetObjectOutputTypeDef:
        """
        Retrieves objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.get_object(Bucket=bucket, Key=filename)

            return s3_response

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def store_file(self, bucket: str, filename: str, file: bytes) -> PutObjectOutputTypeDef:
        """
        Store objects to Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param file: The body of the file in bytes.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.put_object(Bucket=bucket, Key=filename, Body=file)

            return s3_response

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def delete_file(self, bucket: str, filename: str) -> DeleteObjectOutputTypeDef:
        """
        Delete objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to delete.
        :return: S3 delete response syntax.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.delete_object(Bucket=bucket, Key=filename)

            return s3_response

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def create_presigned_url_for_file(
        self, bucket: str, filename: str, expiration_time: int = 3600
    ) -> str:
        """
        Creates a presigned URL for a file stored in Amazon S3.
        The URL can be used to access the file for a limited time.
        The URL expires after a fixed amount of time.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param expiration_time: The number of seconds until the URL
               expires. (Default: 3600).
        :return: The presigned URL.
        :raise S3Error: If operation fails.
        """

        try:
            client_method_params = {'Bucket': bucket, 'Key': filename}

            s3_response = self._client.generate_presigned_url(
                ClientMethod='get_object', Params=client_method_params, ExpiresIn=expiration_time
            )

            return s3_response

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")
