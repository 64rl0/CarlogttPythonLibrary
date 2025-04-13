# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_tickety.py
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
from unittest.mock import MagicMock

# Third Party Library Imports
import botocore.exceptions
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
profile = "amz_inventory_tool_app_prod"
simt = mylib.SimT(aws_region_name=region, aws_profile_name=profile)


def test_update_ticket_success():
    mock_client = MagicMock()
    simt = mylib.SimT(region)
    simt._cache['client'] = mock_client

    mock_client.update_ticket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

    try:
        simt.update_ticket("TICKET123", {"status": "closed"})
    except mylib.SimTError:
        assert True, "update_ticket() raised SimTError unexpectedly!"


def test_update_ticket_client_error():
    mock_client = MagicMock()
    simt = mylib.SimT(region)
    simt._cache['client'] = mock_client

    mock_client.update_ticket.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Unauthorized"}}, "UpdateTicket"
    )

    try:
        simt.update_ticket("TICKET123", {"status": "closed"})
        assert False, "Expected SimTError but none was raised."
    except mylib.SimTError as e:
        assert isinstance(e, mylib.SimTError)


def test_update_ticket_generic_exception():
    mock_client = MagicMock()
    simt = mylib.SimT(region)
    simt._cache['client'] = mock_client

    mock_client.update_ticket.side_effect = Exception("Unexpected error")

    try:
        simt.update_ticket("TICKET123", {"status": "closed"})
        assert False, "Expected SimTError but none was raised."
    except mylib.SimTError as e:
        assert isinstance(e, mylib.SimTError)


def test_update_ticket_invalid_response():
    mock_client = MagicMock()
    simt = mylib.SimT(region)
    simt._cache['client'] = mock_client

    mock_client.update_ticket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    try:
        simt.update_ticket("TICKET123", {"status": "closed"})
        assert False, "Expected SimTError but none was raised."
    except mylib.SimTError as e:
        assert isinstance(e, mylib.SimTError)


def test_update_ticket_invalid_response_type():
    mock_client = MagicMock()
    simt = mylib.SimT(region)
    simt._cache['client'] = mock_client

    mock_client.update_ticket.return_value = None

    try:
        simt.update_ticket("TICKET123", {"status": "closed"})
        assert False, "Expected SimTError but none was raised."
    except mylib.SimTError as e:
        assert isinstance(e, mylib.SimTError)


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
