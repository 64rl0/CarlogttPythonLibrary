# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/CarlogttLibrary/test/aws_boto3/test_cloud_watch.py
# Created 7/9/26 - 3:33 PM UK Time (London) by carlogtt

"""
This module ...
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made code or quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
from typing import Any, Dict

# Third Party Library Imports
import botocore.exceptions
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#

_METRIC_ARN = "arn:aws:cloudwatch:us-east-1:111122223333:alarm:my-metric-alarm"
_COMPOSITE_ARN = "arn:aws:cloudwatch:us-east-1:111122223333:alarm:my-composite-alarm"
# Alarm whose name contains colons, to exercise ARN name parsing.
_COLON_NAME_ARN = "arn:aws:cloudwatch:us-east-1:111122223333:alarm:team:service:latency"


class _FakeCloudWatch:
    """Pretends to be mypy_boto3_cloudwatch.client.CloudWatchClient."""

    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []
        # When set, describe_alarms raises instead of returning.
        self.raise_on_describe: Any = None

    def describe_alarms(self, **payload):
        """Mimic the happy-path response from the real API."""
        self.calls.append(payload)
        if self.raise_on_describe is not None:
            raise self.raise_on_describe
        return {
            "MetricAlarms": [
                {"AlarmArn": _METRIC_ARN, "AlarmName": "my-metric-alarm", "StateValue": "ALARM"},
            ],
            "CompositeAlarms": [
                {
                    "AlarmArn": _COMPOSITE_ARN,
                    "AlarmName": "my-composite-alarm",
                    "StateValue": "OK",
                },
                {
                    "AlarmArn": _COLON_NAME_ARN,
                    "AlarmName": "team:service:latency",
                    "StateValue": "INSUFFICIENT_DATA",
                },
            ],
        }


class _FakeBotoSession:
    """Pretends to be `boto3.session.Session` (only what we need)."""

    def __init__(self, **init_kw) -> None:
        self.init_kw = init_kw
        self._client = _FakeCloudWatch()

    def client(self, service_name: str, **_kw):
        # allow tests to simulate failures by asking for a special service name
        if service_name == "RAISE_CLIENT_ERROR":
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "Boom", "Message": "nope"}}, "DescribeAlarms"
            )
        if service_name == "RAISE_GENERIC":
            raise RuntimeError("bang")
        return self._client


@pytest.fixture(autouse=True)
def _patch_boto(monkeypatch):
    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    yield


@pytest.fixture
def lib_exc():
    from carlogtt_python_library import exceptions as lib_exc

    return lib_exc


@pytest.fixture
def cw_cls():
    from carlogtt_python_library.aws_boto3.cloud_watch import CloudWatch

    class _CW(CloudWatch):
        @property
        def client(self):
            return self._client

    return _CW


@pytest.mark.parametrize(
    "caching",
    [
        False,
        True,
    ],
)
def test_client_caching(caching, cw_cls):
    cw = cw_cls("us-east-1", caching=caching)
    first = cw.client
    second = cw.client
    if caching:
        assert first is second
    else:
        assert first is not second


def test_get_alarm_state_by_arn_metric_alarm(cw_cls):
    cw = cw_cls("us-east-1", caching=True)
    state = cw.get_alarm_state_by_arn(_METRIC_ARN)

    assert state == "ALARM"
    # correct payload reached the fake low-level client
    payload = cw.client.calls[-1]
    assert payload["AlarmNames"] == ["my-metric-alarm"]
    assert payload["AlarmTypes"] == ["CompositeAlarm", "MetricAlarm"]


def test_get_alarm_state_by_arn_composite_alarm(cw_cls):
    cw = cw_cls("us-east-1", caching=True)
    state = cw.get_alarm_state_by_arn(_COMPOSITE_ARN)

    assert state == "OK"
    # composite alarm was matched by its name, not the metric alarm's
    payload = cw.client.calls[-1]
    assert payload["AlarmNames"] == ["my-composite-alarm"]


def test_get_alarm_state_by_arn_name_with_colons(cw_cls):
    # Alarm names may contain colons; everything after ':alarm:' is the name.
    cw = cw_cls("us-east-1", caching=True)

    state = cw.get_alarm_state_by_arn(_COLON_NAME_ARN)

    assert state == "INSUFFICIENT_DATA"
    payload = cw.client.calls[-1]
    assert payload["AlarmNames"] == ["team:service:latency"]


def test_get_alarm_state_by_arn_not_found_raises(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=True)
    unknown_arn = "arn:aws:cloudwatch:us-east-1:111122223333:alarm:does-not-exist"

    with pytest.raises(lib_exc.CloudWatchError) as excinfo:
        cw.get_alarm_state_by_arn(unknown_arn)
    assert "No CloudWatch alarm found" in str(excinfo.value)


def test_get_alarm_state_by_arn_arn_matched_not_just_name(cw_cls, lib_exc):
    # A returned alarm sharing the requested name but a different ARN must
    # NOT be accepted — matching is on the ARN.
    cw = cw_cls("us-east-1", caching=True)
    # Same name as the metric alarm, but a different region in the ARN.
    other_region_arn = "arn:aws:cloudwatch:eu-west-1:111122223333:alarm:my-metric-alarm"

    with pytest.raises(lib_exc.CloudWatchError):
        cw.get_alarm_state_by_arn(other_region_arn)


def test_get_alarm_state_by_arn_invalid_arn_no_marker_raises(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=True)

    with pytest.raises(lib_exc.CloudWatchError) as excinfo:
        cw.get_alarm_state_by_arn("arn:aws:sns:us-east-1:111122223333:some-topic")
    assert "missing ':alarm:'" in str(excinfo.value)


def test_get_alarm_state_by_arn_invalid_arn_empty_name_raises(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=True)

    with pytest.raises(lib_exc.CloudWatchError) as excinfo:
        cw.get_alarm_state_by_arn("arn:aws:cloudwatch:us-east-1:111122223333:alarm:")
    assert "empty alarm name" in str(excinfo.value)


def test_get_alarm_state_by_arn_client_creation_client_error_raises_custom(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=False)
    # force the fake boto session to explode with ClientError on client build
    cw._aws_service_name = "RAISE_CLIENT_ERROR"

    with pytest.raises(lib_exc.CloudWatchError):
        cw.get_alarm_state_by_arn(_METRIC_ARN)


def test_get_alarm_state_by_arn_client_creation_generic_error_raises_custom(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=False)
    cw._aws_service_name = "RAISE_GENERIC"

    with pytest.raises(lib_exc.CloudWatchError):
        cw.get_alarm_state_by_arn(_METRIC_ARN)


def test_get_alarm_state_by_arn_describe_client_error_raises_custom(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=True)
    cw.client.raise_on_describe = botocore.exceptions.ClientError(
        {"Error": {"Code": "Throttling", "Message": "slow down"}}, "DescribeAlarms"
    )

    with pytest.raises(lib_exc.CloudWatchError):
        cw.get_alarm_state_by_arn(_METRIC_ARN)


def test_get_alarm_state_by_arn_describe_generic_error_raises_custom(cw_cls, lib_exc):
    cw = cw_cls("us-east-1", caching=True)
    cw.client.raise_on_describe = RuntimeError("bang")

    with pytest.raises(lib_exc.CloudWatchError):
        cw.get_alarm_state_by_arn(_METRIC_ARN)
