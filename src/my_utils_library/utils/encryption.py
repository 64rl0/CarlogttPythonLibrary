# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# encryption.py
# Created 10/2/23 - 9:25 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
This module provides functions and utilities for password encryption.
It offers encryption algorithms and techniques specifically designed for
securely storing and handling passwords.
"""

# ======================================================================
# EXCEPTIONS
# This section documents any exceptions made or code quality rules.
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
import logging
import os

# Third Party Library Imports
import cryptography.fernet
import cryptography.hazmat.primitives.kdf.scrypt

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'hash_string',
    'validate_hash_match',
    'encrypt_string',
    'decrypt_string',
    'generate_random_secret_key',
]


def _get_scrypt_kdf(salt: bytes) -> cryptography.hazmat.primitives.kdf.scrypt.Scrypt:
    """
    Scrypt is a KDF, Key Derivation Function, designed for password
    storage by Colin Percival to be resistant against hardware-assisted
    attackers by having a tunable memory cost.
    """

    # Scrypt configuration
    length = 32  # The desired length of the derived key in bytes
    n = 2**14  # CPU/Memory cost parameter. It must be larger than 1 and be a power of 2
    r = 8  # Block size parameter
    p = 1  # Parallelization parameter

    kdf = cryptography.hazmat.primitives.kdf.scrypt.Scrypt(salt=salt, length=length, n=n, r=r, p=p)

    return kdf


def hash_string(raw_string: str, fernet_key: str) -> bytes:
    """Hash string with Scrypt for password storage in database"""

    # Encode raw_password to bytes
    b_raw_string = raw_string.encode()

    # Generate a random salt for the password encryption
    salt = os.urandom(32)
    # Encode the salt to url-safe byte array and strip last '=' at the
    # end as a 32 bytes array always ends with a '='
    salt_url_safe_and_clean = base64.urlsafe_b64encode(salt).strip(b'=')

    # Derive key using Scrypt
    kdf = _get_scrypt_kdf(salt)
    b_hashed_string = kdf.derive(b_raw_string)

    # Encode derived_key to url-safe byte array and
    # Strip last '=' at the end as '_get_scrypt_kdf' always return a
    # 32 bytes array which ends with a '='
    b_hashed_string_url_safe_and_clean = base64.urlsafe_b64encode(b_hashed_string).strip(b'=')

    # Embed salt into hashed string joining them together with byte '&'
    b_hashed_string_salt_combined = (
        b_hashed_string_url_safe_and_clean + b'&' + salt_url_safe_and_clean
    )

    # Encode b_hashed_string_salt_combined to url-safe byte array to
    # remote the special '&' and Strip last '=' at the end as a 65 bytes
    # array always ends with a '='
    b_hashed_string_salt_combined_url_safe_clean = base64.urlsafe_b64encode(
        b_hashed_string_salt_combined
    ).strip(b'=')

    # b_hashed_string_salt_combined_url_safe_clean is now ready
    # it's now time to encrypt it fo additional security as at this
    # stage the string is simply urlsafe_b64encoded therefore would be
    # pretty straight forward for someone to decode it with
    # urlsafe_b64decode and find the special '&' which separates the
    # hashed_string and the salt

    # Decode
    s_hashed_string_salt_combined_url_safe_clean = (
        b_hashed_string_salt_combined_url_safe_clean.decode()
    )
    # Encrypt
    s_encrypted = encrypt_string(s_hashed_string_salt_combined_url_safe_clean, fernet_key)
    # Encode
    b_encrypted = s_encrypted.encode()

    return b_encrypted


def validate_hash_match(raw_string: str, hashed_string_to_match: bytes, fernet_key: str) -> bool:
    """
    Validate whether the raw_string (user input) match the
    hashed_string (in database)
    """

    if raw_string and hashed_string_to_match:
        # as the hashed_string_to_match was hashed by the hash_string,
        # it returned an encrypted string the first step is to decrypt
        # the hashed_string_to_match

        # Decode
        s_encrypted = hashed_string_to_match.decode()
        # Decrypt
        s_hashed_string_salt_combined_url_safe_clean = decrypt_string(s_encrypted, fernet_key)
        # Encode
        b_hashed_string_salt_combined_url_safe_clean = (
            s_hashed_string_salt_combined_url_safe_clean.encode()
        )

        # this is the starting point to reverse
        # b_hashed_string_salt_combined_url_safe_clean

        # Add last '=' at the end removed by the 'hash_string' function
        b_hashed_string_salt_combined_url_safe = b_hashed_string_salt_combined_url_safe_clean + b'='

        # Decode b_hashed_string_salt_combined_url_safe_clean_normalized
        # to reveal the special separator '&'
        b_hashed_string_salt_combined = base64.urlsafe_b64decode(
            b_hashed_string_salt_combined_url_safe
        )

        # Split b_hashed_string_url_safe_clean and salt_url_safe_clean
        b_hashed_string_url_safe_clean, salt_url_safe_clean = b_hashed_string_salt_combined.split(
            b'&'
        )

        # Add last '=' at the end removed by the 'hash_string' function
        b_hashed_string_url_safe = b_hashed_string_url_safe_clean + b'='
        salt_url_safe = salt_url_safe_clean + b'='

        # Retrieve original salt and original b_hashed_string by
        # decoding urlsafe_b64decode
        b_hashed_string = base64.urlsafe_b64decode(b_hashed_string_url_safe)
        salt = base64.urlsafe_b64decode(salt_url_safe)

        # b_hashed_string is now ready to be compared to the string to
        # validate now we need to convert the string to validate to hash

        # Encode raw_string
        b_raw_string_to_validate = raw_string.encode()

        # Verify derived key using Scrypt
        kdf = _get_scrypt_kdf(salt)

        try:
            kdf.verify(b_raw_string_to_validate, b_hashed_string)

            return True

        except Exception as e:
            logging.warning(f"Hash validation failed w/ error: {e}")

            return False

    return False


def encrypt_string(string_to_encrypt: str, fernet_key: str) -> str:
    cipher_suite = cryptography.fernet.Fernet(key=fernet_key)

    b_string_to_encrypt = string_to_encrypt.encode()
    b_encrypted = cipher_suite.encrypt(b_string_to_encrypt)

    # Strip last two '==' at the end as Fernet always return a 64 bytes
    # array which ends with two '=='
    b_encrypted_clean = b_encrypted.strip(b'=')

    s_encrypted_clean = b_encrypted_clean.decode()

    return s_encrypted_clean


def decrypt_string(string_to_decrypt: str, fernet_key: str) -> str:
    cipher_suite = cryptography.fernet.Fernet(key=fernet_key)

    # Add two '==' at the end removed by the 'encrypt_string' function
    s_encrypted = string_to_decrypt + '=='
    b_encrypted = s_encrypted.encode()

    try:
        b_decrypted = cipher_suite.decrypt(b_encrypted)
        s_decrypted = b_decrypted.decode()

        return s_decrypted

    except Exception as e:
        logging.warning(f"Decryption failed w/ error: {e}")

        return ""


def generate_random_secret_key(bytes_length: int) -> str:
    # Generate a random string of 64 bytes
    b_random_bytes = os.urandom(bytes_length)

    # Encode the random bytes using Base64 URL-SAFE
    b_random_bytes = base64.urlsafe_b64encode(b_random_bytes)

    # Decode bytes
    s_random_bytes = b_random_bytes.decode()

    return s_random_bytes
