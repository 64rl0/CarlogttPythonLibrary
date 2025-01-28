# flake8: noqa
# mypy: ignore-errors

# Third Party Library Imports
import pytest


def test_that_you_wrote_tests():
    from textwrap import dedent

    assertion_string = dedent("""\
    No, you have not written tests.

    However, unless a test is run, the pytest execution will fail
    due to no tests or missing coverage. So, write a real test and
    then remove this!
    """)
    assert True, assertion_string


def test_carlogtt_library_importable():
    import carlogtt_library
