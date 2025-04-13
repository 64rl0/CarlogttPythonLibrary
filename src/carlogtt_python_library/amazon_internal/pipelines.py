# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/pipelines.py
# Created 4/7/25 - 8:43 AM UK Time (London) by carlogtt
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
import enum
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
    'Pipelines',
    'TargetType',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
PipelinesClient = utils.AwsSigV4Session


class TargetType(enum.Enum):
    """
    Enum class for the different types of targets that can be used in
    the PipelinesAPI.

    Targets represent instances in underlying systems, like packages,
    code deploy apps, etc.
    """

    BATS = 'BATS'
    CD = 'CD'
    CF = 'CF'
    DG = 'DG'
    ENV = 'ENV'
    GEN = 'GEN'
    OS = 'OS'
    PKG = 'PKG'
    VS = 'VS'


class Pipelines:
    """
    A handler class for the PipelinesAPI.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    Internal Amazon API
    https://us-west-2.prod.pipelines-api.builder-tools.aws.dev/model/index.html

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
        self._aws_pipelines_region_name = "us-west-2"
        self._aws_service_name = "pipelines-api"
        self._aws_endpoint_url = "https://us-west-2.prod.pipelines-api.builder-tools.aws.dev"
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> PipelinesClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_pipelines_client()
            return self._cache['client']

        else:
            return self._get_pipelines_client()

    def _get_pipelines_client(self) -> PipelinesClient:
        """
        Create a low level pipelines client.

        :return: A PipelinesClient.
        :raise: PipelinesError if function call fails.
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
                region_name=self._aws_pipelines_region_name,
                service_name=self._aws_service_name,
                boto_session=boto_session,
                protocol=utils.AwsSigV4Protocol.RPCv1,
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.PipelinesError(str(ex.response))

        except Exception as ex:
            raise exceptions.PipelinesError(str(ex))

    def _send_pipelines_api_request(
        self, request_method: utils.AwsSigV4RequestMethod, operation: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Pipelines API.

        """

        headers = {
            "X-Amz-Target": (
                f"com.amazon.pipelinesapinativeservice.PipelinesAPINativeService.{operation}"
            ),
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
            raise exceptions.PipelinesError(str(ex)) from None

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise PipelinesError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.PipelinesError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    def get_pipeline_structure(
        self, *, pipeline_name: Optional[str] = None, pipeline_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Returns the structure of a pipeline based on it’s name or ID.

        :param pipeline_name: The name of the pipeline.
        :param pipeline_id: The id of the pipeline.
        :return: The pipeline structure.
        :raise: PipelinesError if function call fails.
        """

        if pipeline_name and pipeline_id:
            raise exceptions.PipelinesError("Pipeline name and ID are mutually exclusive!")

        if pipeline_name:
            payload = {"pipelineName": pipeline_name}
        elif pipeline_id:
            payload = {"pipelineId": pipeline_id}
        else:
            raise exceptions.PipelinesError("Pipeline name or ID is required!")

        operation = "GetPipelineStructure"

        response = self._send_pipelines_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response

    def get_pipelines_containing_target(
        self, target_name: str, target_type: TargetType, in_primary_pipeline: bool
    ) -> dict[str, Any]:
        """
        Returns a list of pipeline names which contain the provided
        target.

        :param target_name: The name of the target.
        :param target_type: The type of the target.
        :param in_primary_pipeline: Whether the target is in the primary
            pipeline.
        :return: The list of pipelines containing the target.
        :raise: PipelinesError if function call fails.
        """

        payload = {
            "targetName": target_name,
            "targetType": target_type.value,
            "inPrimaryPipeline": in_primary_pipeline,
        }

        operation = "GetPipelinesContainingTarget"

        response = self._send_pipelines_api_request(
            request_method=utils.AwsSigV4RequestMethod.POST, operation=operation, payload=payload
        )

        return response
