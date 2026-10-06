# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/amazon_internal/test_coral.py
# Created 9/9/26 - 2:04 PM UK Time (London) by carlogtt

"""
This module tests the CoralRouter class.
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
import json
from typing import Any

# Third Party Library Imports
import pytest

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


# ----------------------------------------------------------------------
# Fixtures -------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def router():
    import carlogtt_python_library as mylib

    return mylib.CoralRouter()


@pytest.fixture
def registered_router(router):
    @router.get("GetUser", "/users/{userId}")
    def get_user():
        return "get_user"

    @router.post("CreateUser", "/users")
    def create_user():
        return "create_user"

    @router.delete("DeleteDevice", "/sites/{siteId}/devices/{deviceId}")
    def delete_device():
        return "delete_device"

    return router


def make_event(target=None, body=None):
    event: dict[str, Any] = {"headers": {}, "httpMethod": "POST", "path": "/"}

    if target is not None:
        event["headers"]["X-Amz-Target"] = target
    if body is not None:
        event["body"] = json.dumps(body)

    return event


# ----------------------------------------------------------------------
# route registration ---------------------------------------------------
# ----------------------------------------------------------------------
def test_operations_empty_by_default(router):
    assert router.operations == {}


def test_route_registers_operation(router):
    @router.route("Echo", "/echo", "GET")
    def echo():
        return "echo"

    assert router.operations == {"Echo": ("GET", "/echo")}


@pytest.mark.parametrize(
    "decorator_name, expected_method",
    [
        ("get", "GET"),
        ("post", "POST"),
        ("put", "PUT"),
        ("delete", "DELETE"),
        ("patch", "PATCH"),
        ("head", "HEAD"),
    ],
)
def test_convenience_decorators_register_method(router, decorator_name, expected_method):
    decorator = getattr(router, decorator_name)

    @decorator("Echo", "/echo")
    def echo():
        return "echo"

    assert router.operations == {"Echo": (expected_method, "/echo")}


def test_route_method_is_case_insensitive(router):
    @router.route("Echo", "/echo", "get")
    def echo():
        return "echo"

    assert router.operations == {"Echo": ("GET", "/echo")}


def test_route_operation_name_is_stripped(router):
    @router.route("  Echo  ", "/echo", "GET")
    def echo():
        return "echo"

    assert router.operations == {"Echo": ("GET", "/echo")}


def test_route_applies_prefix(registered_router):
    import carlogtt_python_library as mylib

    prefixed_router = mylib.CoralRouter(prefix="/api/v1")

    @prefixed_router.get("GetUser", "/users/{userId}")
    def get_user():
        return "get_user"

    assert prefixed_router.operations == {"GetUser": ("GET", "/api/v1/users/{userId}")}


@pytest.mark.parametrize("method", ["OPTIONS", "TRACE", "FOO", ""])
def test_route_invalid_method_raises(router, method):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.CoralRouterError):

        @router.route("Echo", "/echo", method)
        def echo():
            return "echo"


def test_route_duplicate_route_raises(registered_router):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.CoralRouterError):

        @registered_router.post("CreateUserAgain", "/users")
        def create_user_again():
            return "create_user_again"


def test_route_duplicate_operation_raises(registered_router):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.CoralRouterError):

        @registered_router.get("GetUser", "/users-v2/{userId}")
        def get_user_v2():
            return "get_user_v2"


def test_route_same_path_different_method_is_valid(registered_router):
    @registered_router.get("ListUsers", "/users")
    def list_users():
        return "list_users"

    assert registered_router.operations["ListUsers"] == ("GET", "/users")
    assert registered_router.operations["CreateUser"] == ("POST", "/users")


def test_decorated_function_is_still_callable(router):
    @router.get("Echo", "/echo")
    def echo(value):
        return value

    assert echo("hello") == "hello"


def test_decorator_preserves_function_metadata(router):
    @router.get("Echo", "/echo")
    def echo():
        """Echo docstring."""
        return "echo"

    assert echo.__name__ == "echo"
    assert echo.__doc__ == "Echo docstring."


# ----------------------------------------------------------------------
# transform_rpc_to_rest ------------------------------------------------
# ----------------------------------------------------------------------
def test_transform_resolves_path_parameter(registered_router):
    event = make_event("com.example.UserService.GetUser", {"userId": "123"})

    result = registered_router.transform_rpc_to_rest(event)

    assert result["httpMethod"] == "GET"
    assert result["path"] == "/users/123"
    assert result["resource"] == "/users/{userId}"
    assert result["pathParameters"] == {"userId": "123"}


def test_transform_mutates_and_returns_same_event(registered_router):
    event = make_event("com.example.UserService.GetUser", {"userId": "123"})

    result = registered_router.transform_rpc_to_rest(event)

    assert result is event


def test_transform_static_path_keeps_resource(registered_router):
    event = make_event("com.example.UserService.CreateUser", {"name": "carlo"})

    result = registered_router.transform_rpc_to_rest(event)

    assert result["httpMethod"] == "POST"
    assert result["path"] == "/users"
    assert result["resource"] == "/users"
    assert result["pathParameters"] == {"name": "carlo"}


def test_transform_resolves_multiple_path_parameters(registered_router):
    event = make_event(
        "com.example.DeviceService.DeleteDevice", {"siteId": "s-1", "deviceId": "d-2"}
    )

    result = registered_router.transform_rpc_to_rest(event)

    assert result["httpMethod"] == "DELETE"
    assert result["path"] == "/sites/s-1/devices/d-2"


def test_transform_stringifies_non_string_parameters(registered_router):
    event = make_event("com.example.UserService.GetUser", {"userId": 42})

    result = registered_router.transform_rpc_to_rest(event)

    assert result["path"] == "/users/42"


def test_transform_extra_body_keys_are_kept_in_path_parameters(registered_router):
    event = make_event("com.example.UserService.GetUser", {"userId": "123", "verbose": "true"})

    result = registered_router.transform_rpc_to_rest(event)

    assert result["path"] == "/users/123"
    assert result["pathParameters"] == {"userId": "123", "verbose": "true"}


@pytest.mark.parametrize(
    "target",
    [
        "com.amazon.domain.UserService.GetUser",
        "UserService.GetUser",
        "GetUser",
    ],
)
def test_transform_extracts_operation_from_any_target_depth(registered_router, target):
    event = make_event(target, {"userId": "123"})

    result = registered_router.transform_rpc_to_rest(event)

    assert result["path"] == "/users/123"


def test_transform_unknown_operation_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.UserService.UnknownOp", {})

    with pytest.raises(mylib.CoralRouterError):
        registered_router.transform_rpc_to_rest(event)


def test_transform_missing_target_header_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event(target=None, body={"userId": "123"})

    with pytest.raises(mylib.CoralRouterError):
        registered_router.transform_rpc_to_rest(event)


def test_transform_missing_path_parameter_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.UserService.GetUser", {})

    with pytest.raises(mylib.CoralRouterError):
        registered_router.transform_rpc_to_rest(event)


def test_transform_partial_path_parameters_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.DeviceService.DeleteDevice", {"siteId": "s-1"})

    with pytest.raises(mylib.CoralRouterError):
        registered_router.transform_rpc_to_rest(event)


def test_transform_malformed_json_body_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.UserService.CreateUser")
    event["body"] = "not valid json {"

    with pytest.raises(mylib.CoralRouterError) as exc_info:
        registered_router.transform_rpc_to_rest(event)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_transform_null_body_raises(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.UserService.CreateUser")
    event["body"] = None

    with pytest.raises(mylib.CoralRouterError):
        registered_router.transform_rpc_to_rest(event)


def test_coral_error_is_library_error(registered_router):
    import carlogtt_python_library as mylib

    event = make_event("com.example.UserService.UnknownOp", {})

    with pytest.raises(mylib.CarlogttLibraryError):
        registered_router.transform_rpc_to_rest(event)


def test_transform_missing_body_defaults_to_empty_params(registered_router):
    event = make_event("com.example.UserService.CreateUser", body=None)

    result = registered_router.transform_rpc_to_rest(event)

    assert result["path"] == "/users"
    assert result["pathParameters"] == {}
