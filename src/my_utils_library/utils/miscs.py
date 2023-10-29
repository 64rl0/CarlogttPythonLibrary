# MODULE DETAILS
# miscs.py
# Created 8/9/23 - 11:34 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module provides a set of various utilities.
"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import ctypes

# END IMPORTS


# List of public names in the module
__all__ = [
    'ref_count',
]


def ref_count(obj_id: int) -> int:
    return ctypes.c_long.from_address(obj_id).value
