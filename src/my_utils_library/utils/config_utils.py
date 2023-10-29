# MODULE DETAILS
# config_utils.py
# Created 9/27/23 - 4:21 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module ...
"""

# IMPORTS
# Importing required libraries and modules for the application.

# Standard Library Imports
import json
import os

# Third Party Library Imports
import boto3
from bender import apollo_environment_info
from bender.apollo_error import ApolloError
from botocore.exceptions import ClientError

# END IMPORTS


# List of public names in the module
__all__ = [
    'get_application_root',
    'get_secret',
]


def get_application_root() -> str:
    try:
        return os.path.abspath(apollo_environment_info.ApolloEnvironmentInfo().root)
    except ApolloError:
        return os.path.abspath(apollo_environment_info.BrazilBootstrapEnvironmentInfo().root)


def get_secret(secret_name: str, aws_secrets_manager_region: str = "eu-west-1") -> str:
    """
    Get secret from AWS Secrets Manager.

    :param secret_name: secret to retrieve from secrets manager.
    :param aws_secrets_manager_region: this is the aws account region
           where the secret manager is located.
    :return: secret value as a string.
    """

    # AWS_PROFILE is injected locally for local development testing
    # through Brazil. When running on NAWS this env variable is not set
    aws_profile = os.environ.get('AWS_PROFILE')

    session = boto3.session.Session(profile_name=aws_profile)
    client = session.client(service_name='secretsmanager', region_name=aws_secrets_manager_region)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']

    # If secret is not found return an empty string
    except ClientError:
        secret = ""

    # If secret is found load the string to Python dict and get
    # the password
    else:
        secret_json = json.loads(secret)
        secret = secret_json.get('password', "")

    return secret
