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
from typing import Any, Optional, Union

# Third Party Library Imports
import botocore.exceptions
import mypy_boto3_s3
from mypy_boto3_s3 import type_defs

# Local Folder (Relative) Imports
from .. import exceptions
from . import aws_service_base

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'S3',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
S3Client = mypy_boto3_s3.client.S3Client


class S3(aws_service_base.AwsServiceBase[S3Client]):
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
        super().__init__(
            aws_region_name=aws_region_name,
            aws_profile_name=aws_profile_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            caching=caching,
            client_parameters=client_parameters,
            aws_service_name="s3",
            exception_type=exceptions.S3Error,
        )

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

            list_objects_v2_params: type_defs.ListObjectsV2RequestTypeDef = {
                'Bucket': bucket,
                'Prefix': folder_path,
                **kwargs,  # type: ignore
            }

            while True:
                try:
                    s3_response = self._client.list_objects_v2(**list_objects_v2_params)

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

    def get_file(self, bucket: str, filename: str, **kwargs) -> type_defs.GetObjectOutputTypeDef:
        """
        Retrieves objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        get_obj_payload: type_defs.GetObjectRequestTypeDef = {
            'Bucket': bucket,
            'Key': filename,
            **kwargs,  # type: ignore
        }

        try:
            s3_response = self._client.get_object(**get_obj_payload)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None

    def store_file(
        self, bucket: str, filename: str, file: Union[str, bytes], **kwargs
    ) -> type_defs.PutObjectOutputTypeDef:
        """
        Store objects to Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to retrieve.
        :param file: The body of the file in bytes.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: The object stored in S3.
        :raise S3Error: If operation fails.
        """

        put_obj_pyaload: type_defs.PutObjectRequestTypeDef = {
            'Bucket': bucket,
            'Key': filename,
            'Body': file,
            **kwargs,  # type: ignore
        }

        try:
            s3_response = self._client.put_object(**put_obj_pyaload)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None

    def delete_file(
        self, bucket: str, filename: str, **kwargs
    ) -> type_defs.DeleteObjectOutputTypeDef:
        """
        Delete objects from Amazon S3.

        :param bucket: The name of the S3 bucket.
        :param filename: The name of the file to delete.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: S3 delete response syntax.
        :raise S3Error: If operation fails.
        """

        delete_obj_payload: type_defs.DeleteObjectRequestTypeDef = {
            'Bucket': bucket,
            'Key': filename,
            **kwargs,  # type: ignore
        }

        try:
            s3_response = self._client.delete_object(**delete_obj_payload)

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

        generate_url_payload: dict[str, Any] = {
            'ClientMethod': 'get_object',
            'Params': {
                'Bucket': bucket,
                'Key': filename,
            },
            'ExpiresIn': expiration_time,
            **kwargs,
        }

        try:
            s3_response = self._client.generate_presigned_url(**generate_url_payload)

            return s3_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.S3Error(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.S3Error(str(ex)) from None
