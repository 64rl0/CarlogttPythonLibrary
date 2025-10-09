# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# test/test_encryption.py
# Created 4/25/25 - 10:16 PM UK Time (London) by carlogtt
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
import base64
import os
import time

# Third Party Library Imports
import pytest
from cryptography.fernet import Fernet

# My Library Imports
import carlogtt_python_library as mylib

# END IMPORTS
# ======================================================================


# List of public names in the module
# __all__ = []

# Setting up logger for current module
#

# Type aliases
#


@pytest.fixture(scope="module")
def crypto():
    """Shared Cryptography helper."""
    return mylib.Cryptography()


@pytest.fixture(scope="module")
def aes256_key():
    """32-byte key suitable for AES-256 paths."""
    return os.urandom(32)


@pytest.fixture(scope="module")
def fernet_key():
    """Valid Fernet key (44-byte URL-safe Base64)."""
    return Fernet.generate_key()


# ----------------------------------------------------------------------
# create_key
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "kt,expected_len",
    [
        (mylib.KeyType.AES128, 16),
        (mylib.KeyType.AES256, 32),
        (mylib.KeyType.INITIALIZATION_VECTOR, 16),
    ],
)
def test_create_key_bytes_length(crypto, kt, expected_len):
    key = crypto.create_key(kt, mylib.KeyOutputType.BYTES)
    assert isinstance(key, bytes) and len(key) == expected_len


@pytest.mark.parametrize("kt", [mylib.KeyType.AES128, mylib.KeyType.AES256])
def test_create_key_base64_roundtrip(crypto, kt):
    key_b64 = crypto.create_key(kt, mylib.KeyOutputType.BASE64)
    raw = base64.urlsafe_b64decode(key_b64)
    assert len(raw) == kt.value


def test_create_key_invalid_type_raises(crypto):
    with pytest.raises(mylib.CryptographyError):
        crypto.create_key("SORRY", mylib.KeyOutputType.BYTES)  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# (De)serialise helpers
# ----------------------------------------------------------------------
def test_serialize_deserialize_roundtrip(crypto, aes256_key):
    stored = crypto.serialize_key_for_str_storage(aes256_key)
    restored = crypto.deserialize_key_from_str_storage(stored)
    assert restored == aes256_key and isinstance(restored, bytes)


# ----------------------------------------------------------------------
# AES-128 (Fernet) path
# ----------------------------------------------------------------------
def test_encrypt_decrypt_aes128_roundtrip(crypto, fernet_key):
    plaintext = "secret text æøå"
    ct = crypto.encrypt_string(plaintext, fernet_key, mylib.EncryptionAlgorithm.AES_128)
    pt = crypto.decrypt_string(ct, fernet_key, mylib.EncryptionAlgorithm.AES_128)
    assert pt == plaintext


def test_encrypt_string_wrong_key_len_aes128_raises(crypto):
    with pytest.raises(ValueError):
        crypto.encrypt_string("oops", b"short_key", mylib.EncryptionAlgorithm.AES_128)


# ----------------------------------------------------------------------
# AES-256 path
# ----------------------------------------------------------------------
def test_encrypt_decrypt_aes256_roundtrip(crypto, aes256_key):
    plaintext = "προσωπικό μυστικό"
    ct = crypto.encrypt_string(plaintext, aes256_key, mylib.EncryptionAlgorithm.AES_256)
    pt = crypto.decrypt_string(ct, aes256_key, mylib.EncryptionAlgorithm.AES_256)
    assert pt == plaintext


def test_encrypt_string_wrong_key_len_aes256_raises(crypto):
    with pytest.raises(ValueError):
        crypto.encrypt_string("oops", b"short_key", mylib.EncryptionAlgorithm.AES_256)


# ----------------------------------------------------------------------
# AES-GCS path
# ----------------------------------------------------------------------
def test_encrypt_decrypt_aes_gcm_roundtrip(crypto, aes256_key):
    plaintext = "προσωπικό μυστικό"
    ct = crypto.encrypt_string(plaintext, aes256_key, mylib.EncryptionAlgorithm.AES_GCM)
    pt = crypto.decrypt_string(ct, aes256_key, mylib.EncryptionAlgorithm.AES_GCM)
    assert pt == plaintext


def test_encrypt_string_wrong_key_len_aes_gcm_raises(crypto):
    with pytest.raises(ValueError):
        crypto.encrypt_string("oops", b"short_key", mylib.EncryptionAlgorithm.AES_GCM)


# ----------------------------------------------------------------------
# Default encryption
# ----------------------------------------------------------------------
def test_encrypt_decrypt_default_encryption_roundtrip(crypto, aes256_key):
    plaintext = "προσωπικό μυστικό"
    ct = crypto.encrypt_string(plaintext, aes256_key)
    pt = crypto.decrypt_string(ct, aes256_key)
    assert pt == plaintext


def test_encrypt_string_wrong_key_len_default_encryption_raises(crypto):
    with pytest.raises(ValueError):
        crypto.encrypt_string("oops", b"short_key")


# ----------------------------------------------------------------------
# Hash / Validate
# ----------------------------------------------------------------------
def test_hash_and_validate_success(crypto, aes256_key):
    raw = "p@ssw0rd"
    hashed = crypto.hash_string(raw, aes256_key)
    assert crypto.validate_hash_match(raw, hashed, aes256_key)


def test_hash_and_validate_failure(crypto, aes256_key):
    raw = "p@ssw0rd"
    hashed = crypto.hash_string(raw, aes256_key)
    assert not crypto.validate_hash_match("WRONG", hashed, aes256_key)


def test_hash_and_validate_success_v2(crypto, aes256_key):
    raw = "p@ssw0rd"
    hashed = crypto.hash_string_v2(raw)
    assert crypto.validate_hash_match_v2(raw, hashed)


def test_hash_and_validate_failure_v2(crypto, aes256_key):
    raw = "p@ssw0rd"
    hashed = crypto.hash_string_v2(raw)
    assert not crypto.validate_hash_match_v2("WRONG", hashed)


# ----------------------------------------------------------------------
# Re-encrypt
# ----------------------------------------------------------------------
def test_re_encrypt_string(crypto, aes256_key):
    other_key = os.urandom(32)
    plaintext = "rotate me"
    old_ct = crypto.encrypt_string(plaintext, aes256_key)
    new_ct = crypto.re_encrypt_string(old_ct, aes256_key, other_key)
    assert crypto.decrypt_string(new_ct, other_key) == plaintext


# ----------------------------------------------------------------------
# Sign / Verify
# ----------------------------------------------------------------------
def test_sign_verify_signature(crypto, aes256_key):
    data = b"\x00\x11testdata"
    sig = crypto.sign(data, aes256_key)
    res = crypto.verify_signature(sig, aes256_key)
    assert res["signature_valid"] and res["data"] == data


# ----------------------------------------------------------------------
# Token generation / verification
# ----------------------------------------------------------------------
def test_create_and_verify_token_valid(crypto, aes256_key):
    now_epoch = time.time()
    tok_info = crypto.create_token(length=12, validity_secs=5, now_epoch=now_epoch, key=aes256_key)
    res = crypto.verify_token(tok_info["token"], tok_info["ciphertoken"], now_epoch, aes256_key)
    assert res["token_valid"]


def test_verify_token_expired(crypto, aes256_key):
    now_epoch = time.time()
    tok_info = crypto.create_token(length=6, validity_secs=0, now_epoch=now_epoch, key=aes256_key)

    time.sleep(0.5)

    res = crypto.verify_token(tok_info["token"], tok_info["ciphertoken"], now_epoch, aes256_key)
    assert not res["token_valid"] and res.get("response_info") == "Token expired"
