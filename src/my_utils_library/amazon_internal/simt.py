# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# simt.py
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
import time
from typing import Any, Optional

# Third Party Library Imports
import boto3
import botocore.config

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'SimTicketHandler',
]


class SimTicketHandler:
    """
    A handler class for the TicketyPythonSdk.
    """

    def __init__(
        self,
        ticket_id: str,
        aws_region_name: str,
        aws_account_id: str = "default",
        ticketing_system_name: str = "default",
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        """
        aws_profile and aws_region are injected locally for local
        development testing through Brazil. When running on NAWS this
        env variable is not set.

        Internal Amazon API
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicketingSystemAccessGrant
        """

        # The AWS Account ID name for the target ticketing system.
        # Use “Default” unless you are targeting an integ environment.
        # https://w.amazon.com/bin/view/IssueManagement/SIMTicketing/TicketyAPI/FAQ/#HCanIuseTicketyAPItoaccessintegdata3F
        self._aws_account_id = aws_account_id

        # The Ticketing System for the target ticketing system.
        # Use “Default” unless you are targeting an integ environment.
        # https://w.amazon.com/bin/view/IssueManagement/SIMTicketing/TicketyAPI/FAQ/#HCanIuseTicketyAPItoaccessintegdata3F
        self._ticketing_system_name = ticketing_system_name

        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_service_name = "tickety"
        self._aws_endpoint_url = "https://global.api.tickety.amazon.dev"

        self.ticket_id = ticket_id

    @property
    def _client(self):
        return self._get_tickety_client()

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

    def _get_tickety_client(self):
        """
        Create a low level tickety client.

        :return: A tickety client.
        :raise: SimTHandlerError if function call fails.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
            )
            client = boto_session.client(  # type: ignore
                service_name=self._aws_service_name,
                endpoint_url=self._aws_endpoint_url,
                config=self._tickety_client_config,
            )

            return client

        except Exception as ex:
            raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")

    def get_ticket_details(self):
        """
        Retrieves a ticket from the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/GetTicket

        :return
        :raise: SimTHandlerError if function call fails.
        """

        try:
            tickety_response = self._client.get_ticket(
                ticketId=self.ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
            )

            try:
                return tickety_response['ticket']

            except KeyError as ex:
                raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")

        except Exception as ex:
            raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")

    def update_ticket(self, payload: dict[str, Any]) -> None:
        """
        Updates a ticket in the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicket

        :param payload:
        :return: Nothing.
        :raise: SimTHandlerError if function call fails.
        """

        try:
            self._client.update_ticket(
                ticketId=self.ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
                update=payload,
            )

        except Exception as ex:
            raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")

        time.sleep(0.5)

        # Retrieve ticket to assert all the values have been updated
        # successfully
        ticket_updated = self.get_ticket_details()

        # Prepare for exception
        exception_message = ""

        for key, value in payload.items():
            try:
                assert (
                    payload[key] == ticket_updated[key]
                ), f"Value for '{key}' has not been updated"

            except AssertionError as ex:
                exception_message += str(ex) + " - "

        if exception_message:
            raise exceptions.SimTHandlerError(exception_message)

    def create_ticket_comment(
        self,
        comment: str,
        thread_name: str = "CORRESPONDENCE",
        content_type: str = "text/amz-markdown-sim",
    ) -> str:
        """
        Updates a ticket in the ticketing system.

        Internal Amazon API:
        https://prod.artifactbrowser.brazil.aws.dev/api/v1/packages/TicketyServiceModel/versions/1.0.41444.0/platforms/AL2_aarch64/flavors/DEV.STD.PTHREAD/brazil-documentation/redoc/index.html#operation/UpdateTicket

        :param thread_name: Must be one of these 3:
               "CORRESPONDENCE" "WORKLOG" "ANNOUNCEMENTS".
               Auto default to "CORRESPONDENCE".
        :param comment: The comment to post.
               Between 3 and 60_000 characters.
        :param content_type: Must be one of these 2:
               "text/amz-markdown-sim" "text/plain".
               Auto default to "text/amz-markdown-sim".
        :return: The SIM-T commentId as a string.
        :raise: SimTHandlerError if function call fails.
        """

        payload = {
            'threadName': thread_name,
            'message': comment,
            'contentType': content_type,
        }

        try:
            tickety_response = self._client.create_ticket_comment(
                ticketId=self.ticket_id,
                awsAccountId=self._aws_account_id,
                ticketingSystemName=self._ticketing_system_name,
                **payload,
            )

            try:
                return tickety_response['commentId']

            except KeyError as ex:
                raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")

        except Exception as ex:
            raise exceptions.SimTHandlerError(f"Operation failed! - {str(ex)}")
