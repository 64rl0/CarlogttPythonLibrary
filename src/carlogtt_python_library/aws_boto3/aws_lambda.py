# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/aws_boto3/aws_lambda.py
# Created 3/13/24 - 7:25 PM UK Time (London) by carlogtt
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
from typing import Any, Literal, Optional

# Third Party Library Imports
import boto3
import botocore.exceptions
from mypy_boto3_lambda.client import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Lambda',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class Lambda:
    """
    The Lambda class provides a simplified interface for interacting
    with Amazon Lambda services within a Python application.

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
        self._aws_service_name: Literal['lambda'] = "lambda"
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> LambdaClient:
        """
        Returns a Lambda client.
        Caches the client if caching is enabled.

        :return: The LambdaClient.
        """

        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_client()
            return self._cache['client']

        else:
            return self._get_boto_client()

    def _get_boto_client(self) -> LambdaClient:
        """
        Create a low-level Lambda client.

        :return: The LambdaClient.
        :raise LambdaError: If operation fails.
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
            raise exceptions.LambdaError(str(ex.response))

        except Exception as ex:
            raise exceptions.LambdaError(str(ex))

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise LambdaError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.LambdaError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    def invoke(self, function_name: str, **kwargs) -> InvocationResponseTypeDef:
        """
        Invokes a Lambda function.

        :param function_name: The name or ARN of the Lambda function,
               version, or alias.
               Function name – my-function (name-only)
               Function name – my-function:v1 (with alias)
               Function ARN –
               arn:aws:lambda:us-west-2:123456789012:function:my-function
               Partial ARN – 123456789012:function:my-function
               You can append a version number or alias to any of the
               formats.
        :param kwargs: Any other param passed to the underlying boto3.
        :return: lambda invoke response converted to python dict.
        :raise LambdaError: If operation fails.
        """

        try:
            lambda_response = self._client.invoke(FunctionName=function_name, **kwargs)

            # Convert lambda response Payload from StreamingBody to
            # python dict
            lambda_response_payload = json.loads(lambda_response['Payload'].read().decode())

            # Replacing the StreamingBody with the python dict
            lambda_response['Payload'] = lambda_response_payload

            return lambda_response

        except botocore.exceptions.ClientError as ex:
            raise exceptions.LambdaError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.LambdaError(str(ex)) from None
