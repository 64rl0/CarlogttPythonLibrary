# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/aws_boto3/cloud_watch.py
# Created 7/9/26 - 4:27 PM UK Time (London) by carlogtt

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
import botocore.exceptions
import mypy_boto3_cloudwatch

# Local Folder (Relative) Imports
from .. import exceptions
from . import aws_service_base

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'CloudWatch',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
CloudWatchClient = mypy_boto3_cloudwatch.client.CloudWatchClient


class CloudWatch(aws_service_base.AwsServiceBase[CloudWatchClient]):
    """
    The CloudWatch class provides a simplified interface for interacting
    with Amazon CloudWatch services within a Python application.

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
            aws_service_name="cloudwatch",
            exception_type=exceptions.CloudWatchError,
        )

    def get_alarm_state_by_arn(self, alarm_arn: str) -> str:
        """
        Return the current state of a CloudWatch alarm given its ARN.

        CloudWatch has no API to look up an alarm directly by ARN, so
        the alarm name is parsed out of the ARN and used to query
        `describe_alarms`. Both metric and composite alarms are
        requested, then the returned alarm whose ARN matches the
        supplied one is selected. Matching on the returned ARN (rather
        than trusting the name alone) guards against a name collision
        between a metric and a composite alarm.

        The returned state is one of the CloudWatch alarm state values:
        'OK', 'ALARM', or 'INSUFFICIENT_DATA'.

        :param alarm_arn: The Amazon Resource Name (ARN) of the alarm,
               e.g. 'arn:aws:cloudwatch:<region>:<acct>:alarm:<name>'.
        :return: The alarm state value as a string.
        :raise CloudWatchError: If the ARN is malformed, no alarm
               matches the ARN, or the underlying API call fails.
        """

        alarm_name = self._parse_alarm_name(alarm_arn)

        try:
            response = self._client.describe_alarms(
                AlarmNames=[alarm_name],
                AlarmTypes=['CompositeAlarm', 'MetricAlarm'],
            )

            alarms: list[Any] = [
                *response.get('MetricAlarms', []),
                *response.get('CompositeAlarms', []),
            ]

            for alarm in alarms:
                if alarm.get('AlarmArn') == alarm_arn:
                    return str(alarm['StateValue'])

            raise exceptions.CloudWatchError(f"No CloudWatch alarm found for ARN '{alarm_arn}'.")

        except exceptions.CloudWatchError:
            raise

        except botocore.exceptions.ClientError as ex:
            raise exceptions.CloudWatchError(str(ex.response)) from None

        except Exception as ex:
            raise exceptions.CloudWatchError(str(ex)) from None

    @staticmethod
    def _parse_alarm_name(alarm_arn: str) -> str:
        """
        Extract the alarm name from a CloudWatch alarm ARN.

        The alarm ARN format is
        'arn:aws:cloudwatch:<region>:<account-id>:alarm:<alarm-name>'.
        The alarm name is everything following the ':alarm:' segment and
        may itself contain colons.

        :param alarm_arn: The alarm ARN to parse.
        :return: The alarm name.
        :raise CloudWatchError: If the ARN does not contain an ':alarm:'
               segment or the name is empty.
        """

        marker = ':alarm:'
        marker_index = alarm_arn.find(marker)

        if marker_index == -1:
            raise exceptions.CloudWatchError(
                f"Invalid CloudWatch alarm ARN '{alarm_arn}': missing '{marker}' segment."
            )

        alarm_name = alarm_arn[marker_index + len(marker) :]

        if not alarm_name:
            raise exceptions.CloudWatchError(
                f"Invalid CloudWatch alarm ARN '{alarm_arn}': empty alarm name."
            )

        return alarm_name
