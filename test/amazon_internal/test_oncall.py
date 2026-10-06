# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_oncall.py
# Created 5/12/26 - 11:58 AM UK Time (London) by carlogtt

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
import datetime
from typing import Any

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


# Real samples captured via awscurl against the corp OnCall endpoints.
# Keep these shape-faithful so tests fail loudly if the library parses
# fields that the server stopped returning.
_WOCS_TEAM_RESPONSE: dict[str, Any] = {
    "currOncalls": ["phaup"],
    "alsoNotifyList": None,
    "currStart": "2026-05-12T08:00:00Z",
    "currEnd": "2026-05-12T16:00:00Z",
    "nextOncalls": ["mcilvn"],
    "prevOncalls": ["ducluu"],
    "teamName": "kuiper-ground-operations",
    "aliasName": None,
    "aliasType": None,
}

_WOCS_ALIAS_RESPONSE: dict[str, Any] = {
    "currOncalls": ["phaup"],
    "alsoNotifyList": ["grabatin@amazon.com", "mrcchp@amazon.com"],
    "currStart": "2026-05-12T08:00:00Z",
    "currEnd": "2026-05-12T16:00:00Z",
    "nextOncalls": ["mcilvn"],
    "prevOncalls": ["ducluu"],
    "teamName": "kuiper-ground-operations",
    "aliasName": None,
    "aliasType": "MAIL",
}

_NAPI_SCHEDULE_RESPONSE: list[dict[str, Any]] = [
    {
        "startDateTime": "2026-05-12T00:00:00Z",
        "endDateTime": "2026-05-12T08:00:00Z",
        "oncallMember": ["ducluu"],
        "alsoNotifyList": None,
        "shiftType": "historical",
    },
    {
        "startDateTime": "2026-05-12T08:00:00Z",
        "endDateTime": "2026-05-12T16:00:00Z",
        "oncallMember": ["phaup"],
        "alsoNotifyList": None,
        "shiftType": None,
    },
    {
        "startDateTime": "2026-05-12T16:00:00Z",
        "endDateTime": "2026-05-13T00:00:00Z",
        "oncallMember": ["mcilvn"],
        "alsoNotifyList": None,
        "shiftType": None,
    },
]


# ----------------------------------------------------------------------
# 1. Autouse fixture – patch boto3 + utils.AwsSigV4Session
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_deps(monkeypatch):
    """Replace external deps with light fakes for every test."""

    class _FakeResponse:
        def __init__(self, payload: Any):
            self._payload = payload

        def json(self):
            return self._payload

    # Routes a request to the payload that matches its URL path.
    def _route(url: str) -> Any:
        if "/aliases_schedules/" in url:
            return _NAPI_SCHEDULE_RESPONSE
        if "/aliases/" in url:
            return _WOCS_ALIAS_RESPONSE
        if "/teams/" in url:
            return _WOCS_TEAM_RESPONSE
        raise AssertionError(f"Unexpected URL in test: {url}")

    # One shared recorder so tests can inspect what was sent regardless
    # of which internal client was used.
    recorder: dict[str, Any] = {"calls": []}

    class _FakeSigV4:
        def __init__(self, **kwargs):
            # Capture which service this instance represents so tests
            # can assert the right client was selected.
            self.service_name = kwargs.get("service_name")
            self.region_name = kwargs.get("region_name")

        def request(self, *, method, url, headers, params=None, data=None):
            recorder["calls"].append({
                "service": self.service_name,
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "data": data,
            })
            return _FakeResponse(_route(url))

    monkeypatch.setattr("carlogtt_python_library.utils.AwsSigV4Session", _FakeSigV4, raising=True)

    class _FakeBotoSession:
        def __init__(self, **_):
            pass

        def client(self, *_, **__):
            pass

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    # Expose the recorder to tests via a module-level attribute on the
    # fixture's return, but pytest gives us nothing from autouse, so
    # stash it on a well-known module attribute instead.
    import carlogtt_python_library.amazon_internal.oncall as oncall_mod

    oncall_mod._TEST_RECORDER = recorder  # type: ignore[attr-defined]

    yield recorder


# ----------------------------------------------------------------------
# 2. Helpers / fixtures -------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def oncall_fresh():
    from carlogtt_python_library.amazon_internal.oncall import OnCall

    return OnCall("eu-west-1", caching=False)


@pytest.fixture
def oncall_cached():
    from carlogtt_python_library.amazon_internal.oncall import OnCall

    return OnCall("eu-west-1", caching=True)


@pytest.fixture
def recorder():
    import carlogtt_python_library.amazon_internal.oncall as oncall_mod

    return oncall_mod._TEST_RECORDER


# ----------------------------------------------------------------------
# 3. Tests --------------------------------------------------------------
# ----------------------------------------------------------------------
def test_client_cache_and_invalidate(oncall_cached):
    first_wocs = oncall_cached._wocs_client
    first_napi = oncall_cached._napi_client

    assert first_wocs is oncall_cached._wocs_client
    assert first_napi is oncall_cached._napi_client

    oncall_cached.invalidate_client_cache()

    assert first_wocs is not oncall_cached._wocs_client
    assert first_napi is not oncall_cached._napi_client


def test_invalidate_cache_without_caching_raises(oncall_fresh):
    from carlogtt_python_library.exceptions import OnCallError

    with pytest.raises(OnCallError):
        oncall_fresh.invalidate_client_cache()


def test_get_oncall_for_team_returns_dict(oncall_fresh, recorder):
    result = oncall_fresh.get_oncall_for_team("kuiper-ground-operations")

    assert isinstance(result, dict)
    assert result == _WOCS_TEAM_RESPONSE

    call = recorder["calls"][-1]
    assert call["service"] == "who-is-oncall-naws"
    assert call["method"] == "GET"
    assert call["url"].endswith("/teams/kuiper-ground-operations")
    assert call["params"] is None


def test_get_oncall_for_team_url_encodes_name(oncall_fresh, recorder):
    oncall_fresh.get_oncall_for_team("name with/slash")

    call = recorder["calls"][-1]
    # spaces and slashes must be percent-encoded into the path segment
    assert "name%20with%2Fslash" in call["url"]
    assert " " not in call["url"]


def test_get_oncall_for_alias_returns_dict(oncall_fresh, recorder):
    result = oncall_fresh.get_oncall_for_alias("kuiper-ground-operations")

    assert isinstance(result, dict)
    assert result == _WOCS_ALIAS_RESPONSE

    call = recorder["calls"][-1]
    assert call["service"] == "who-is-oncall-naws"
    assert call["url"].endswith("/aliases/kuiper-ground-operations")


def test_get_oncall_at_finds_covering_shift(oncall_fresh, recorder):
    at = datetime.datetime(2026, 5, 12, 12, 0, 0, tzinfo=datetime.timezone.utc)
    shift = oncall_fresh.get_oncall_at("kuiper-ground-operations", "kuiper-ground-operations", at)

    assert shift["oncallMember"] == ["phaup"]
    assert shift["startDateTime"] == "2026-05-12T08:00:00Z"

    call = recorder["calls"][-1]
    assert call["service"] == "oncall-api"
    assert call["method"] == "GET"
    assert call["url"].endswith(
        "/sigv4/teams/kuiper-ground-operations/aliases_schedules/kuiper-ground-operations"
    )

    # ±7-day buffer around 2026-05-12 = 2026-05-05 .. 2026-05-19
    assert call["params"] == {"from": "2026-05-05", "to": "2026-05-19"}


def test_get_oncall_at_boundary_returns_first_matching_shift(oncall_fresh):
    # Shift 1 ends at 08:00:00Z and shift 2 starts at 08:00:00Z. Both
    # match because the comparison is inclusive on both ends. The
    # library returns the first match in response order, which is
    # shift 1.
    at = datetime.datetime(2026, 5, 12, 8, 0, 0, tzinfo=datetime.timezone.utc)
    shift = oncall_fresh.get_oncall_at("team", "alias", at)

    assert shift["oncallMember"] == ["ducluu"]


def test_get_oncall_at_normalizes_non_utc_input(oncall_fresh):
    # 05:00 PDT (UTC-7) == 12:00 UTC, which sits inside shift 2.
    pdt = datetime.timezone(datetime.timedelta(hours=-7))
    at = datetime.datetime(2026, 5, 12, 5, 0, 0, tzinfo=pdt)
    shift = oncall_fresh.get_oncall_at("team", "alias", at)

    assert shift["oncallMember"] == ["phaup"]


def test_get_oncall_at_returns_empty_dict_when_no_match(oncall_fresh):
    at = datetime.datetime(2027, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    shift = oncall_fresh.get_oncall_at("team", "alias", at)

    assert shift == {}


def test_get_oncall_at_rejects_naive_datetime(oncall_fresh):
    from carlogtt_python_library.exceptions import OnCallError

    naive = datetime.datetime(2026, 5, 12, 12, 0, 0)
    with pytest.raises(OnCallError):
        oncall_fresh.get_oncall_at("team", "alias", naive)


def test_get_oncall_between_returns_all_overlapping_shifts(oncall_fresh, recorder):
    # Window spans the full day, hitting all three shifts in the
    # fixture (00-08, 08-16, 16-24). No clipping required because the
    # window aligns with the union of shifts.
    start = datetime.datetime(2026, 5, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 13, 0, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert [s["oncallMember"] for s in result] == [["ducluu"], ["phaup"], ["mcilvn"]]
    assert result[0]["startDateTime"] == "2026-05-12T00:00:00Z"
    assert result[-1]["endDateTime"] == "2026-05-13T00:00:00Z"

    call = recorder["calls"][-1]
    assert call["service"] == "oncall-api"
    assert call["method"] == "GET"
    assert call["url"].endswith("/sigv4/teams/team/aliases_schedules/alias")
    # ±7-day buffer extends from BOTH interval bounds, so:
    # from = 2026-05-12 - 7d = 2026-05-05
    # to   = 2026-05-13 + 7d = 2026-05-20
    assert call["params"] == {"from": "2026-05-05", "to": "2026-05-20"}


def test_get_oncall_between_clips_edge_shifts(oncall_fresh):
    # Window 10:00 -> 18:00 sits inside shifts 2 (08-16) and 3 (16-24).
    # First shift's start should be clipped to 10:00, last shift's end
    # to 18:00. Middle of the API list (shift 1) is excluded entirely.
    start = datetime.datetime(2026, 5, 12, 10, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 12, 18, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert len(result) == 2
    assert result[0]["oncallMember"] == ["phaup"]
    assert result[0]["startDateTime"] == "2026-05-12T10:00:00Z"
    assert result[0]["endDateTime"] == "2026-05-12T16:00:00Z"
    assert result[1]["oncallMember"] == ["mcilvn"]
    assert result[1]["startDateTime"] == "2026-05-12T16:00:00Z"
    assert result[1]["endDateTime"] == "2026-05-12T18:00:00Z"


def test_get_oncall_between_window_inside_single_shift(oncall_fresh):
    # 10:00 -> 14:00 is fully inside shift 2 (08:00 -> 16:00).
    # Both ends of the returned shift should match the window.
    start = datetime.datetime(2026, 5, 12, 10, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 12, 14, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert len(result) == 1
    assert result[0]["oncallMember"] == ["phaup"]
    assert result[0]["startDateTime"] == "2026-05-12T10:00:00Z"
    assert result[0]["endDateTime"] == "2026-05-12T14:00:00Z"


def test_get_oncall_between_excludes_zero_overlap_at_boundary(oncall_fresh):
    # Window starts exactly when shift 2 ends. Shift 2's overlap with
    # the window has zero duration, so it must NOT be returned.
    start = datetime.datetime(2026, 5, 12, 16, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 12, 20, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert len(result) == 1
    assert result[0]["oncallMember"] == ["mcilvn"]
    assert result[0]["startDateTime"] == "2026-05-12T16:00:00Z"
    assert result[0]["endDateTime"] == "2026-05-12T20:00:00Z"


def test_get_oncall_between_returns_empty_list_when_no_overlap(oncall_fresh):
    start = datetime.datetime(2027, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2027, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert result == []


def test_get_oncall_between_normalizes_non_utc_input(oncall_fresh):
    # 03:00 PDT (UTC-7) == 10:00 UTC; 11:00 PDT == 18:00 UTC.
    pdt = datetime.timezone(datetime.timedelta(hours=-7))
    start = datetime.datetime(2026, 5, 12, 3, 0, 0, tzinfo=pdt)
    end = datetime.datetime(2026, 5, 12, 11, 0, 0, tzinfo=pdt)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert [s["oncallMember"] for s in result] == [["phaup"], ["mcilvn"]]
    assert result[0]["startDateTime"] == "2026-05-12T10:00:00Z"
    assert result[-1]["endDateTime"] == "2026-05-12T18:00:00Z"


def test_get_oncall_between_rejects_naive_datetime(oncall_fresh):
    from carlogtt_python_library.exceptions import OnCallError

    aware = datetime.datetime(2026, 5, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    naive = datetime.datetime(2026, 5, 12, 12, 0, 0)

    with pytest.raises(OnCallError):
        oncall_fresh.get_oncall_between("team", "alias", naive, aware)

    with pytest.raises(OnCallError):
        oncall_fresh.get_oncall_between("team", "alias", aware, naive)


def test_get_oncall_between_rejects_inverted_interval(oncall_fresh):
    from carlogtt_python_library.exceptions import OnCallError

    start = datetime.datetime(2026, 5, 12, 12, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 12, 8, 0, 0, tzinfo=datetime.timezone.utc)

    with pytest.raises(OnCallError):
        oncall_fresh.get_oncall_between("team", "alias", start, end)


def test_get_oncall_between_rejects_zero_length_interval(oncall_fresh):
    from carlogtt_python_library.exceptions import OnCallError

    at = datetime.datetime(2026, 5, 12, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with pytest.raises(OnCallError):
        oncall_fresh.get_oncall_between("team", "alias", at, at)


def test_get_oncall_between_preserves_gap_shift(oncall_fresh, monkeypatch):
    # Replace the schedule fixture with one that includes a gap shift
    # (empty oncallMember). Gaps must be returned so callers can detect
    # uncovered periods.
    import carlogtt_python_library.amazon_internal.oncall as oncall_mod

    gap_response = [
        {
            "startDateTime": "2026-05-12T00:00:00Z",
            "endDateTime": "2026-05-12T08:00:00Z",
            "oncallMember": ["ducluu"],
            "alsoNotifyList": None,
            "shiftType": None,
        },
        {
            "startDateTime": "2026-05-12T08:00:00Z",
            "endDateTime": "2026-05-12T16:00:00Z",
            "oncallMember": [],
            "alsoNotifyList": None,
            "shiftType": None,
        },
        {
            "startDateTime": "2026-05-12T16:00:00Z",
            "endDateTime": "2026-05-13T00:00:00Z",
            "oncallMember": ["mcilvn"],
            "alsoNotifyList": None,
            "shiftType": None,
        },
    ]

    original_send = oncall_mod.OnCall._send_oncall_api_request

    def _patched(self, *args, **kwargs):
        if "/aliases_schedules/" in kwargs.get("url", ""):
            return gap_response
        return original_send(self, *args, **kwargs)

    monkeypatch.setattr(oncall_mod.OnCall, "_send_oncall_api_request", _patched)

    start = datetime.datetime(2026, 5, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 5, 13, 0, 0, 0, tzinfo=datetime.timezone.utc)

    result = oncall_fresh.get_oncall_between("team", "alias", start, end)

    assert [s["oncallMember"] for s in result] == [["ducluu"], [], ["mcilvn"]]
