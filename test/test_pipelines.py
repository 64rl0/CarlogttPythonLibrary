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
pipelines = mylib.Pipelines(
    aws_region_name=region,
    aws_profile_name=profile,
    caching=True,
    client_parameters={},
)


def get_pipeline_structure():
    response = pipelines.get_pipeline_structure(pipeline_name="ADC-OAR")

    return response


def pipelines_throttling():
    counter = 0
    while True:
        counter += 1
        response = pipelines.get_pipeline_structure(pipeline_name="ADC-OAR")
        print(response)
        if counter == 20:
            break

    return response


if __name__ == '__main__':
    funcs = [
        get_pipeline_structure,
        # pipelines_throttling,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
