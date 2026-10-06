# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/utils/pagination.py
# Created 9/8/26 - 3:31 PM UK Time (London) by carlogtt

"""
This module contains utilities for cursor-based pagination of list
results using opaque, URL-safe cursor tokens.
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
# These exceptions may be necessary due to specific coding requirements
# or to bypass false positives.
# ======================================================================
#

# ======================================================================
# IMPORTS
# Importing required libraries and modules for the application.
# ======================================================================

# Standard Library Imports
import base64
import json
import logging
from collections.abc import Callable, Sequence
from typing import Any, Optional, TypeGuard, TypeVar

# Local Folder (Relative) Imports
from .. import exceptions

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'Paginator',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
ItemType = TypeVar('ItemType')


class Paginator:
    """
    A collection of utilities to paginate list results with opaque,
    URL-safe cursor tokens.

    The cursor payload is a flat dict with str keys and str values
    chosen by the caller (i.e. the sort-key fields of the last item
    of a page). Tokens are deterministic for a given payload and must
    be treated as opaque by clients and passed back verbatim.

    Tokens are NOT signed nor encrypted, therefore the decoded
    payload must be treated as untrusted client input.

    :param default_page_size: The page size used when a request does
           not specify one. Must be >= 1 and <= max_page_size.
    :param max_page_size: The hard upper bound for the page size.
    :param logger: The logging.Logger instance to be used for
           logging. If not explicitly provided, the module uses
           Python's standard logging module as a default logger.
    :raise PaginationError: If the page size configuration is
           invalid.
    """

    def __init__(
        self,
        default_page_size: int = 50,
        max_page_size: int = 100,
        logger: logging.Logger = module_logger,
    ) -> None:
        if default_page_size < 1:
            raise exceptions.PaginationError(
                f"Invalid default_page_size: {default_page_size!r} must be >= 1"
            )

        if max_page_size < default_page_size:
            raise exceptions.PaginationError(
                f"Invalid max_page_size: {max_page_size!r} must be >="
                f" default_page_size ({default_page_size!r})"
            )

        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        self.logger = logger

    def normalize_page_size(self, max_results: Optional[int]) -> int:
        """
        Return the effective page size for a request.

        When max_results is None the configured default page size is
        returned, otherwise the value is clamped into the range
        [1, max_page_size].

        :param max_results: The page size requested by the caller, or
               None if the caller did not specify one.
        :return: The effective page size.
        """

        if max_results is None:
            return self.default_page_size

        page_size = max(1, min(max_results, self.max_page_size))

        return page_size

    def encode_cursor(self, payload: dict[str, str]) -> str:
        """
        Encode a resume-after cursor payload into an opaque, URL-safe
        token.

        Encoding is deterministic: the same payload always produces
        the same token, regardless of the payload key order.

        :param payload: The cursor payload. It must be a flat dict
               with str keys and str values.
        :return: The opaque URL-safe token.
        :raise PaginationError: If the payload is not a flat dict
               with str keys and str values.
        """

        if not self._is_valid_payload(payload):
            raise exceptions.PaginationError(f"Invalid pagination payload: {payload!r}")

        raw = json.dumps(payload, sort_keys=True).encode()
        token = base64.urlsafe_b64encode(raw).decode()

        self.logger.debug(f"Encoded pagination cursor with keys: {sorted(payload)}")

        return token

    def decode_cursor(self, token: str) -> dict[str, str]:
        """
        Decode an opaque cursor token back into its payload.

        Tokens are opaque and must be passed back verbatim, therefore
        a token that does not decode to the expected shape is treated
        as a caller error. Tokens are not signed, so treat the
        decoded payload as untrusted client input.

        :param token: The opaque token to decode.
        :return: The decoded cursor payload.
        :raise PaginationError: If the token is not a valid
               pagination token.
        """

        try:
            raw = base64.urlsafe_b64decode(token.encode())
            payload = json.loads(raw)

        except ValueError as ex:
            raise exceptions.PaginationError(f"Invalid pagination token: {token!r}") from ex

        if not self._is_valid_payload(payload):
            raise exceptions.PaginationError(f"Invalid pagination token: {token!r}")

        self.logger.debug(f"Decoded pagination cursor with keys: {sorted(payload)}")

        return payload

    def paginate(
        self,
        items: Sequence[ItemType],
        *,
        cursor_factory: Callable[[ItemType], dict[str, str]],
        max_results: Optional[int] = None,
    ) -> tuple[list[ItemType], Optional[str]]:
        """
        Slice a single page off items and build the token for the
        next page.

        The items sequence must already be sorted and filtered down
        to the items following the cursor of the previous page.
        Resume-after filtering is domain specific and is the caller
        responsibility.

        :param items: The sorted sequence of the remaining items.
        :param cursor_factory: A callable that receives the last item
               of the page and returns its cursor payload.
        :param max_results: The page size requested by the caller, or
               None to use the configured default page size.
        :return: A tuple of (page, next_token). next_token is None
                 when there are no more items after this page.
        :raise PaginationError: If the payload returned by the
               cursor_factory is not a flat dict with str keys and
               str values.
        """

        page_size = self.normalize_page_size(max_results)
        page = list(items[:page_size])

        next_token: Optional[str] = None
        if len(items) > page_size:
            next_token = self.encode_cursor(cursor_factory(page[-1]))

        self.logger.debug(
            f"Paginated {len(items)} items into a page of {len(page)}"
            f" (more_pages={next_token is not None})"
        )

        return page, next_token

    @staticmethod
    def _is_valid_payload(payload: Any) -> TypeGuard[dict[str, str]]:
        """
        Return True if payload is a flat dict with str keys and str
        values.
        """

        is_valid = isinstance(payload, dict) and all(
            isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
        )

        return is_valid
