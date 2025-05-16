# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_pipelines.py
# Created 4/7/25 - 11:36 AM UK Time (London) by carlogtt
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


# ----------------------------------------------------------------------
# 1. Autouse fixture – patch boto3 + utils.retry + utils.AwsSigV4Session
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_deps(monkeypatch):
    """Replace external deps with light fakes for every test."""

    # ---- Fake SigV4 Session used by Pipelines._get_pipelines_client --
    class _FakeResponse:
        def __init__(self, payload: Optional[dict[str, Any]] = None):
            self._payload = payload or {}

        def json(self):
            return self._payload

    class _FakeSigV4:
        def __init__(self, **_):
            self._last_request: Optional[dict[str, Any]] = None

        def request(self, *, method, url, headers, data):
            self._last_request = {
                "method": method,
                "url": url,
                "headers": headers,
                "data": data,
            }
            # craft echo response
            return _FakeResponse({"ok": True, "echo": data})

    monkeypatch.setattr("carlogtt_library.utils.AwsSigV4Session", _FakeSigV4, raising=True)

    # ---- Fake boto3 session (never hits AWS) ------------------------
    class _FakeBotoSession:
        def __init__(self, **_):
            pass

        def client(self, *_, **__):
            pass  # never called because Pipelines uses SigV4 Session

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    yield


# ----------------------------------------------------------------------
# 2. Helpers / fixtures -------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def pipelines_cached():
    from carlogtt_library.amazon_internal.pipelines import Pipelines

    return Pipelines("eu-west-1", caching=True)


@pytest.fixture
def pipelines_fresh():
    from carlogtt_library.amazon_internal.pipelines import Pipelines

    return Pipelines("eu-west-1", caching=False)


# ----------------------------------------------------------------------
# 3. Tests --------------------------------------------------------------
# ----------------------------------------------------------------------
def test_client_cache_and_invalidate(pipelines_cached):
    first = pipelines_cached._client
    assert first is pipelines_cached._client

    pipelines_cached.invalidate_client_cache()
    assert first is not pipelines_cached._client


def test_send_api_request_echo(pipelines_fresh):
    import carlogtt_library as mylib

    # private helper exercised indirectly via public method
    res = pipelines_fresh.get_pipelines_containing_target(
        target_name="foo",
        target_type=mylib.TargetType.PKG,  # type: ignore[attr-defined]
        in_primary_pipeline=True,
    )
    assert res["ok"] and res["echo"]["targetName"] == "foo"


def test_get_pipeline_structure_by_name(pipelines_fresh):
    res = pipelines_fresh.get_pipeline_structure(pipeline_name="MyPipe")
    assert res["echo"]["pipelineName"] == "MyPipe"


def test_get_pipeline_structure_by_id(pipelines_fresh):
    res = pipelines_fresh.get_pipeline_structure(pipeline_id="abc123")
    assert res["echo"]["pipelineId"] == "abc123"


def test_get_pipeline_structure_missing_args_raises(pipelines_fresh):
    from carlogtt_library.exceptions import PipelinesError

    with pytest.raises(PipelinesError):
        pipelines_fresh.get_pipeline_structure()


def test_get_pipeline_structure_both_args_raises(pipelines_fresh):
    from carlogtt_library.exceptions import PipelinesError

    with pytest.raises(PipelinesError):
        pipelines_fresh.get_pipeline_structure(pipeline_name="X", pipeline_id="Y")


def test_get_pipelines_containing_target(pipelines_cached):
    import carlogtt_library as mylib

    res = pipelines_cached.get_pipelines_containing_target(
        target_name="demo",
        target_type=mylib.TargetType.CD,  # type: ignore[attr-defined]
        in_primary_pipeline=False,
    )
    assert res["echo"]["targetType"] == "CD"
