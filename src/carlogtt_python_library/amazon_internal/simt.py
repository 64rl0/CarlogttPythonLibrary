# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/amazon_internal/simt.py
# Created 10/25/23 - 3:55 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import functools
import logging
import warnings
from collections.abc import Generator
from typing import Any, Optional

# Third Party Library Imports
import boto3
import botocore.config
import botocore.exceptions

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'SimT',
    'SimTicketHandler',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
TicketyClient = Any


class SimT:
    """
    A handler class for the TicketyPythonSdk.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    Internal Amazon API
    https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicketingSystemAccessGrant

    :param aws_region_name: The name of the AWS region where the
           service is to be used. This parameter is required to
           configure the AWS client.
    :param aws_account_id: The AWS Account ID name for the target
           ticketing system. Use “default” unless you are targeting
           an integ environment.
           https://w.amazon.com/bin/view/IssueManagement/SIMTicketing/TicketyAPI/FAQ/#HCanIuseTicketyAPItoaccessintegdata3F
    :param ticketing_system_name: The Ticketing System for the
           target ticketing system. Use “default” unless you are
           targeting an integ environment.
           https://w.amazon.com/bin/view/IssueManagement/SIMTicketing/TicketyAPI/FAQ/#HCanIuseTicketyAPItoaccessintegdata3F
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
        aws_account_id: str = "default",
        ticketing_system_name: str = "default",
    ) -> None:
        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_session_token = aws_session_token
        self._caching = caching
        self._cache: dict[str, Any] = dict()
        self._aws_account_id = aws_account_id
        self._ticketing_system_name = ticketing_system_name
        self._aws_tickety_region_name = "global"
        self._aws_service_name = "tickety"
        self._aws_endpoint_url = "https://global.api.tickety.amazon.dev"
        self._client_parameters = client_parameters if client_parameters else dict()

    @property
    def _client(self) -> TicketyClient:
        if self._caching:
            if self._cache.get('client') is None:
                self._cache['client'] = self._get_boto_tickety_client()
            return self._cache['client']

        else:
            return self._get_boto_tickety_client()

    @functools.cached_property
    def _tickety_client_config(self):
        """
        The botocore config is where you can set a number of other
        overrides for your client such as the RetryMode and Client Side
        Timeouts. You should evaluate these based on the needs of your
        system and set them accordingly.

        Importantly this includes the custom signer that uses AWS
        SigV4a. This allows for your requests to the TicketyService to
        succeed regardless of the region being called. This fact is
        important because global.api.tickety.amazon.dev used below
        allows you to call the service based on latency-based DNS
        routing. More importantly this will give the Tickety team the
        leverage to redirect traffic away from an unhealthy region.
        Should an outage occur your traffic will automatically be
        weighted away from a negatively impacted region to one that is
        healthy. So as long as you use a global signer, your requests
        will succeed. By contrast, if you are using a request that is
        signed for a single region to call a region-specific endpoint,
        then your system will be vulnerable to outages in that region
        and will not be able to take advantage of the multi-region
        nature of the global endpoint.
        """

        return botocore.config.Config(signature_version="v4a", retries={"mode": "adaptive"})

    def _get_boto_tickety_client(self) -> TicketyClient:
        """
        Create a low level tickety client.

        :return: A tickety client.
        :raise: SimTError if function call fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_tickety_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
            )
            client = boto_session.client(  # type: ignore
                service_name=self._aws_service_name,
                endpoint_url=self._aws_endpoint_url,
                config=self._tickety_client_config,
                **self._client_parameters,
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response))

        except Exception as ex:
            raise exceptions.SimTError(str(ex))

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
            raise exceptions.SimTError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['client'] = None

    def get_tickets(self, filters: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
        """
        Returns an iterable of ticketIds.

        :param filters:
        :return: Returns an iterable of ticketIds.
        :raise: SimTError if function call fails.
        """

        payload: dict[str, Any] = {'filters': filters}
        next_token = 'valid_string'

        try:
            while next_token:
                tickety_response = self._list_tickets_with_retry(payload)

                next_token = tickety_response.get('nextToken', '')
                payload.update({'nextToken': next_token})

                for ticket_data in tickety_response.get('ticketSummaries', []):
                    yield ticket_data

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SimTError(str(ex)) from None

    @utils.retry(Exception)
    def _list_tickets_with_retry(self, payload: dict[str, Any]):
        """
        Perform the `list_tickets` operation with automatic retries for
        transient exceptions.

        :param payload:
            The parameters to pass to the underlying client's
            `list_tickets` call. Typically includes filters,
            nextToken, etc.
        :return:
            The raw response dictionary from `list_tickets`, which
            includes a potential `nextToken` and a list of ticket
            summaries in the `ticketSummaries` key.
        """

        return self._client.list_tickets(
            awsAccountId=self._aws_account_id,
            ticketingSystemName=self._ticketing_system_name,
            **payload,
        )

    @utils.retry(exceptions.SimTError)
    def get_ticket_details(
        self,
        ticket_id: str,
    ):
        """
        Retrieves a ticket from the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/GetTicket

        :param ticket_id: The ticket ID.
        :return:
        :raise: SimTError if function call fails.
        """

        try:
            tickety_response = self._client.get_ticket(
                ticketId=ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
            )

            try:
                return tickety_response['ticket']

            except KeyError as ex_inner:
                raise exceptions.SimTError(str(ex_inner))

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SimTError(str(ex)) from None

    @utils.retry(exceptions.SimTError)
    def update_ticket(self, ticket_id: str, payload: dict[str, Any]) -> None:
        """
        Updates a ticket in the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicket

        :param ticket_id: The ticket ID.
        :param payload:
        :return:
        :raise: SimTError if function call fails.
        """

        try:
            response = self._client.update_ticket(
                ticketId=ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
                update=payload,
            )

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SimTError(str(ex)) from None

        if (
            not isinstance(response, dict)
            or response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200
        ):
            raise exceptions.SimTError(str(response))

    @utils.retry(exceptions.SimTError)
    def create_ticket_comment(
        self,
        ticket_id: str,
        comment: str,
        thread_name: str = "CORRESPONDENCE",
        content_type: str = "text/amz-markdown-sim",
    ) -> str:
        """
        Updates a ticket in the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicket

        :param ticket_id: The ticket ID.
        :param thread_name: Must be one of these 3:
               "CORRESPONDENCE" "WORKLOG" "ANNOUNCEMENTS".
               Auto default to "CORRESPONDENCE".
        :param comment: The comment to post.
               Between 3 and 60_000 characters.
        :param content_type: Must be one of these 2:
               "text/amz-markdown-sim" "text/plain".
               Auto default to "text/amz-markdown-sim".
        :return: The SIM-T commentId as a string.
        :raise: SimTError if function call fails.
        """

        payload = {
            'threadName': thread_name,
            'message': comment,
            'contentType': content_type,
        }

        try:
            tickety_response = self._client.create_ticket_comment(
                ticketId=ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
                **payload,
            )

            try:
                return tickety_response['commentId']

            except KeyError as ex_inner:
                raise exceptions.SimTError(str(ex_inner))

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SimTError(str(ex)) from None

    @utils.retry(exceptions.SimTError)
    def create_ticket(self, ticket_data: dict[str, Any]) -> str:
        """
        Create a ticket in the ticketing system and return the
        ticket ID.

        :param ticket_data:
        :return: The ticket ID.
        """

        try:
            ticket_response = self._client.create_ticket(
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
                ticket=ticket_data,
            )

            try:
                return ticket_response['id']

            except KeyError as ex_inner:
                raise exceptions.SimTError(str(ex_inner))

        except botocore.exceptions.ClientError as ex:
            raise exceptions.SimTError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.SimTError(str(ex)) from None


class SimTicketHandler(SimT):
    """
    DEPRECATED: Please use SimT instead.
    This subclass only exists for backward compatibility.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "[DEPRECATED] 'SimTicketHandler' is deprecated. Please use 'SimT' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
