# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/amazon_internal/coral.py
# Created 12/3/25 - 9:59 AM UK Time (London) by carlogtt

"""
This module contains a lightweight router to expose a Coral RPC
service as REST-style routes on AWS Lambda behind API Gateway.
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
import functools
import json
import logging
from collections.abc import Callable
from typing import Any, Optional, TypeAlias

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    "CoralRouter",
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
AnyCallableT: TypeAlias = Callable[..., Any]


class CoralRouter:
    """
    A lightweight router that registers REST-style routes with
    decorators and rewrites Coral RPC-style requests (POST to /
    with an X-Amz-Target header) into REST-style API Gateway
    events so they can be dispatched to the registered routes.

    :param prefix: The path prefix applied to every registered
           route (e.g. "/api/v1"). Defaults to no prefix.
    """

    _ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"}

    def __init__(self, prefix: Optional[str] = None):
        self._routes: dict[tuple[str, str], AnyCallableT] = {}
        self._operations: dict[str, tuple[str, str]] = {}
        self._prefix = prefix if prefix is not None else ""

    @property
    def operations(self) -> dict[str, tuple[str, str]]:
        """
        Get the operations dictionary.
        """

        return self._operations

    def transform_rpc_to_rest(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Transform an RPC-style request to a REST-style request.

        Extracts the operation name from the X-Amz-Target header and
        converts the RPC request (POST to /) into a REST request
        with proper HTTP method, path, and parameters. i.e. an event
        with X-Amz-Target "com.example.Service.GetUser" and body
        {"userId": "123"} transforms to GET /users/123.

        :param event: The API Gateway event containing the RPC-style
               request.
        :return: The transformed event with REST-style routing
                 (httpMethod, path, pathParameters, resource).
        :raise CoralRouterError: If the operation is not found, the
               request body is not valid JSON, or required path
               parameters are missing.
        """

        # Extract operation from X-Amz-Target header
        headers = event.get("headers", {})
        target = headers.get("X-Amz-Target", "com.amazon.NoOp")

        # Parse operation name:
        # "com.amazon.domain.CoralService.Operation"
        operation = target.split(".")[-1]

        if operation not in self._operations:
            raise exceptions.CoralRouterError(f"Operation {operation} not found")

        # Extract params from body and map to path
        try:
            params = json.loads(event.get("body", "{}"))
        except (TypeError, ValueError) as ex:
            raise exceptions.CoralRouterError(f"Invalid JSON body: {event.get('body')!r}") from ex

        method, resource = self._operations[operation]
        path = resource

        if "{" in resource and "}" in resource:
            # Replace resource params (e.g., {siteId} with actual value)
            for key, value in params.items():
                path = path.replace(f"{{{key}}}", str(value))
            if "{" in path and "}" in path:
                raise exceptions.CoralRouterError(
                    f"Operation {operation} is missing path parameter values in {path}"
                )

        # Rewrite event
        event["resource"] = resource
        event["path"] = path
        event["pathParameters"] = params
        event["httpMethod"] = method

        return event

    def route(
        self, operation: str, path: str, method: str
    ) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Register a route with the specified method and path.

        :param operation: The Coral operation name (e.g. "Echo").
        :param path: The path for the route (e.g. "/api/v1/sites").
        :param method: The HTTP method for the route (e.g. "GET",
               "POST").
        :return: A decorator function that registers the route.
        :raise CoralRouterError: If the method is not a valid HTTP
               method or the route/operation is already registered.
        """

        def decorator(func: AnyCallableT) -> AnyCallableT:
            """
            Decorator function to register a route.
            """

            method_nor = method.upper()
            path_nor = f"{self._prefix}{path}"
            operation_nor = operation.strip()
            key_nor = (method_nor, path_nor)

            if method_nor not in self._ALLOWED_METHODS:
                raise exceptions.CoralRouterError(f"Invalid HTTP method {method}")
            if key_nor in self._routes:
                raise exceptions.CoralRouterError(f"Route {method} {path} already registered")
            if operation_nor in self._operations:
                raise exceptions.CoralRouterError(f"Operation {operation} already registered")

            self._routes[key_nor] = func
            self._operations[operation_nor] = key_nor

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                """
                Wrapper function to handle the route logic.
                This function is called when the route is invoked.
                """

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Get route decorator with GET `method`
        """

        return self.route(operation, path, "GET")

    def post(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Post route decorator with POST `method`
        """

        return self.route(operation, path, "POST")

    def put(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Put route decorator with PUT `method`
        """

        return self.route(operation, path, "PUT")

    def delete(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Delete route decorator with DELETE `method`
        """

        return self.route(operation, path, "DELETE")

    def patch(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Patch route decorator with PATCH `method`
        """

        return self.route(operation, path, "PATCH")

    def head(self, operation: str, path: str) -> Callable[[AnyCallableT], AnyCallableT]:
        """
        Head route decorator with HEAD `method`
        """

        return self.route(operation, path, "HEAD")
