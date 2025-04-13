# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/aws_boto3/s3.py
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
import logging
from typing import Any, Literal, Optional, Union

# Third Party Library Imports
import boto3
import botocore.exceptions
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import (
    DeleteObjectOutputTypeDef,
    GetObjectOutputTypeDef,
    ListObjectsV2RequestTypeDef,
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

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases


class S3:
    """
    The S3 class provides a simplified interface for interacting with
    Amazon S3 services within a Python application.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    :param aws_region_name: The name of the AWS region where the
           service is to be used. This parameter is required to
           configure the AWS client.
    :param aws_profile_name: The name of the AWS profile to use for
           credentials. This is useful if you have multiple profiles
           configured in your AWS credentials file.
           Default is None, which means the default profile or
           environment variables will be used if not provided.
    :param aws_access_key_id: The AWS access key ID for
           programmatically accessing AWS services. This parameter
           is optional and only needed if not using a profile from
           the AWS credentials file.
    :param aws_secret_access_key: The AWS secret access key
           corresponding to the provided access key ID. Like the
           access key ID, this parameter is optional and only needed
           if not using a profile.
    :param aws_session_token: The AWS temporary session token
           corresponding to the provided access key ID. Like the
           access key ID, this parameter is optional and only needed
           if not using a profile.
    :param caching: Determines whether to enable caching for the
           client session. If set to True, the client session will
           be cached to improve performance and reduce the number
           of API calls. Default is False.
    :param client_parameters: A key-value pair object of parameters that
           will be passed to the low-level service client.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        caching: bool = False,
        client_parameters: Optional[dict[str, Any]] = None,
    ) -> None:
        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_session_token = aws_session_token
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._aws_service_name: Literal['s3'] = "s3"
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> S3Client:
        """
        Returns a S3 client.
        Caches the client if caching is enabled.

        :return: The S3BClient.
        """

        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_client()
            return self._cache['client']

        else:
            return self._get_boto_client()

    def _get_boto_client(self) -> S3Client:
        """
        Create a low-level S3 client.

        :return: The S3Client.
        :raise S3Error: If operation fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
            )
            client = boto_session.client(
                service_name=self._aws_service_name, **self._client_parameters
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response))

        except Exception as ex:
            raise exceptions.S3Error(str(ex))

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise S3Error: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.S3Error(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    def list_files(self, bucket: str, folder_path: str = "", **kwargs) -> list[str]:
        """
        List all the files in the bucket.

        :param bucket: The name of the S3 bucket.
        :param folder_path: The prefix to the path of the folder to
               list. Leave default to list all the files in the bucket.
               (Default: "").
        :param kwargs: Any other param passed to the underlying boto3.
        :return: A list of the files in the bucket.
        :raise S3Error: If operation fails.
        """
        try:
            filenames_list: list[str] = []

            list_objects_v2_params: ListObjectsV2RequestTypeDef = {
                'Bucket': bucket,
                'Prefix': folder_path,
            }

            while True:
                try:
                    s3_response = self._client.list_objects_v2(**list_objects_v2_params, **kwargs)

                except botocore.exceptions.ClientError as ex_inner:
                    raise exceptions.S3Error(str(ex_inner.response))

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
            raise exceptions.S3Error(str(ex)) from None

    def get_file(self, bucket: str, filename: str, **kwargs) -> GetObjectOutputTypeDef:
        """
        Retrieves objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.get_object(Bucket=bucket, Key=filename, **kwargs)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None

    def store_file(
        self, bucket: str, filename: str, file: Union[str, bytes], **kwargs
    ) -> PutObjectOutputTypeDef:
        """
        Store objects to Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param file: The body of the file in bytes.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.put_object(Bucket=bucket, Key=filename, Body=file, **kwargs)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None

    def delete_file(self, bucket: str, filename: str, **kwargs) -> DeleteObjectOutputTypeDef:
        """
        Delete objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to delete.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: S3 delete response syntax.
        :raise S3Error: If operation fails.
        """

        try:
            s3_response = self._client.delete_object(Bucket=bucket, Key=filename, **kwargs)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None

    def create_presigned_url_for_file(
        self, bucket: str, filename: str, expiration_time: int = 3600, **kwargs
    ) -> str:
        """
        Creates a presigned URL for a file stored in Amazon S3.
        The URL can be used to access the file for a limited time.
        The URL expires after a fixed amount of time.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param expiration_time: The number of seconds until the URL
               expires. (Default: 3600).
        :param kwargs: Any other param passed to the underlying boto3.
        :return: The presigned URL.
        :raise S3Error: If operation fails.
        """

        try:
            client_method_params = {'Bucket': bucket, 'Key': filename}

            s3_response = self._client.generate_presigned_url(
                ClientMethod='get_object',
                Params=client_method_params,
                ExpiresIn=expiration_time,
                **kwargs,
            )

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None
