# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_mirador.py
# Created 3/24/25 - 8:31 PM UK Time (London) by carlogtt
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
from pprint import pprint

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
# module_logger =

# Type aliases
#


region = "eu-north-1"
profile = "akhjones_dev"
mirador = mylib.Mirador(
    aws_region_name=region,
    mirador_role_arn='arn:aws:iam::376204018982:role/mirador-api-D222006546-gamma-arn',
    mirador_external_id='91c7248a-a87a-40a7-9dbd-e0d88fb27c20',
    mirador_api_key='CXc5qfkpmr5zf7eGowwgA75ZDHL4XOTP6uLACgL4',
    mirador_stage='gamma',
    aws_profile_name=profile,
    client_parameters={},
    caching=True,
)


def get_finding_attributes():
    response = mirador.get_finding_attributes()
    pprint(response)


def get_resource_attributes():
    response = mirador.get_resource_attributes()
    pprint(response)


if __name__ == '__main__':
    funcs = [
        get_finding_attributes,
        get_resource_attributes,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
