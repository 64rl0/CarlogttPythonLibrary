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
from typing import Optional

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
    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
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
        self._aws_service_name = "secretsmanager"

    @property
    def _client(self) -> SecretsManagerClient:
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

    def get_secret_password(self, secret_name: str) -> str:
        """
        Get secret from AWS Secrets Manager.
        Return ONLY the value of the 'password' field!

        :param secret_name: secret to retrieve from secrets manager.
        :return: ONLY the value of the 'password' field!
        """

        try:
            get_secret_value_response = self._client.get_secret_value(SecretId=secret_name)
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
