# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/utils/test_string_tools.py
# Created 3/13/26 - 10:55 AM UK Time (London) by carlogtt

"""
This module ...
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
def su():
    import carlogtt_python_library as mylib

    return mylib.StringUtils()


# ----------------------------------------------------------------------
# snake_case -----------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("simpleTest", "simple_test"),
        ("simple-Test", "simple_test"),
        ("easy", "easy"),
        ("easy-easy", "easy_easy"),
        ("HTML", "h_t_m_l"),
        ("simpleXML", "simple_x_m_l"),
        ("PDFLoad", "p_d_f_load"),
        ("startMIDDLELast", "start_m_i_d_d_l_e_last"),
        ("AString", "a_string"),
        ("UserID", "user_i_d"),
        ("Test123", "test123"),
        ("Some4Numbers234", "some4_numbers234"),
        ("TEST123String", "t_e_s_t123_string"),
        ("TEST-123String", "t_e_s_t_123_string"),
        ("_TestString", "test_string"),
        ("TestString_", "test_string"),
        ("-TestString", "test_string"),
        ("TestString-", "test_string"),
        ("__TestString", "test_string"),
        ("TestString__", "test_string"),
        ("--TestString", "test_string"),
        ("TestString--", "test_string"),
        ("-_TestString", "test_string"),
        ("TestString_-", "test_string"),
    ],
)
def test_snake_case(su, input_str, expected):
    assert su.snake_case(input_str) == expected


# ----------------------------------------------------------------------
# snake_case_v2 --------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("simpleTest", "simple_test"),
        ("simple-Test", "simple_test"),
        ("easy", "easy"),
        ("easy-easy", "easy_easy"),
        ("HTML", "html"),
        ("simpleXML", "simple_xml"),
        ("PDFLoad", "pdf_load"),
        ("startMIDDLELast", "start_middle_last"),
        ("AString", "a_string"),
        ("UserID", "user_id"),
        ("Test123", "test_123"),
        ("Some4Numbers234", "some_4_numbers_234"),
        ("TEST123String", "test_123_string"),
        ("TEST-123String", "test_123_string"),
        ("_TestString", "_test_string"),
        ("TestString_", "test_string_"),
        ("-TestString", "_test_string"),
        ("TestString-", "test_string_"),
        ("__TestString", "_test_string"),
        ("TestString__", "test_string_"),
        ("--TestString", "_test_string"),
        ("TestString--", "test_string_"),
        ("-_TestString", "_test_string"),
        ("TestString_-", "test_string_"),
    ],
)
def test_snake_case_v2(su, input_str, expected):
    assert su.snake_case_v2(input_str) == expected


# ----------------------------------------------------------------------
# camel_case -----------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("simpleTest", "simpleTest"),
        ("simple-Test", "simpleTest"),
        ("simple test", "simpleTest"),
        ("easy", "easy"),
        ("easy-easy", "easyEasy"),
        ("HTML", "html"),
        ("simpleXML", "simpleXml"),
        ("PDFLoad", "pdfLoad"),
        ("startMIDDLELast", "startMiddleLast"),
        ("AString", "aString"),
        ("UserID", "userId"),
        ("Test123", "test123"),
        ("Some4Numbers234", "some4Numbers234"),
        ("TEST123String", "test123String"),
        ("TEST-123String", "test123String"),
        ("_TestString", "testString"),
        ("TestString_", "testString"),
        ("-TestString", "testString"),
        ("TestString-", "testString"),
        ("__TestString", "testString"),
        ("TestString__", "testString"),
        ("--TestString", "testString"),
        ("TestString--", "testString"),
        ("-_TestString", "testString"),
        ("TestString_-", "testString"),
        ("snake_case_string", "snakeCaseString"),
        ("", ""),
        ("_", ""),
    ],
)
def test_camel_case(su, input_str, expected):
    assert su.camel_case(input_str) == expected


# ----------------------------------------------------------------------
# pascal_case ----------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("simpleTest", "SimpleTest"),
        ("simple-Test", "SimpleTest"),
        ("simple test", "SimpleTest"),
        ("easy", "Easy"),
        ("easy-easy", "EasyEasy"),
        ("HTML", "Html"),
        ("simpleXML", "SimpleXml"),
        ("PDFLoad", "PdfLoad"),
        ("startMIDDLELast", "StartMiddleLast"),
        ("AString", "AString"),
        ("UserID", "UserId"),
        ("Test123", "Test123"),
        ("Some4Numbers234", "Some4Numbers234"),
        ("TEST123String", "Test123String"),
        ("TEST-123String", "Test123String"),
        ("_TestString", "TestString"),
        ("TestString_", "TestString"),
        ("-TestString", "TestString"),
        ("TestString-", "TestString"),
        ("__TestString", "TestString"),
        ("TestString__", "TestString"),
        ("--TestString", "TestString"),
        ("TestString--", "TestString"),
        ("-_TestString", "TestString"),
        ("TestString_-", "TestString"),
        ("snake_case_string", "SnakeCaseString"),
        ("", ""),
        ("_", ""),
    ],
)
def test_pascal_case(su, input_str, expected):
    assert su.pascal_case(input_str) == expected
