# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# secrets_manager.py
# Created 11/22/23 - 12:25 PM UK Time (London) by carlogtt
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
from typing import Any, Optional

# Third Party Library Imports
import boto3
import botocore.exceptions
from mypy_boto3_secretsmanager.client import SecretsManagerClient

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'SecretsManager',
]

# Type aliases
#


class SecretsManager:
    """
    The SecretsManager class provides a simplified interface for
    interacting with Amazon SecretsManager services within a Python
    application.

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
    :param caching: Determines whether to enable caching for the
           client session. If set to True, the client session will
           be cached to improve performance and reduce the number
           of API calls. Default is False.
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
        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._aws_service_name = "secretsmanager"

    @property
    def _client(self) -> SecretsManagerClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_secretsmanager_client()
            return self._cache['client']

        else:
            return self._get_boto_secretsmanager_client()

    def _get_boto_secretsmanager_client(self) -> SecretsManagerClient:
        """
        Create a low-level secrets manager client.
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
            raise exceptions.SecretsManagerError(f"Operation failed! - {str(ex)}")

    def get_secret_password(self, secret_name: str, **kwargs) -> str:
        """
        Get secret from AWS Secrets Manager.
        Return ONLY the value of the 'password' field!

        :param secret_name: secret to retrieve from secrets manager.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: ONLY the value of the 'password' field!
        """

        try:
            get_secret_value_response = self._client.get_secret_value(
                SecretId=secret_name, **kwargs
            )
            secret = get_secret_value_response['SecretString']

        # If secret is not found return an empty string
        except botocore.exceptions.ClientError:
            secret = ""

        # If secret is found load the string to Python dict and get
        # the password
        else:
            secret_json = json.loads(secret)
            secret = secret_json.get('password', "")

        return secret
