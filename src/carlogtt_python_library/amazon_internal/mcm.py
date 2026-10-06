# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/mcm.py
# Created 6/9/26 - 10:32 AM UK Time (London) by carlogtt

"""
This module provides a client for the Amazon MCM (Modeled Change
Management) API.

It wraps the ModeledCmApiService Coral client behind a single handler
with the library's standard credential/caching ergonomics. The
underlying service is region-locked to us-east-1; only the stage
(beta / prod) selects the endpoint.
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
from typing import Any, Optional, cast

# Third Party Library Imports
import boto3
import botocore.exceptions
from com.amazon.modeledcmapi.datatypes.identifiers.cmfriendlyidentifier import (  # type: ignore
    CmFriendlyIdentifier,
)
from com.amazon.modeledcmapi.modeledcmapiservice import ModeledCmApiServiceClient  # type: ignore
from com.amazon.modeledcmapi.requests.cmrequests.getcmrequest import GetCmRequest  # type: ignore
from coral import coralrpc

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Mcm',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
# The Coral client attaches its operations dynamically and ships no
# py.typed, so a precise type is not available; alias to Any like the
# other generated-client wrappers in this package (see mirador.py).
McmClient = Any


class Mcm:
    """
    A handler class for the Amazon MCM (Modeled Change Management) API.

    It wraps the ModeledCmApiService Coral client and includes an option
    to cache the client session to minimize the number of API calls.

    The underlying service is region-locked to ``us-east-1``; the
    ``aws_region_name`` argument selects the region used to resolve AWS
    credentials, while ``mcm_stage`` selects the service endpoint.

    Internal Amazon API:
    https://w.amazon.com/bin/view/ChangeManagement/MCM/API/UserGuides/IntegrationGuide

    :param aws_region_name: The name of the AWS region used to resolve
           credentials for SigV4 signing. This parameter is required to
           configure the AWS session.
    :param mcm_stage: The MCM service stage to target, must be 'beta'
           or 'prod'. Defaults to 'prod'.
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
           will be passed to the orchestrator constructor.
    :raise McmError: If ``mcm_stage`` is not 'beta' or 'prod'.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        mcm_stage: str = 'prod',
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        caching: bool = False,
        client_parameters: Optional[dict[str, Any]] = None,
    ) -> None:
        # The MCM service is only reachable through these regional proxy
        # endpoints; the service itself is region-locked to us-east-1.
        mcm_endpoints = {
            "beta": "https://modeled-cm-api-service-proxy-beta.us-east-1.amazonaws.com",
            "prod": "https://modeled-cm-api-service-proxy.us-east-1.amazonaws.com",
        }

        if mcm_stage not in mcm_endpoints:
            raise exceptions.McmError(
                f"Invalid mcm_stage {mcm_stage!r}. Must be one of {sorted(mcm_endpoints)}."
            )

        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_session_token = aws_session_token
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._mcm_stage = mcm_stage
        self._mcm_aws_region = "us-east-1"
        self._mcm_aws_service = "modeled-cm-api-service"
        self._mcm_endpoint_url = mcm_endpoints[mcm_stage]
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> McmClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_mcm_client()
            return cast(McmClient, self._cache['client'])

        else:
            return self._get_mcm_client()

    def _get_mcm_client(self) -> McmClient:
        """
        Create a low level MCM client.

        Resolves AWS credentials through a boto3 session and builds a
        SigV4-signed CoralRPC orchestrator pointed at the configured
        stage endpoint.

        :return: A ModeledCmApiServiceClient.
        :raise McmError: If client construction fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
            )

            credentials = boto_session.get_credentials()
            if credentials is None:
                raise exceptions.McmError("Failed to resolve AWS credentials.")
            frozen_credentials = credentials.get_frozen_credentials()

            # access_key / secret_key are typed Optional by boto3-stubs;
            # without both we can't SigV4-sign, so fail loudly rather
            # than hand the orchestrator a None to encode.
            if not frozen_credentials.access_key or not frozen_credentials.secret_key:
                raise exceptions.McmError("Resolved AWS credentials are missing an access key.")

            orchestrator = coralrpc.new_orchestrator(
                endpoint=self._mcm_endpoint_url,
                timeout=30,
                aws_region=self._mcm_aws_region,
                aws_service=self._mcm_aws_service,
                aws_access_key=frozen_credentials.access_key.encode("utf-8"),
                aws_secret_key=frozen_credentials.secret_key.encode("utf-8"),
                aws_security_token=(
                    frozen_credentials.token.encode("utf-8") if frozen_credentials.token else None
                ),
                signature_algorithm="v4",
                **self._client_parameters,
            )

            return ModeledCmApiServiceClient(orchestrator)

        except botocore.exceptions.ClientError as ex:
            raise exceptions.McmError(str(ex.response))

        except Exception as ex:
            raise exceptions.McmError(str(ex))

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached client, if caching is enabled.

        This method allows manually invalidating the cached client,
        forcing a new client instance to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise McmError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.McmError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    @utils.retry(exception_to_check=exceptions.McmError)
    def get_mcm(self, mcm_id: str) -> dict[str, Any]:
        """
        Retrieve an MCM (change management record) by its friendly ID.

        :param mcm_id: The MCM friendly identifier, e.g.
            ``"MCM-12345678"``.
        :return: A dictionary describing the MCM with keys ``mcm_id``,
            ``uuid``, ``url``, ``title``, ``description``, ``status``,
            ``requester``, ``technician``, ``scheduled_start`` and
            ``scheduled_end``.
        :raise McmError: If the request fails or the MCM is not found.
        """

        try:
            cm_friendly_identifier = CmFriendlyIdentifier(friendly_id=mcm_id)
            request = GetCmRequest(cm_friendly_identifier=cm_friendly_identifier)

            response = self._client.get_cm(request)
            cm = response.cm

            friendly_id = cm.cm_friendly_identifier.friendly_id

            mcm = {
                'mcm_id': friendly_id,
                'uuid': cm.cm_identifier.uuid,
                'url': f"https://mcm.amazon.com/cms/{friendly_id}",
                'title': cm.cm_overview.title,
                'description': cm.cm_overview.description,
                'status': cm.status_and_approvers.cm_status,
                'requester': cm.cm_overview.requester,
                'technician': cm.cm_overview.technician,
                'scheduled_start': cm.cm_overview.scheduled_start,
                'scheduled_end': cm.cm_overview.scheduled_end,
            }

            return mcm

        except botocore.exceptions.ClientError as ex:
            raise exceptions.McmError(str(ex.response)) from None

        except exceptions.McmError:
            raise

        except Exception as ex:
            raise exceptions.McmError(str(ex)) from None
