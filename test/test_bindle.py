# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_bindle.py
# Created 4/8/25 - 2:10 PM UK Time (London) by carlogtt
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

# Third Party Library Imports
from test__entrypoint__ import master_logger

# My Library Imports
import carlogtt_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
module_logger = master_logger.get_child_logger(__name__)

# Type aliases
#

region = "eu-west-1"
profile = "carlogtt-isengard-dev"
bindle = mylib.Bindle(
    aws_region_name=region,
    aws_profile_name=profile,
    caching=True,
    client_parameters={},
)


def get_resource():
    bindle_id = 'amzn1.bindle.resource.5opbe5frefojjq7wucqq'
    response = bindle.describe_resource(bindle_id=bindle_id)

    return response


def get_bindles_team():
    team_id = 'carlogtt'
    response = bindle.find_bindles_by_owner_with_team_id(team_id=team_id)

    return response


def get_package_info():
    package_name = 'CarlogttLibrary'
    response = bindle.describe_package(package_name=package_name)

    return response


def bindle_throttling():
    bindle_id = 'amzn1.bindle.resource.5opbe5frefojjq7wucqq'
    counter = 0
    while True:
        counter += 1
        response = bindle.describe_resource(bindle_id=bindle_id)
        print(response)
        if counter == 20:
            break

    return response


if __name__ == '__main__':
    funcs = [
        # get_resource,
        get_package_info,
        # get_bindles_team,
        # bindle_throttling,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
