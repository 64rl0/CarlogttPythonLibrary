# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/aws_boto/cloud_front.py
# Created 2/8/24 - 1:07 PM UK Time (London) by carlogtt
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
import time
from typing import Any, Optional

# Third Party Library Imports
import boto3

# Local Folder (Relative) Imports
from .. import exceptions

# TODO: uncomment this when brazil
#       supports mypy_boto3_cloudfront.client
# from mypy_boto3_cloudfront.client import CloudFrontClient


# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'CloudFront',
]

# Setting up logger for current module
# module_logger =

# Type aliases
#

# TODO: absolutely remove this when brazil
#       supports mypy_boto3_cloudfront.client
CloudFrontClient = Any


class CloudFront:
    """
    The CloudFront class provides a simplified interface for interacting
    with Amazon CloudFront services within a Python application.
    """

    def __init__(
        self,
        aws_region_name: str,
        *,
        aws_profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        caching: bool = False,
    ) -> None:
        """
        aws_profile and aws_region are injected locally for local
        development testing through Brazil. When running on NAWS this
        env variable is not set.
        """

        self._aws_region_name = aws_region_name
        self._aws_profile_name = aws_profile_name
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self.caching = caching
        self.cache: dict[str, Any] = dict()
        self._aws_service_name = "cloudfront"

    @property
    def _client(self) -> CloudFrontClient:
        if self.caching:
            if self.cache.get('client') is None:
                self.cache['client'] = self._get_boto_cloud_front_client()
            return self.cache['client']

        else:
            return self._get_boto_cloud_front_client()

    def _get_boto_cloud_front_client(self) -> CloudFrontClient:
        """
        Create a low-level CloudFront client.
        """

        try:
            boto_session = boto3.session.Session(
                region_name=self._aws_region_name,
                profile_name=self._aws_profile_name,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
            )
            client = boto_session.client(service_name=self._aws_service_name)  # type: ignore

            return client

        except Exception as ex:
            raise exceptions.S3Error(f"Operation failed! - {str(ex)}")

    def invalidate_distribution(self, distribution: str, path: str = "/*"):
        """
        Create a new invalidation.

        :param distribution: The distribution ID where to create the
               invalidation.
        :param path: The path to invalidate, leave default to invalidate
               the whole distribution. Must start with a /. i.e. /*
        :return: Invalidation response syntax.
        :raise CloudFrontError: If operation fails.
        """

        try:
            cloud_front_response = self._client.create_invalidation(
                DistributionId=distribution,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': [
                            path,
                        ],
                    },
                    'CallerReference': str(time.time_ns()),
                },
            )

            return cloud_front_response

        except Exception as ex:
            raise exceptions.CloudFrontError(f"Operation failed! - {str(ex)}")
