# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/bindle.py
# Created 4/8/25 - 1:31 PM UK Time (London) by carlogtt
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
import boto3
import botocore.auth
import botocore.awsrequest
import botocore.config
import botocore.exceptions

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Bindle',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
BindleClient = utils.AwsSigV4Session


class Bindle:
    """
    A handler class for the BindleAPI.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    Internal Amazon API
    https://coral.amazon.com/BindleService/Alpha/model/com.amazon.bindle.coral.calls%23BindleService/com.amazon.bindle.coral.calls%23AaaEnableSoftwareApplication?endpoint=http%3A%2F%2Fbindle-service.integ.amazon.com%3A80

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
        self._aws_bindle_region_name = "us-east-1"
        self._aws_service_name = "BindleService"
        self._aws_endpoint_url = "https://bindle-service-awsauth.us-east-1.amazonaws.com"
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> BindleClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_bindle_client()
            return self._cache['client']

        else:
            return self._get_bindle_client()

    def _get_bindle_client(self) -> BindleClient:
        """
        Create a low level bindle client.

        :return: A BindleClient.
        :raise: BindleError if function call fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
            )

            client = utils.AwsSigV4Session(
                region_name=self._aws_bindle_region_name,
                service_name=self._aws_service_name,
                boto_session=boto_session,
                protocol=utils.AwsSigV4Protocol.RPCv0,
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.BindleError(str(ex.response))

        except Exception as ex:
            raise exceptions.BindleError(str(ex))

    def _send_bindle_api_request(
        self, request_method: utils.AwsSigV4RequestMethod, operation: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Bindle API.

        """
        headers = {
            "X-Amz-Target": f"com.amazon.bindle.coral.calls.BindleService.{operation}",
        }

        try:
            response = self._client.request(
                method=request_method.value,
                url=self._aws_endpoint_url,
                headers=headers,
                data=payload,
            )

            response_obj = response.json()

            return response_obj

        except Exception as ex:
            raise exceptions.BindleError(str(ex)) from None

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise BindleError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.BindleError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    def describe_resource(self, resource_id: str) -> dict[str, Any]:
        """
        Returns the structure of a resource based on its ID.

        :param resource_id: The id of the resource.
        :return: The resource structure.
        :raise: BindleError if function call fails.
        """

        operation = "DescribeResource"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "resourceId": resource_id,
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def describe_package(self, package_name: str) -> dict[str, Any]:
        """
        Returns the structure of a package based on its name.

        :param package_name: The name of the package.
        :return: The package structure.
        :raise: BindleError if function call fails.
        """

        operation = "DescribeResource"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "resourceName": package_name,
                "resourceType": {
                    "namespaceName": "builder-tools",
                    "resourceTypeName": "package",
                },
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def describe_versionset_group(self, versionset_group_name: str) -> dict[str, Any]:
        """
        Returns the structure of a versionset group based on its name.

        :param versionset_group_name: The name of the versionset group.
        :return: The versionset group structure.
        :raise: BindleError if function call fails.
        """

        operation = "DescribeResource"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "resourceName": versionset_group_name,
                "resourceType": {
                    "namespaceName": "brazil",
                    "resourceTypeName": "version-set-group",
                },
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def describe_material_set(self, material_set_name: str) -> dict[str, Any]:
        """
        Returns the structure of a material set based on its name.

        :param material_set_name: The name of the material set.
        :return: The material set structure.
        :raise: BindleError if function call fails.
        """

        operation = "DescribeResource"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "resourceName": material_set_name,
                "resourceType": {
                    "namespaceName": "odin",
                    "resourceTypeName": "materialset",
                },
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def describe_software_application(self, software_application_name: str) -> dict[str, Any]:
        """
        Returns the structure of a software application based on its
        name.

        :param software_application_name: The name of the software
            application.
        :return: The software application structure.
        :raise: BindleError if function call fails.
        """

        operation = "DescribeResource"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "resourceName": software_application_name,
                "resourceType": {
                    "namespaceName": "Bindle",
                    "resourceTypeName": "SoftwareApp",
                },
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def find_bindles_by_owner_with_team_id(self, team_id: str) -> dict[str, Any]:
        """
        Returns all the bindles owned by a team.

        :param team_id: The id of the team.
        :return: The bindles owned by the team.
        :raise: BindleError if function call fails.
        """

        operation = "FindBindlesByOwner"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "identifier": {
                    "__type": "com.amazon.bindle.coral.types#TeamId",
                    "identifier": team_id,
                },
                "pagination": {"limit": 200},
                "includePersonalBindles": False,
                "allowUnsortedResults": True,
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def find_bindles_by_owner_with_alias(self, alias: str) -> dict[str, Any]:
        """
        Returns all the bindles owned by a user.

        :param alias: The alias of the user.
        :return: The bindles owned by the user.
        :raise: BindleError if function call fails.
        """

        operation = "FindBindlesByOwner"

        payload = {
            "Service": "com.amazon.bindle.coral.calls#BindleService",
            "Operation": f"com.amazon.bindle.coral.calls#{operation}",
            "Input": {
                "identifier": {
                    "__type": "com.amazon.bindle.coral.types#Username",
                    "identifier": alias,
                },
                "pagination": {"limit": 200},
                "includePersonalBindles": False,
                "allowUnsortedResults": True,
            },
        }

        response = self._send_bindle_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response
