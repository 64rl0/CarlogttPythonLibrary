# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/utils/test_pagination.py
# Created 9/8/26 - 3:31 PM UK Time (London) by carlogtt

"""
This module tests the Paginator class.
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
import base64
import re

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
# Fixture --------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def paginator():
    import carlogtt_python_library as mylib

    return mylib.Paginator(default_page_size=3, max_page_size=5)


# ----------------------------------------------------------------------
# Constructor ----------------------------------------------------------
# ----------------------------------------------------------------------
def test_constructor_defaults():
    import carlogtt_python_library as mylib

    paginator = mylib.Paginator()

    assert paginator.default_page_size == 50
    assert paginator.max_page_size == 100


def test_constructor_default_equal_to_max_is_valid():
    import carlogtt_python_library as mylib

    paginator = mylib.Paginator(default_page_size=5, max_page_size=5)

    assert paginator.normalize_page_size(None) == 5


@pytest.mark.parametrize(
    "default_page_size, max_page_size",
    [
        (0, 100),
        (-1, 100),
        (10, 9),
        (10, 0),
    ],
)
def test_constructor_invalid_config_raises(default_page_size, max_page_size):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.PaginationError):
        mylib.Paginator(default_page_size=default_page_size, max_page_size=max_page_size)


# ----------------------------------------------------------------------
# normalize_page_size --------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "max_results, expected",
    [
        (None, 3),
        (1, 1),
        (0, 1),
        (-10, 1),
        (4, 4),
        (5, 5),
        (6, 5),
        (100, 5),
    ],
)
def test_normalize_page_size(paginator, max_results, expected):
    assert paginator.normalize_page_size(max_results) == expected


# ----------------------------------------------------------------------
# encode_cursor / decode_cursor ----------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        {"equipment_id": "eq-123"},
        {"created_at": "2026-09-08T10:00:00Z", "equipment_id": "eq-123"},
        {},
        {"name": "città università"},
        {"arn": "arn:aws:cloudwatch:us-east-1:123:alarm:my:alarm"},
        {"empty": ""},
    ],
)
def test_cursor_round_trip(paginator, payload):
    token = paginator.encode_cursor(payload)

    assert paginator.decode_cursor(token) == payload


def test_encode_cursor_is_deterministic(paginator):
    token_a = paginator.encode_cursor({"a": "1", "b": "2"})
    token_b = paginator.encode_cursor({"b": "2", "a": "1"})

    assert token_a == token_b


def test_encode_cursor_is_url_safe(paginator):
    token = paginator.encode_cursor({"key": "value with spaces & symbols ~!?"})

    assert re.fullmatch(r"[A-Za-z0-9_\-=]+", token)


@pytest.mark.parametrize(
    "payload",
    [
        "not-a-dict",
        ["a", "b"],
        None,
        {"a": 1},
        {"a": None},
        {1: "a"},
        {"a": {"nested": "dict"}},
    ],
)
def test_encode_cursor_invalid_payload_raises(paginator, payload):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.PaginationError):
        paginator.encode_cursor(payload)


@pytest.mark.parametrize(
    "token",
    [
        "",
        "not a valid token !!!",
        base64.urlsafe_b64encode(b"not json").decode(),
        base64.urlsafe_b64encode(b'["a", "b"]').decode(),
        base64.urlsafe_b64encode(b'"just a string"').decode(),
        base64.urlsafe_b64encode(b'{"a": 1}').decode(),
        base64.urlsafe_b64encode(b'{"a": null}').decode(),
        base64.urlsafe_b64encode(b'{"a": {"b": "c"}}').decode(),
    ],
)
def test_decode_cursor_invalid_token_raises(paginator, token):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.PaginationError):
        paginator.decode_cursor(token)


def test_decode_cursor_error_chains_original_exception(paginator):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.PaginationError) as exc_info:
        paginator.decode_cursor(base64.urlsafe_b64encode(b"not json").decode())

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_pagination_error_is_library_error(paginator):
    import carlogtt_python_library as mylib

    with pytest.raises(mylib.CarlogttLibraryError):
        paginator.decode_cursor("not a valid token !!!")


# ----------------------------------------------------------------------
# paginate -------------------------------------------------------------
# ----------------------------------------------------------------------
def test_paginate_fewer_items_than_page_size(paginator):
    items = ["a", "b"]

    page, next_token = paginator.paginate(items, cursor_factory=lambda item: {"last": item})

    assert page == ["a", "b"]
    assert next_token is None


def test_paginate_empty_items(paginator):
    page, next_token = paginator.paginate([], cursor_factory=lambda item: {"last": item})

    assert page == []
    assert next_token is None


def test_paginate_exact_page_size_has_no_next_token(paginator):
    items = ["a", "b", "c"]

    page, next_token = paginator.paginate(items, cursor_factory=lambda item: {"last": item})

    assert page == ["a", "b", "c"]
    assert next_token is None


def test_paginate_more_items_returns_next_token(paginator):
    items = ["a", "b", "c", "d", "e"]

    page, next_token = paginator.paginate(items, cursor_factory=lambda item: {"last": item})

    assert page == ["a", "b", "c"]
    assert next_token is not None
    assert paginator.decode_cursor(next_token) == {"last": "c"}


def test_paginate_respects_max_results(paginator):
    items = ["a", "b", "c", "d", "e"]

    page, next_token = paginator.paginate(
        items, cursor_factory=lambda item: {"last": item}, max_results=2
    )

    assert page == ["a", "b"]
    assert paginator.decode_cursor(next_token) == {"last": "b"}


def test_paginate_clamps_max_results(paginator):
    items = ["a", "b", "c", "d", "e", "f", "g"]

    page, next_token = paginator.paginate(
        items, cursor_factory=lambda item: {"last": item}, max_results=100
    )

    assert page == ["a", "b", "c", "d", "e"]
    assert paginator.decode_cursor(next_token) == {"last": "e"}


def test_paginate_accepts_any_sequence_and_returns_list(paginator):
    items = ("a", "b", "c", "d")

    page, next_token = paginator.paginate(items, cursor_factory=lambda item: {"last": item})

    assert isinstance(page, list)
    assert page == ["a", "b", "c"]
    assert next_token is not None


def test_paginate_full_walk_visits_all_items_once(paginator):
    items = [f"{i:02d}" for i in range(10)]
    collected = []
    next_token = None

    while True:
        if next_token is None:
            remaining = items
        else:
            cursor = paginator.decode_cursor(next_token)
            remaining = [item for item in items if item > cursor["last"]]

        page, next_token = paginator.paginate(remaining, cursor_factory=lambda item: {"last": item})
        collected.extend(page)

        if next_token is None:
            break

    assert collected == items
