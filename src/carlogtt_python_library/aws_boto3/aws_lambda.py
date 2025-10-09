# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/aws_boto3/aws_lambda.py
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
from typing import Any, Optional

# Third Party Library Imports
import botocore.exceptions
import mypy_boto3_lambda
from mypy_boto3_lambda import type_defs

# Local Folder (Relative) Imports
from .. import exceptions
from . import aws_service_base

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Lambda',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
LambdaClient = mypy_boto3_lambda.client.LambdaClient


class Lambda(aws_service_base.AwsServiceBase[LambdaClient]):
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
        super().__init__(
            aws_region_name=aws_region_name,
            aws_profile_name=aws_profile_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            caching=caching,
            client_parameters=client_parameters,
            aws_service_name="lambda",
            exception_type=exceptions.LambdaError,
        )

    def invoke(self, function_name: str, **kwargs) -> type_defs.InvocationResponseTypeDef:
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

        invoke_payload: type_defs.InvocationRequestTypeDef = {
            'FunctionName': function_name,
            **kwargs,  # type: ignore
        }

        try:
            lambda_response = self._client.invoke(**invoke_payload)

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
