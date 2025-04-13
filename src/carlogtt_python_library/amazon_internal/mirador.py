# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/mirador.py
# Created 3/24/25 - 2:13 PM UK Time (London) by carlogtt
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
from typing import Any, Optional

# Third Party Library Imports
import aws_mirador_api_service_python_client_utils  # type: ignore
import boto3
import botocore.config
import botocore.exceptions

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    "Mirador",
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
MiradorClient = Any


class Mirador:
    """
    A handler class for the Mirador API.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    Internal Amazon API
    https://prod.artifactbrowser.brazil.aws.dev/packages/AWSMiradorAPIServiceModel/versions/1.0.12187.0/platforms/AL2_x86_64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html

    :param aws_region_name: The name of the AWS region where the
           service is to be used. This parameter is required to
           configure the AWS client.
    :param mirador_role_arn: The ARN of the role you received after
           onboarding.
    :param mirador_external_id: The external ID you used for onboarding.
    :param mirador_api_key: The Mirador API key to use.
    :param mirador_stage: Stage name, must be 'beta', 'gamma', 'prod'.
           Defaults to 'prod'
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
        mirador_role_arn: str,
        mirador_external_id: str,
        mirador_api_key: str,
        mirador_stage: str = 'prod',
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
        self._mirador_role_arn = mirador_role_arn
        self._mirador_external_id = mirador_external_id
        self._mirador_api_key = mirador_api_key
        self._mirador_stage = mirador_stage
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> MiradorClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_mirador_client()
            return self._cache['client']

        else:
            return self._get_boto_mirador_client()

    def _get_boto_mirador_client(self) -> MiradorClient:
        """
        Create a low level mirador client.

        :return: A mirador client.
        :raise: MiradorError if function call fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
            )
            client = aws_mirador_api_service_python_client_utils.new_mirador_client(
                stage=self._mirador_stage,
                region=self._aws_region_name,
                role_arn=self._mirador_role_arn,
                external_id=self._mirador_external_id,
                session=boto_session,
                **self._client_parameters,
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.MiradorError(str(ex.response))

        except Exception as ex:
            raise exceptions.MiradorError(str(ex))

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise SimTError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.MiradorError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    @utils.retry(exceptions.MiradorError)
    def get_finding_attributes(self) -> list[tuple[str, str]]:
        """
        Get the list of finding attributes.

        :return: A list of tuples containing the attribute name and
            type.
        :raise: MiradorError if function call fails.
        """

        try:
            response = self._client.get_finding_attributes(api_key=self._mirador_api_key)

            attributes = [(attrib.name, attrib.type) for attrib in response.attributes]

            return attributes

        except botocore.exceptions.ClientError as ex:
            raise exceptions.MiradorError(str(ex.response))

        except Exception as ex:
            raise exceptions.MiradorError(str(ex))

    @utils.retry(exceptions.MiradorError)
    def get_resource_attributes(self) -> list[tuple[str, str]]:
        """
        Get the list of resource attributes.

        :return: A list of tuples containing the attribute name and
            type.
        :raise: MiradorError if function call fails.
        """

        try:
            response = self._client.get_resource_attributes(api_key=self._mirador_api_key)

            attributes = [(attrib.name, attrib.type) for attrib in response.attributes]

            return attributes

        except botocore.exceptions.ClientError as ex:
            raise exceptions.MiradorError(str(ex.response))

        except Exception as ex:
            raise exceptions.MiradorError(str(ex))
