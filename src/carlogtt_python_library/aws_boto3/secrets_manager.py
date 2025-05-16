# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/aws_boto3/secrets_manager.py
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
import logging
from typing import Any, Optional

# Third Party Library Imports
import botocore.exceptions
import mypy_boto3_secretsmanager
from mypy_boto3_secretsmanager import type_defs

# Local Folder (Relative) Imports
from .. import exceptions
from . import aws_service_base

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'SecretsManager',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
SecretsManagerClient = mypy_boto3_secretsmanager.client.SecretsManagerClient


class SecretsManager(aws_service_base.AwsServiceBase[SecretsManagerClient]):
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
            aws_service_name="secretsmanager",
            exception_type=exceptions.SecretsManagerError,
        )

    def get_all_secrets(self) -> list[type_defs.SecretListEntryTypeDef]:
        """
        Retrieves a list of all secrets stored in AWS Secrets Manager.

        This method paginates through the secrets if the number of
        secrets exceeds the max results per request, ensuring all
        secrets are retrieved.

        :return: A list of dictionaries, where each dictionary
                 represents a secret stored in AWS Secrets Manager.
                 The structure of each dictionary is defined by the
                 `SecretListEntryTypeDef`.
        :raise SecretsManagerError: If operation fails.
        """

        list_secrets_args: type_defs.ListSecretsRequestTypeDef = {}
        secrets = []

        try:
            while True:
                try:
                    secretsmanager_response = self._client.list_secrets(**list_secrets_args)

                except botocore.exceptions.ClientError as ex_inner:
                    raise exceptions.SecretsManagerError(str(ex_inner.response))

                secrets.extend(secretsmanager_response["SecretList"])

                if not secretsmanager_response.get('NextToken'):
                    break

                list_secrets_args['NextToken'] = secretsmanager_response["NextToken"]

            return secrets

        except Exception as ex:
            raise exceptions.SecretsManagerError(str(ex)) from None

    def get_secret(self, secret_id: str, **kwargs) -> Optional[dict[str, str]]:
        """
        Get secret from AWS Secrets Manager.
        Retrieves the contents of the encrypted fields from the
        specified secret_id.

        :param secret_id: The ARN (Amazon Resource Name) or name of
               the secret to retrieve.
               For an ARN, we recommend that you specify a complete ARN
               rather than a partial ARN.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: A dictionary containing the secret's contents.
                 In cases where the secret is not found, an empty
                 dictionary is returned.
        :raise SecretsManagerError: If operation fails.
        """

        get_secret_value_payload: type_defs.GetSecretValueRequestTypeDef = {
            'SecretId': secret_id,
            **kwargs,  # type: ignore
        }

        try:
            try:
                secretsmanager_response = self._client.get_secret_value(**get_secret_value_payload)

            except botocore.exceptions.ClientError as ex_inner:
                raise exceptions.SecretsManagerError(str(ex_inner.response))

            secret_str = secretsmanager_response.get('SecretString')

            # If secret is not found return None
            if not secret_str:
                return None

            # If secret is found load the string to Python dict
            secret = json.loads(secret_str)

            return secret

        except Exception as ex:
            raise exceptions.SecretsManagerError(str(ex)) from None

    def get_secret_password(self, secret_id: str, **kwargs) -> str:
        """
        Get secret from AWS Secrets Manager.
        Return ONLY the value of the 'password' field!

        :param secret_id: The ARN (Amazon Resource Name) or name of
               the secret to retrieve.
               For an ARN, we recommend that you specify a complete ARN
               rather than a partial ARN.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: ONLY the value of the 'password' field!
        :raise SecretsManagerError: If operation fails.
        """

        secret = self.get_secret(secret_id=secret_id, **kwargs)

        if secret:
            secret_password = secret.get('password', "")

        else:
            secret_password = ""

        return secret_password

    def delete_secret(
        self,
        secret_id: str,
        recovery_days: int = 30,
        force_delete: bool = False,
    ) -> type_defs.DeleteSecretResponseTypeDef:
        """
        Deletes a secret from AWS Secrets Manager.
        This method supports both immediate deletion and scheduled
        deletion.

        :param secret_id: The ARN (Amazon Resource Name) or name of
               the secret to delete.
               For an ARN, we recommend that you specify a complete ARN
               rather than a partial ARN.
        :param recovery_days: The number of days that Secrets Manager
               waits before permanently deleting the secret.
               This parameter is ignored if `force_delete` is set to
               True. Default is 30 days.
        :param force_delete: If set to True, the secret is immediately
               deleted without any recovery window. Default is False.
        :return: A dictionary with the deletion response. The structure
                 of the response is defined by the
                 `DeleteSecretResponseTypeDef`.
        :raise SecretsManagerError: If operation fails.
        """

        delete_secret_args: type_defs.DeleteSecretRequestTypeDef = {
            'SecretId': secret_id,
        }

        if force_delete:
            delete_secret_args['ForceDeleteWithoutRecovery'] = True

        else:
            delete_secret_args['RecoveryWindowInDays'] = recovery_days

        try:
            secretsmanager_response = self._client.delete_secret(**delete_secret_args)

            return secretsmanager_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SecretsManagerError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SecretsManagerError(str(ex)) from None
