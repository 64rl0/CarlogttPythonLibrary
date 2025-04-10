# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/aws_sig_v4_requests.py
# Created 4/8/25 - 1:34 PM UK Time (London) by carlogtt
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
import json
import logging
import urllib.parse
from typing import Any

# Third Party Library Imports
import boto3
import botocore.auth
import botocore.awsrequest
import requests

# Local Folder (Relative) Imports
from .. import exceptions
from . import decorators

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'AwsSigV4Session',
    'AwsSigV4RequestMethod',
    'AwsSigV4Protocol',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class AwsSigV4Protocol(enum.Enum):
    """
    Enum representing supported protocol types for the session.
    """

    RPCv0 = enum.auto()
    RPCv1 = enum.auto()


class AwsSigV4RequestMethod(enum.Enum):
    """
    Enum class for the different types of requests that can be made to
    the PipelinesAPI.

    Each enum value represents a specific type of request, such as
    GET, POST, PUT, or DELETE.
    """

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class AwsSigV4Session(requests.Session):
    """
    Custom session that signs all outgoing HTTP requests using AWS
    Signature Version 4.

    :param region_name: AWS region where the service is hosted
        (e.g., 'us-west-2').
    :param service_name: Name of the AWS service
        (e.g., 'execute-api').
    :param boto_session: Boto3 session that includes credentials.
    :param protocol: AwsSigV4Protocol version for the request headers.
    :raises AwsSigV4SessionError: If credentials are missing or
        HTTP response fails.
    """

    def __init__(
        self,
        region_name: str,
        service_name: str,
        boto_session: boto3.Session,
        protocol: AwsSigV4Protocol,
    ):
        super().__init__()
        self._region_name = region_name
        self._service_name = service_name
        self._boto_session = boto_session
        self._protocol = protocol

    def prepare_request(self, request: requests.Request):
        """
        Prepares and signs a request with AWS Signature Version 4.

        :param request: The request object to be prepared and signed.
        :return: The prepared request with SigV4 headers.
        :raises AwsSigV4SessionError: If the specified protocol is not
            supported.
        """

        # Base headers
        headers_base = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
        }

        module_logger.debug("Preparing request headers")

        if self._protocol == AwsSigV4Protocol.RPCv0:
            headers_protocol: dict[str, str] = {}

        elif self._protocol == AwsSigV4Protocol.RPCv1:
            headers_protocol = {
                "Content-Encoding": "amz-1.0",
            }

        else:
            raise exceptions.AwsSigV4SessionError(f"Unsupported protocol: {self._protocol}")

        # Update headers with protocol-specific headers
        headers = {**headers_base, **headers_protocol}
        request.headers.update(headers)

        # Let requests do its normal prep
        # e.g. (Cookie handling, redirects, etc.)
        prepared = super().prepare_request(request)

        # Get signed headers from SigV4Auth
        signed_headers = self._get_signed_headers(request=prepared)

        # Inject signed headers into the request
        prepared.headers.update(signed_headers)

        module_logger.debug(f"request prepared: {prepared.__dict__}")

        return prepared

    @decorators.retry(exceptions.AwsSigV4SessionError)
    def request(self, *args, **kwargs) -> requests.Response:
        """
        Sends a signed HTTP request and checks for successful response
        status.

        :param args: Positional arguments passed to
            `requests.Session.request()`.
        :param kwargs: Keyword arguments to configure the request.
        :return: The HTTP response object.
        :raises AwsSigV4SessionError: If the HTTP status code indicates
            failure.
        """

        module_logger.debug("Serializing request data")
        if kwargs.get('data', None) and isinstance(kwargs['data'], dict):
            kwargs['data'] = self._serialize_request_data(kwargs['data'])

        # Ensure the following kwargs are set
        kwargs['timeout'] = kwargs.get('timeout', 300)
        kwargs['allow_redirects'] = kwargs.get('allow_redirects', True)

        # Let requests do its normal request
        # e.g. (Cookie handling, redirects, etc.)
        response = super().request(*args, **kwargs)

        # Retry if not successful
        if response.status_code < 200 or response.status_code >= 300:
            msg = f"HTTP Status Code: {response.status_code} - {response.text}"
            module_logger.debug(msg)
            raise exceptions.AwsSigV4SessionError(msg)

        # Protocol RPCv0 always returns 200 as status code
        # even if the request fails
        if self._protocol is AwsSigV4Protocol.RPCv0:
            # keywords indicating failure of the Coral API
            keyword_to_check = ['exception']

            try:
                response_obj = response.json()
                __type = response_obj['Output']['__type']

                if any(keyword in __type.casefold() for keyword in keyword_to_check):
                    message = response_obj['Output']['message']
                    raise exceptions.AwsSigV4SessionError(message)

            except Exception:
                msg = f"Exception raised from Coral API: {response.text}"
                module_logger.debug(msg)
                raise exceptions.AwsSigV4SessionError(msg)

        return response

    def _serialize_request_data(self, data: dict[str, Any]) -> bytes:
        """
        Serializes the request data into utf-8 encoded bytes.

        :param data: The request data to be serialized.
        :return: The serialized utf-8 encoded bytes.
        """

        data_serialized = json.dumps(
            data, indent=None, separators=(",", ":"), ensure_ascii=False
        ).encode('utf-8')

        return data_serialized

    def _get_signed_headers(self, request: requests.PreparedRequest) -> dict[str, str]:
        """
        Generates AWS SigV4 signed headers for a given prepared request.

        :param request: The HTTP request to sign.
        :return: A dictionary of SigV4 authentication headers.
        :raises AwsSigV4SessionError: If no valid credentials are found.
        """

        if not (credentials := self._boto_session.get_credentials()):
            msg = "No AWS credentials found in the Boto3 session!"
            module_logger.error(msg)
            raise exceptions.AwsSigV4SessionError(msg)

        # Convert the requests Request into a botocore
        # AWSRequest so SigV4Auth can sign it.
        aws_request = botocore.awsrequest.AWSRequest(
            method=request.method,
            url=request.url,
            data=request.body,
        )
        module_logger.debug(f"request headers before sigv4: {dict(aws_request.headers.items())}")

        # Ensure the Host header is set properly
        parsed_url = urllib.parse.urlparse(str(request.url)).netloc.split(':')[0]
        aws_request.headers['Host'] = parsed_url

        # Actually sign the request
        sig_v4 = botocore.auth.SigV4Auth(
            credentials=credentials,
            service_name=self._service_name,
            region_name=self._region_name,
        )
        sig_v4.add_auth(aws_request)
        module_logger.debug(f"request headers after sigv4: {dict(aws_request.headers.items())}")

        signed_headers = dict(aws_request.headers.items())

        return signed_headers
