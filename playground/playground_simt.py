# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/playground_simt.py
# Created 2/20/25 - 12:21 PM UK Time (London) by carlogtt
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
from _playground_base import master_logger

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
profile = "amz_inventory_tool_app_prod"
simt = mylib.SimT(aws_region_name=region, aws_profile_name=profile)


def ticket_details():
    det = simt.get_ticket_details('53170900-0845-4c41-b6a1-f3cedeb7374b')
    pprint(det)


def ticket_update():
    ticket_id = '53170900-0845-4c41-b6a1-f3cedeb7374b'
    payload = {'status': 'Assigned'}
    simt.update_ticket(ticket_id, payload)


def get_tickets():
    filters = {'requesters': [{'namespace': 'MIDWAY', 'value': 'carlogtt'}]}
    response = simt.get_tickets(filters=filters)
    for ticket in response:
        print(ticket)


if __name__ == '__main__':
    funcs = [
        ticket_details,
        # ticket_update,
        # get_tickets,
    ]

    for func in funcs:
        print()
        print("Calling: ", func.__name__)
        pprint(func())
        print("*" * 30 + "\n")
