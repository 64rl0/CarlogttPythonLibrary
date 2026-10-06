# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/oncall.py
# Created 4/8/25 - 1:31 PM UK Time (London) by carlogtt

"""
This module provides a client for the Amazon OnCall API.

It wraps two services behind a single handler:
- WhoIsOncall (WOCS): current / previous / next oncall shift lookups.
- NornInterfaceService (NAPI): schedule queries for arbitrary datetimes.
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
import datetime
import logging
import urllib.parse
from typing import Any, Optional, cast

# Third Party Library Imports
import boto3
import botocore.exceptions

# Local Folder (Relative) Imports
from .. import exceptions, utils

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'OnCall',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
OnCallClient = utils.AwsSigV4Session


class OnCall:
    """
    A handler class for the OnCallAPI.

    It includes an option to cache the client session to minimize
    the number of AWS API call.

    For an overview of the underlying Amazon OnCall services (WOCS for
    current/prev/next shifts, NornInterfaceService / NAPI for arbitrary
    schedule queries) and how to onboard your team, see:
    https://w.amazon.com/bin/view/AmazonOncall/API

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

    # Buffer applied on both sides of the target datetime when querying
    # the Schedule API. The API's from/to filter is date-only and its
    # timezone semantics are not documented; 7 days safely covers
    # weekly-or-shorter rotations and any timezone offset.
    _SCHEDULE_QUERY_BUFFER = datetime.timedelta(days=7)

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
        self._client_parameters = client_parameters if client_parameters else dict()

        # WhoIsOncall (WOCS) — current/prev/next shift lookups.
        self._wocs_region_name = "us-west-2"
        self._wocs_host_name = "who-is-oncall.us-west-2.amazonaws.com"
        self._wocs_service_name = "who-is-oncall-naws"
        self._wocs_endpoint_url = "https://who-is-oncall.us-west-2.amazonaws.com"

        # NornInterfaceService (NAPI) — schedule queries.
        self._napi_region_name = "us-west-2"
        self._napi_host_name = "oncall-api.us-west-2.amazonaws.com"
        self._napi_service_name = "oncall-api"
        self._napi_endpoint_url = "https://oncall-api.us-west-2.amazonaws.com"

    @property
    def _wocs_client(self) -> OnCallClient:
        if self._caching:
            if self._cache.get('wocs_client') is None:
                self._cache['wocs_client'] = self._get_oncall_client(
                    region_name=self._wocs_region_name,
                    service_name=self._wocs_service_name,
                )
            return cast(OnCallClient, self._cache['wocs_client'])

        return self._get_oncall_client(
            region_name=self._wocs_region_name,
            service_name=self._wocs_service_name,
        )

    @property
    def _napi_client(self) -> OnCallClient:
        if self._caching:
            if self._cache.get('napi_client') is None:
                self._cache['napi_client'] = self._get_oncall_client(
                    region_name=self._napi_region_name,
                    service_name=self._napi_service_name,
                )
            return cast(OnCallClient, self._cache['napi_client'])

        return self._get_oncall_client(
            region_name=self._napi_region_name,
            service_name=self._napi_service_name,
        )

    def _get_oncall_client(self, region_name: str, service_name: str) -> OnCallClient:
        """
        Create a low level SigV4-signed session for an OnCall service.

        :param region_name: The AWS region of the target service.
        :param service_name: The AWS service name used for SigV4
            signing.
        :return: A signed OnCallClient.
        :raise OnCallError: If session construction fails.
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
                region_name=region_name,
                service_name=service_name,
                boto_session=boto_session,
                protocol=utils.AwsSigV4Protocol.REST,
            )

            return client

        except botocore.exceptions.ClientError as ex:
            raise exceptions.OnCallError(str(ex.response))

        except Exception as ex:
            raise exceptions.OnCallError(str(ex))

    def _send_oncall_api_request(
        self,
        client: OnCallClient,
        host: str,
        method: utils.AwsSigV4RequestMethod,
        url: str,
        *,
        params: Optional[dict[str, str]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Make a signed HTTP request to an OnCall service and return the
        decoded JSON body.

        :param client: The signed session to use.
        :param host: Value for the Host header (service hostname).
        :param method: HTTP method.
        :param url: Fully-qualified request URL.
        :param params: Optional query-string parameters.
        :param data: Optional JSON body.
        :return: The decoded JSON response (shape is endpoint-specific).
        :raise OnCallError: If the request fails.
        """

        headers = {"Host": host}

        try:
            response = client.request(
                method=method.value,
                url=url,
                headers=headers,
                params=params,
                data=data,
            )

            response_obj = response.json()

            return response_obj

        except Exception as ex:
            raise exceptions.OnCallError(str(ex)) from None

    def invalidate_client_cache(self) -> None:
        """
        Clears the cached clients, if caching is enabled.

        This method allows manually invalidating the cached clients,
        forcing new client instances to be created on the next access.
        Useful if AWS credentials have changed or if there's a need to
        connect to a different region within the same instance
        lifecycle.

        :return: None.
        :raise OnCallError: Raises an error if caching is not enabled
               for this instance.
        """

        if not self._cache:
            raise exceptions.OnCallError(
                f"Session caching is not enabled for this instance of {self.__class__.__qualname__}"
            )

        self._cache['wocs_client'] = None
        self._cache['napi_client'] = None

    def get_oncall_for_team(self, team_name: str) -> dict[str, Any]:
        """
        Retrieve the current, previous, and next oncall shift for a
        team.

        Use this for teams whose oncall is driven by the default team
        schedule. For teams that expose custom aliases (e.g. separate
        primary/secondary), use :meth:`get_oncall_for_alias` instead —
        the team endpoint can return incorrect shift information for
        those.

        :param team_name: The oncall team name.
        :return: A dictionary with keys ``currOncalls``,
            ``prevOncalls``, ``nextOncalls``, ``currStart``,
            ``currEnd``, ``alsoNotifyList``, ``teamName``,
            ``aliasName``,
            ``aliasType``. ``aliasName`` and ``aliasType`` are ``None``
            on this endpoint. ``currStart`` / ``currEnd`` are ISO
            datetime strings (UTC, trailing ``Z``).
        :raise OnCallError: If the request fails.
        """

        path = f"/teams/{urllib.parse.quote(team_name, safe='')}"
        url = f"{self._wocs_endpoint_url}{path}"

        response = self._send_oncall_api_request(
            client=self._wocs_client,
            host=self._wocs_host_name,
            method=utils.AwsSigV4RequestMethod.GET,
            url=url,
        )

        assert isinstance(response, dict)

        return response

    def get_oncall_for_alias(self, alias_name: str) -> dict[str, Any]:
        """
        Retrieve the current, previous, and next oncall shift for a team
        alias.

        Required for teams using custom aliases — see
        https://w.amazon.com/bin/view/CorpInfra/Tools/OncallProject/API/CustomAliasesTeamOncall

        :param alias_name: The oncall alias name
            (e.g. ``page-corpinfra-tools-primary``).
        :return: A dictionary with keys ``currOncalls``,
            ``prevOncalls``, ``nextOncalls``, ``currStart``,
            ``currEnd``, ``alsoNotifyList``, ``teamName``,
            ``aliasName``,
            ``aliasType``. ``currStart`` / ``currEnd`` are ISO datetime
            strings (UTC, trailing ``Z``).
        :raise OnCallError: If the request fails.
        """

        path = f"/aliases/{urllib.parse.quote(alias_name, safe='')}"
        url = f"{self._wocs_endpoint_url}{path}"

        response = self._send_oncall_api_request(
            client=self._wocs_client,
            host=self._wocs_host_name,
            method=utils.AwsSigV4RequestMethod.GET,
            url=url,
        )

        assert isinstance(response, dict)

        return response

    def get_oncall_at(
        self,
        team_name: str,
        alias_name: str,
        at_datetime_utc: datetime.datetime,
    ) -> dict[str, Any]:
        """
        Find the oncall shift that covers a specific point in time.

        Internally calls the NornInterfaceService Schedule API. For
        current-oncall lookups prefer :meth:`get_oncall_for_team` or
        :meth:`get_oncall_for_alias` — the Schedule API is not
        recommended for critical paths by the Amazon OnCall team.

        :param team_name: The oncall team name.
        :param alias_name: The alias within that team to query.
        :param at_datetime_utc: A timezone-aware datetime. Naive
            datetimes are rejected because timezone is load-bearing for
            shift boundary matching.
        :return: The matching shift as a dict with ``startDateTime``,
            ``endDateTime``, ``oncallMember`` (list of logins — empty
            for gap shifts), ``alsoNotifyList``, and ``shiftType`` (e.g.
            ``"historical"`` or ``None``). May also contain
            ``contributors`` for shifts produced by post-processors
            (e.g. fragmentation). An empty dict is returned if no shift
            covers the requested instant.
        :raise OnCallError: If ``at_datetime_utc`` is naive or the
            request fails.
        """

        if at_datetime_utc.tzinfo is None:
            raise exceptions.OnCallError(
                "at_datetime_utc must be timezone-aware; received a naive datetime"
            )

        at_utc = at_datetime_utc.astimezone(datetime.timezone.utc)

        from_date = (at_utc - self._SCHEDULE_QUERY_BUFFER).date()
        to_date = (at_utc + self._SCHEDULE_QUERY_BUFFER).date()

        path = (
            f"/sigv4/teams/{urllib.parse.quote(team_name, safe='')}"
            f"/aliases_schedules/{urllib.parse.quote(alias_name, safe='')}"
        )
        url = f"{self._napi_endpoint_url}{path}"
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }

        response = self._send_oncall_api_request(
            client=self._napi_client,
            host=self._napi_host_name,
            method=utils.AwsSigV4RequestMethod.GET,
            url=url,
            params=params,
        )

        assert isinstance(response, list)

        for shift in response:
            start_raw = shift.get('startDateTime')
            end_raw = shift.get('endDateTime')
            if not start_raw or not end_raw:
                continue

            start = self._parse_utc_z(start_raw)
            end = self._parse_utc_z(end_raw)

            if start <= at_utc <= end:
                return cast(dict[str, Any], shift)

        return {}

    def get_oncall_between(
        self,
        team_name: str,
        alias_name: str,
        start_datetime_utc: datetime.datetime,
        end_datetime_utc: datetime.datetime,
    ) -> list[dict[str, Any]]:
        """
        Return every oncall shift overlapping the half-open interval
        ``[start_datetime_utc, end_datetime_utc)``.

        Internally calls the NornInterfaceService Schedule API and
        filters the response down to shifts that intersect the requested
        window. Edge shifts are clipped: a shift that started before
        ``start_datetime_utc`` is returned with ``startDateTime`` set to
        ``start_datetime_utc``, and a shift that ends after
        ``end_datetime_utc`` is returned with ``endDateTime`` set to
        ``end_datetime_utc``. Gap shifts (empty ``oncallMember``) are
        preserved so callers can detect uncovered periods.
        For current-oncall lookups prefer :meth:`get_oncall_for_team` or
        :meth:`get_oncall_for_alias` — the Schedule API is not
        recommended for critical paths by the Amazon OnCall team.

        :param team_name: The oncall team name.
        :param alias_name: The alias within that team to query.
        :param start_datetime_utc: Inclusive lower bound.
            Timezone-aware.
        :param end_datetime_utc: Exclusive upper bound. Timezone-aware
            and strictly greater than ``start_datetime_utc``.
        :return: A list of shift dicts in API order, each with
            ``startDateTime``, ``endDateTime``, ``oncallMember`` (list
            of logins — empty for gap shifts), ``alsoNotifyList``, and
            ``shiftType``. ``startDateTime`` / ``endDateTime`` are ISO
            datetime strings in UTC with a trailing ``Z``. May also
            contain ``contributors`` for shifts produced by
            post-processors. Empty list if no shift overlaps the
            interval.
        :raise OnCallError: If either datetime is naive, the interval
            is empty or inverted, or the request fails.
        """

        if start_datetime_utc.tzinfo is None or end_datetime_utc.tzinfo is None:
            raise exceptions.OnCallError(
                "start_datetime_utc and end_datetime_utc must be timezone-aware;"
                " received a naive datetime"
            )

        start_utc = start_datetime_utc.astimezone(datetime.timezone.utc)
        end_utc = end_datetime_utc.astimezone(datetime.timezone.utc)

        if end_utc <= start_utc:
            raise exceptions.OnCallError(
                "end_datetime_utc must be strictly greater than start_datetime_utc"
            )

        from_date = (start_utc - self._SCHEDULE_QUERY_BUFFER).date()
        to_date = (end_utc + self._SCHEDULE_QUERY_BUFFER).date()

        path = (
            f"/sigv4/teams/{urllib.parse.quote(team_name, safe='')}"
            f"/aliases_schedules/{urllib.parse.quote(alias_name, safe='')}"
        )
        url = f"{self._napi_endpoint_url}{path}"
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }

        response = self._send_oncall_api_request(
            client=self._napi_client,
            host=self._napi_host_name,
            method=utils.AwsSigV4RequestMethod.GET,
            url=url,
            params=params,
        )

        assert isinstance(response, list)

        result: list[dict[str, Any]] = []

        for shift in response:
            start_raw = shift.get('startDateTime')
            end_raw = shift.get('endDateTime')
            if not start_raw or not end_raw:
                continue

            shift_start = self._parse_utc_z(start_raw)
            shift_end = self._parse_utc_z(end_raw)

            # Half-open overlap test on both interval bounds: a shift
            # touching only the boundary contributes zero duration and
            # is excluded.
            if shift_end <= start_utc or shift_start >= end_utc:
                continue

            clipped_start = max(shift_start, start_utc)
            clipped_end = min(shift_end, end_utc)

            clipped_shift = dict(shift)
            clipped_shift['startDateTime'] = self._format_utc_z(clipped_start)
            clipped_shift['endDateTime'] = self._format_utc_z(clipped_end)

            result.append(clipped_shift)

        return result

    @staticmethod
    def _parse_utc_z(value: str) -> datetime.datetime:
        """
        Parse an ISO-8601 datetime string in the Schedule API's
        ``...Z`` convention into a UTC-aware ``datetime``.

        ``datetime.fromisoformat`` rejects a trailing ``Z`` on Python
        3.10 (fixed in 3.11+), so the suffix is normalized to
        ``+00:00`` before parsing. The result is always converted to
        UTC for consistent comparisons even if the input carries a
        non-UTC offset.
        """

        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(
            datetime.timezone.utc
        )

    @staticmethod
    def _format_utc_z(value: datetime.datetime) -> str:
        """
        Format a UTC datetime as an ISO-8601 string with a trailing
        ``Z`` to match the Schedule API response convention.
        """

        return value.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
