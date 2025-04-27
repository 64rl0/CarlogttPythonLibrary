# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_aws_sig_v4_requests.py
# Created 4/26/25 - 8:20 AM UK Time (London) by carlogtt
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

# Special Imports
from __future__ import annotations

# Standard Library Imports
import json
from types import SimpleNamespace

# Third Party Library Imports
import pytest
import requests
from test__entrypoint__ import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)
# master_logger.detach_root_logger()

# Type aliases
#


# ----------------------------------------------------------------------
# Monkey-patches applied automatically to every test
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_decorators_retry(monkeypatch):
    """
    Replace decorators.retry with a do-nothing decorator/context-manager.
    """

    class _NoopRetry:
        def __call__(self, fn):  # decorator form
            return fn

        def __enter__(self):  # context-manager form
            return lambda fn, *a, **kw: fn(*a, **kw)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "carlogtt_library.utils.decorators.retry",
        lambda *a, **kw: _NoopRetry(),
        raising=True,
    )


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def dummy_boto_session():
    """A minimal stub that looks like a boto3.Session."""
    return SimpleNamespace(get_credentials=lambda: None)


@pytest.fixture
def session(dummy_boto_session):
    from carlogtt_library.utils.aws_sig_v4_requests import (
        AwsSigV4Protocol,
        AwsSigV4Session,
    )

    return AwsSigV4Session(
        region_name="eu-west-1",
        service_name="execute-api",
        boto_session=dummy_boto_session,
        protocol=AwsSigV4Protocol.RPCv1,
    )


# ----------------------------------------------------------------------
# _serialize_request_data ------------------------------------------------
# ----------------------------------------------------------------------
def test_serialize_request_data_produces_utf8_bytes(session):
    data = {"α": "β", "x": 1}
    out = session._serialize_request_data(data)
    assert isinstance(out, bytes)
    assert json.loads(out.decode()) == data


# ----------------------------------------------------------------------
# prepare_request --------------------------------------------------------
# ----------------------------------------------------------------------
def test_prepare_request_applies_headers_and_signs(monkeypatch, session):
    # Patch the signing helper so we don't need real AWS creds
    captured_req = {}

    def _fake_sign(request):
        captured_req["prep"] = request
        return {"Authorization": "FAKE-SIG"}

    monkeypatch.setattr(session, "_get_signed_headers", _fake_sign)

    req = requests.Request("GET", "https://example.com/hello")
    prepared = session.prepare_request(req)

    # Base + protocol headers
    for hdr in ("Accept", "Content-Type", "Content-Encoding"):
        assert hdr in prepared.headers

    # Signature injected
    assert prepared.headers["Authorization"] == "FAKE-SIG"

    # ensure helper got the PreparedRequest we expect
    assert captured_req["prep"] is prepared


# ----------------------------------------------------------------------
# request()  – success & failure paths ----------------------------------
# ----------------------------------------------------------------------
def _make_response(status: int, body: str = "OK", json_body: dict | None = None):
    """Utility to craft a fake requests.Response."""
    resp = requests.Response()
    resp.status_code = status
    resp._content = body.encode()
    if json_body is not None:
        resp._content = json.dumps(json_body).encode()
        resp.headers["Content-Type"] = "application/json"
    resp.url = "https://example.com"
    return resp


def test_request_serializes_data_and_returns(monkeypatch, session):
    # intercept the underlying Session.request call
    called_kwargs = {}

    def _fake_request(self, *args, **kwargs):
        called_kwargs.update(kwargs)
        return _make_response(200)

    monkeypatch.setattr(requests.Session, "request", _fake_request, raising=True)

    resp = session.request("POST", "https://example.com", data={"a": 1})

    # data should have been converted to bytes
    assert isinstance(called_kwargs["data"], bytes)
    assert resp.status_code == 200


def test_request_raises_on_http_error(monkeypatch, session):
    monkeypatch.setattr(
        requests.Session,
        "request",
        lambda *a, **k: _make_response(502, "bad"),
        raising=True,
    )

    with pytest.raises(mylib.AwsSigV4SessionError):
        session.request("GET", "https://example.com")


def test_request_rpcv0_detects_embedded_error(monkeypatch, dummy_boto_session):
    ses = mylib.AwsSigV4Session(
        region_name="eu-west-1",
        service_name="execute-api",
        boto_session=dummy_boto_session,
        protocol=mylib.AwsSigV4Protocol.RPCv0,
    )

    # fake Coral error payload (status 200 but __type contains 'Exception')
    payload = {
        "Output": {
            "__type": "SomeService.Exception",
            "message": "boom",
        }
    }

    monkeypatch.setattr(
        requests.Session,
        "request",
        lambda *a, **k: _make_response(200, json_body=payload),
        raising=True,
    )

    with pytest.raises(mylib.AwsSigV4SessionError):
        ses.request("POST", "https://example.com", data={})
