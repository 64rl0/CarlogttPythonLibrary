# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_mcm.py
# Created 6/9/26 - 10:32 AM UK Time (London) by carlogtt

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
from types import SimpleNamespace
from typing import Any
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


# A nested object shaped like the ModeledCmApiService GetCmResponse, so
# that get_mcm's attribute walk (response.cm.cm_overview.title, etc.)
# exercises the same access path it would against the real client.
def _make_get_cm_response(
    friendly_id: str = "MCM-12345678",
    uuid: str = "11111111-2222-3333-4444-555555555555",
) -> Any:
    return SimpleNamespace(
        cm=SimpleNamespace(
            cm_friendly_identifier=SimpleNamespace(friendly_id=friendly_id),
            cm_identifier=SimpleNamespace(uuid=uuid),
            cm_overview=SimpleNamespace(
                title="Replace antenna controller at MSP501",
                description="Swap the failed controller unit.",
                requester="alice",
                technician="bob",
                scheduled_start=1750000000000,
                scheduled_end=1750003600000,
            ),
            status_and_approvers=SimpleNamespace(cm_status="Scheduled"),
        )
    )


# ----------------------------------------------------------------------
# 1. Autouse fixture – fake boto3 creds + the Coral MCM client
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_deps(monkeypatch, mcm_mod):
    """Replace external deps with light fakes for every test."""

    # Fake the credential chain so _get_mcm_client never touches the
    # network or a real profile.
    class _FakeCredentials:
        access_key = "AKIAFAKE"
        secret_key = "secretfake"
        token = "tokenfake"

        def get_frozen_credentials(self):
            return self

    class _FakeBotoSession:
        def __init__(self, **_):
            pass

        def get_credentials(self):
            return _FakeCredentials()

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _FakeBotoSession, raising=True)

    # Replace the whole client-construction boundary so we don't need a
    # real coral orchestrator. Each call returns a fresh MagicMock whose
    # get_cm yields a realistic response; tests that need specific
    # behavior overwrite the cached client.
    def _fake_get_mcm_client(self):
        client = MagicMock(name="ModeledCmApiServiceClient")
        client.get_cm.return_value = _make_get_cm_response()
        return client

    monkeypatch.setattr(mcm_mod.Mcm, "_get_mcm_client", _fake_get_mcm_client, raising=True)

    yield


# ----------------------------------------------------------------------
# 2. Helpers / fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def mcm_mod():
    # Imported lazily (never at module level) so this file is collected
    # via the conftest session-start alias.
    import carlogtt_python_library.amazon_internal.mcm as mcm_mod

    return mcm_mod


@pytest.fixture(scope="session")
def real_get_mcm_client(mcm_mod):
    # Session-scoped so the capture happens before the function-scoped
    # autouse fixture swaps _get_mcm_client for a fake; this lets the
    # credential-path tests drive the *real* client builder.
    return mcm_mod.Mcm._get_mcm_client


@pytest.fixture
def mcm_fresh():
    from carlogtt_python_library.amazon_internal.mcm import Mcm

    return Mcm("us-east-1", caching=False)


@pytest.fixture
def mcm_cached():
    from carlogtt_python_library.amazon_internal.mcm import Mcm

    return Mcm("us-east-1", caching=True)


# ----------------------------------------------------------------------
# 3. Tests – construction / stage validation
# ----------------------------------------------------------------------
def test_default_stage_is_prod(mcm_fresh):
    assert mcm_fresh._mcm_stage == "prod"
    assert mcm_fresh._mcm_endpoint_url.endswith("amazonaws.com")
    assert "beta" not in mcm_fresh._mcm_endpoint_url


def test_beta_stage_selects_beta_endpoint():
    from carlogtt_python_library.amazon_internal.mcm import Mcm

    mcm = Mcm("us-east-1", mcm_stage="beta")
    assert "beta" in mcm._mcm_endpoint_url


def test_invalid_stage_raises():
    from carlogtt_python_library.amazon_internal.mcm import Mcm
    from carlogtt_python_library.exceptions import McmError

    with pytest.raises(McmError):
        Mcm("us-east-1", mcm_stage="gamma")


# ----------------------------------------------------------------------
# 4. Tests – client caching / invalidation
# ----------------------------------------------------------------------
def test_client_cache_and_invalidate(mcm_cached):
    first = mcm_cached._client
    assert first is mcm_cached._client

    mcm_cached.invalidate_client_cache()

    assert first is not mcm_cached._client


def test_fresh_client_not_cached(mcm_fresh):
    # caching disabled => a new client object per access
    assert mcm_fresh._client is not mcm_fresh._client


def test_invalidate_cache_without_caching_raises(mcm_fresh):
    from carlogtt_python_library.exceptions import McmError

    with pytest.raises(McmError):
        mcm_fresh.invalidate_client_cache()


# ----------------------------------------------------------------------
# 5. Tests – get_mcm
# ----------------------------------------------------------------------
def test_get_mcm_returns_expected_dict(mcm_fresh):
    result = mcm_fresh.get_mcm("MCM-12345678")

    assert result == {
        "mcm_id": "MCM-12345678",
        "uuid": "11111111-2222-3333-4444-555555555555",
        "url": "https://mcm.amazon.com/cms/MCM-12345678",
        "title": "Replace antenna controller at MSP501",
        "description": "Swap the failed controller unit.",
        "status": "Scheduled",
        "requester": "alice",
        "technician": "bob",
        "scheduled_start": 1750000000000,
        "scheduled_end": 1750003600000,
    }


def test_get_mcm_passes_friendly_id_to_request(mcm_cached):
    # Use the cached client so we can inspect the exact call args.
    client = mcm_cached._client
    mcm_cached.get_mcm("MCM-87654321")

    assert client.get_cm.call_count == 1
    request = client.get_cm.call_args.args[0]
    # GetCmRequest is the real generated type; its friendly identifier
    # carries the id we passed in.
    assert request.cm_friendly_identifier.friendly_id == "MCM-87654321"


def test_get_mcm_url_uses_response_friendly_id(mcm_cached):
    # Even if the server echoes a different canonical id, the url is
    # built from the response, not the input argument.
    client = mcm_cached._client
    client.get_cm.return_value = _make_get_cm_response(friendly_id="MCM-99999999")

    result = mcm_cached.get_mcm("MCM-00000000")

    assert result["mcm_id"] == "MCM-99999999"
    assert result["url"] == "https://mcm.amazon.com/cms/MCM-99999999"


def test_get_mcm_client_error_raises_mcm_error(mcm_cached):
    from carlogtt_python_library.exceptions import McmError

    client = mcm_cached._client
    client.get_cm.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Unauthorized"}}, "GetCm"
    )

    with pytest.raises(McmError):
        mcm_cached.get_mcm("MCM-12345678")


def test_get_mcm_generic_exception_raises_mcm_error(mcm_cached):
    from carlogtt_python_library.exceptions import McmError

    client = mcm_cached._client
    client.get_cm.side_effect = RuntimeError("service exploded")

    with pytest.raises(McmError):
        mcm_cached.get_mcm("MCM-12345678")


def test_get_mcm_missing_field_raises_mcm_error(mcm_cached):
    from carlogtt_python_library.exceptions import McmError

    # Response missing the nested cm attribute => AttributeError inside
    # get_mcm, which must surface as McmError, not a raw AttributeError.
    client = mcm_cached._client
    client.get_cm.return_value = SimpleNamespace()

    with pytest.raises(McmError):
        mcm_cached.get_mcm("MCM-12345678")


def test_mcm_error_is_carlogtt_python_library_error():
    from carlogtt_python_library.exceptions import CarlogttLibraryError, McmError

    assert issubclass(McmError, CarlogttLibraryError)


# ----------------------------------------------------------------------
# 6. Tests – _get_mcm_client (real client builder, coral faked)
# ----------------------------------------------------------------------
def test_get_mcm_client_builds_orchestrator(monkeypatch, mcm_fresh, mcm_mod, real_get_mcm_client):
    # Drive the real builder (the autouse fixture stubbed it) with a
    # faked coralrpc.new_orchestrator + client so no network is touched.
    captured = {}

    def _fake_new_orchestrator(**kwargs):
        captured.update(kwargs)
        return "ORCHESTRATOR"

    def _fake_client_cls(orchestrator):
        captured["orchestrator_arg"] = orchestrator
        return "MCM_CLIENT"

    monkeypatch.setattr(mcm_mod.coralrpc, "new_orchestrator", _fake_new_orchestrator)
    monkeypatch.setattr(mcm_mod, "ModeledCmApiServiceClient", _fake_client_cls)

    client = real_get_mcm_client(mcm_fresh)

    assert client == "MCM_CLIENT"
    assert captured["orchestrator_arg"] == "ORCHESTRATOR"
    # Signed for the right service/region and the prod endpoint.
    assert captured["aws_service"] == "modeled-cm-api-service"
    assert captured["aws_region"] == "us-east-1"
    assert captured["endpoint"] == mcm_fresh._mcm_endpoint_url
    assert captured["signature_algorithm"] == "v4"
    # Credentials are byte-encoded for coral.
    assert captured["aws_access_key"] == b"AKIAFAKE"
    assert captured["aws_secret_key"] == b"secretfake"
    assert captured["aws_security_token"] == b"tokenfake"


def test_get_mcm_client_none_credentials_raises(monkeypatch, mcm_fresh, real_get_mcm_client):
    from carlogtt_python_library.exceptions import McmError

    class _NoCredSession:
        def __init__(self, **_):
            pass

        def get_credentials(self):
            return None

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _NoCredSession, raising=True)

    with pytest.raises(McmError, match="Failed to resolve AWS credentials"):
        real_get_mcm_client(mcm_fresh)


def test_get_mcm_client_missing_access_key_raises(monkeypatch, mcm_fresh, real_get_mcm_client):
    from carlogtt_python_library.exceptions import McmError

    class _BlankCreds:
        access_key = ""
        secret_key = ""
        token = None

        def get_frozen_credentials(self):
            return self

    class _BlankCredSession:
        def __init__(self, **_):
            pass

        def get_credentials(self):
            return _BlankCreds()

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _BlankCredSession, raising=True)

    with pytest.raises(McmError, match="missing an access key"):
        real_get_mcm_client(mcm_fresh)


def test_get_mcm_client_no_token_passes_none(monkeypatch, mcm_fresh, mcm_mod, real_get_mcm_client):
    # Long-term credentials have no session token; coral should get None.
    captured = {}

    class _NoTokenCreds:
        access_key = "AKIALONGTERM"
        secret_key = "secretlongterm"
        token = None

        def get_frozen_credentials(self):
            return self

    class _NoTokenSession:
        def __init__(self, **_):
            pass

        def get_credentials(self):
            return _NoTokenCreds()

    import boto3.session

    monkeypatch.setattr(boto3.session, "Session", _NoTokenSession, raising=True)
    monkeypatch.setattr(
        mcm_mod.coralrpc, "new_orchestrator", lambda **kw: captured.update(kw) or "O"
    )
    monkeypatch.setattr(mcm_mod, "ModeledCmApiServiceClient", lambda o: "C")

    real_get_mcm_client(mcm_fresh)

    assert captured["aws_security_token"] is None
