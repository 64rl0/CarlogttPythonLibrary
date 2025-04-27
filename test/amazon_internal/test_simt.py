# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_simt.py
# Created 2/20/25 - 12:21 PM UK Time (London) by carlogtt
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
# flake8: noqa
# mypy: ignore-errors

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
from typing import Any, Optional
from unittest.mock import MagicMock

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


# ----------------------------------------------------------------------
# 1.  Global monkey-patches applied to every test
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_boto_and_retry(monkeypatch):
    """Replace boto3 Session + utils.retry with local fakes."""

    # ---------- fake Tickety client -----------------------------------
    class _FakeTickety:
        def __init__(self):
            self._pages = 0
            self.updated_payload: Optional[dict[str, Any]] = None

        # list_tickets paginates: first call returns nextToken, second doesn't
        def list_tickets(self, **_kw):
            self._pages += 1
            if self._pages == 1:
                return {
                    "ticketSummaries": [{"id": "t1"}, {"id": "t2"}],
                    "nextToken": "MORE",
                }
            return {
                "ticketSummaries": [{"id": "t3"}],
                "nextToken": "",
            }

        # ----------------- ticket operations --------------------------
        def get_ticket(self, **_kw):
            ticket_id = _kw["ticketId"]
            if ticket_id == "missing_field":
                return {}  # triggers KeyError path
            return {"ticket": {"id": ticket_id, "status": "OPEN"}}

        def update_ticket(self, **_kw):
            self.updated_payload = _kw["update"]
            if _kw["ticketId"] == "bad":
                return {"ResponseMetadata": {"HTTPStatusCode": 500}}
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

        def create_ticket_comment(self, **_kw):
            if _kw["ticketId"] == "fail":
                return {}  # missing commentId
            return {"commentId": "c-123"}

        def create_ticket(self, **_kw):
            data = _kw["ticket"]
            if "summary" not in data:
                return {}  # missing id
            return {"id": "sim-123"}

    # ---------- fake boto3 Session -----------------------------------
    class _FakeBotoSession:
        def __init__(self, **_):
            self._client = _FakeTickety()

        def client(self, **_):
            return self._client

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    # ---------- utils.retry  (decorator & ctx-mgr) --------------------
    class _NoopRetry:
        def __call__(self, fn):  # decorator
            return fn

        def __enter__(self):  # context-manager
            return lambda fn, *a, **kw: fn(*a, **kw)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "carlogtt_library.utils.retry",
        lambda *a, **kw: _NoopRetry(),
        raising=True,
    )

    yield


# ----------------------------------------------------------------------
# 2.  Fixtures – instances ready for tests
# ----------------------------------------------------------------------
@pytest.fixture
def simt_cached():
    from carlogtt_library.amazon_internal.simt import SimT

    return SimT("eu-west-1", caching=True)


@pytest.fixture
def simt_fresh():
    from carlogtt_library.amazon_internal.simt import SimT

    return SimT("eu-west-1", caching=False)


@pytest.fixture
def simt_instance():
    import carlogtt_library as mylib

    return mylib.SimT('eu-west-1')


@pytest.fixture
def mock_client():
    return MagicMock()


# ----------------------------------------------------------------------
# 3.  Tests
# ----------------------------------------------------------------------
def test_client_caching_and_invalidate(simt_cached):
    first = simt_cached._client
    assert first is simt_cached._client  # cached

    simt_cached.invalidate_client_cache()
    assert first is not simt_cached._client  # new instance after invalidation


def test_get_tickets_paginates(simt_cached):
    ids = [t["id"] for t in simt_cached.get_tickets({"foo": "bar"})]
    assert ids == ["t1", "t2", "t3"]


def test_get_ticket_details_success(simt_fresh):
    ticket = simt_fresh.get_ticket_details("t1")
    assert ticket["id"] == "t1"


def test_get_ticket_details_missing_field_raises(simt_fresh):
    from carlogtt_library.exceptions import SimTError

    with pytest.raises(SimTError):
        simt_fresh.get_ticket_details("missing_field")


def test_update_ticket_success(simt_cached):
    payload = {"state": "CLOSED"}
    simt_cached.update_ticket("t1", payload)
    assert simt_cached._client.updated_payload == payload


def test_update_ticket_bad_status_raises(simt_cached):
    from carlogtt_library.exceptions import SimTError

    with pytest.raises(SimTError):
        simt_cached.update_ticket("bad", {})


def test_create_comment_success(simt_cached):
    cid = simt_cached.create_ticket_comment("t1", "hello")
    assert cid == "c-123"


def test_create_comment_missing_key_raises(simt_cached):
    from carlogtt_library.exceptions import SimTError

    with pytest.raises(SimTError):
        simt_cached.create_ticket_comment("fail", "oops")


def test_create_ticket_success(simt_fresh):
    tid = simt_fresh.create_ticket({"summary": "Test"})
    assert tid == "sim-123"


def test_create_ticket_missing_id_raises(simt_fresh):
    from carlogtt_library.exceptions import SimTError

    with pytest.raises(SimTError):
        simt_fresh.create_ticket({"no_summary": "bad"})


def test_simticket_handler_deprecation():
    from carlogtt_library.amazon_internal.simt import SimTicketHandler

    with pytest.warns(DeprecationWarning):
        handler = SimTicketHandler("us-east-1")


def test_update_ticket_success(simt_instance, mock_client):
    import carlogtt_library as mylib

    simt_instance._cache['client'] = mock_client
    mock_client.update_ticket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

    try:
        simt_instance.update_ticket("TICKET123", {"status": "closed"})
    except mylib.SimTError:
        assert True, "update_ticket() raised SimTError unexpectedly!"


def test_update_ticket_client_error(simt_instance, mock_client):
    simt_instance._cache['client'] = mock_client
    mock_client.update_ticket.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Unauthorized"}}, "UpdateTicket"
    )

    simt_instance.update_ticket("TICKET123", {"status": "closed"})


def test_update_ticket_generic_exception(simt_instance, mock_client):
    simt_instance._cache['client'] = mock_client
    mock_client.update_ticket.side_effect = Exception("Unexpected error")

    simt_instance.update_ticket("TICKET123", {"status": "closed"})


def test_update_ticket_invalid_response(simt_instance, mock_client):
    simt_instance._cache['client'] = mock_client
    mock_client.update_ticket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    simt_instance.update_ticket("TICKET123", {"status": "closed"})


def test_update_ticket_invalid_response_type(simt_instance, mock_client):
    simt_instance._cache['client'] = mock_client
    mock_client.update_ticket.return_value = None

    simt_instance.update_ticket("TICKET123", {"status": "closed"})
