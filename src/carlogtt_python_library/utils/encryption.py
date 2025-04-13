# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_library/utils/encryption.py
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
import ast
import base64
import enum
import logging
import os
import random
import string
import time
from collections.abc import Sequence
from typing import Union

# Third Party Library Imports
import cryptography.fernet
import cryptography.hazmat.backends
import cryptography.hazmat.primitives.ciphers.algorithms
import cryptography.hazmat.primitives.ciphers.modes
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.hmac
import cryptography.hazmat.primitives.kdf.hkdf
import cryptography.hazmat.primitives.kdf.scrypt
import cryptography.hazmat.primitives.padding

# END IMPORTS
# ======================================================================


# List of public names in the module
__all__ = [
    'KeyType',
    'KeyOutputType',
    'EncryptionAlgorithm',
    'Cryptography',
]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)

# Type aliases
#


class KeyType(enum.Enum):
    """
    Enumeration to specify the key type based on its length.

    Attributes:
        AES128: Represents a key length of 128 bits (16 bytes) for AES
                encryption. This size is often used for its balance
                between security and performance.
        AES256: Represents a key length of 256 bits (32 bytes) for AES
                encryption. Offers a high level of security and is
                recommended for situations requiring enhanced data
                protection.
        INITIALIZATION_VECTOR: A 128-bit (16-byte) IV used in various
                               encryption modes to ensure ciphertext
                               uniqueness. Suitable for use with AES
                               and other block ciphers in modes like
                               CBC.
    """

    AES128 = 16
    AES256 = 32
    INITIALIZATION_VECTOR = 16


class KeyOutputType(enum.Enum):
    """
    Enumeration to specify the output format of the generated key.

    Attributes:
        BYTES: The key is returned as raw bytes.
        BASE64: The key is returned as URL-safe Base64-encoded bytes.
    """

    BYTES = enum.auto()
    BASE64 = enum.auto()


class EncryptionAlgorithm(enum.Enum):
    """
    Defines supported encryption algorithms and their corresponding
    security levels.
    """

    AES_128 = enum.auto()
    AES_256 = enum.auto()


class Cryptography:
    """
    Provides cryptographic functionalities including key generation,
    serialization for storage, encryption, decryption, and signing.
    Utilizes symmetric encryption (AES-256) and HMAC for signing.

    :param logger: The logging.Logger instance to be used for logging
           the execution time of the decorated function.
           If not explicitly provided, the function uses
           Python's standard logging module as a default logger.
    """

    def __init__(self, logger: logging.Logger = module_logger):
        self.logger = logger

    def create_key(self, key_type: KeyType, key_output: KeyOutputType) -> bytes:
        """
        Generates a cryptographic key of specified type and returns it
        in the specified output format.

        :param key_type: The type of key to generate, affecting its
               length.
        :param key_output: The output format of the generated key.
        :returns: The generated key in the specified output format.
        """

        # Create a random bytes
        key = os.urandom(key_type.value)

        # Return the key based on the output format
        self.logger.debug(
            f"{key_type.value}-Bytes Key for {key_type.name} - {key_output.name} created"
        )

        if key_output is KeyOutputType.BYTES:
            return key

        elif key_output is KeyOutputType.BASE64:
            return base64.urlsafe_b64encode(key)

    def serialize_key_for_str_storage(self, key: bytes) -> str:
        """
        Converts a bytes object (key) to a string representation
        suitable for storage. Utilizes Python's repr() function to
        create a string that represents the bytes object.

        :param key: The bytes object to be serialized.
        :return: A string representation of the bytes object, including
                 the bytes literal prefix b''.
        """

        self.logger.debug("Serializing key for storage")

        return repr(key)

    def deserialize_key_from_str_storage(self, key: str) -> bytes:
        """
        Converts a string representation of a bytes object back into the
        original bytes object. This function is intended to be used in
        conjunction with serialize_key_for_str_storage, allowing for the
        retrieval of the original bytes object from a stored string.

        :param key: The string representation of the bytes object,
               expected to include the bytes literal prefix b''.
        :return: The original bytes object.
        """

        self.logger.debug("Deserializing key from storage")

        return ast.literal_eval(key)

    def hash_string(self, raw_string: str, key: bytes) -> str:
        """
        Hashes a given string using the Scrypt Key Derivation Function
        and encrypts the result for secure storage.
        The function embeds the salt used for hashing within the
        encrypted hash, ensuring that each piece of data is uniquely
        salted and securely stored.

        :param raw_string: The raw string to be hashed and encrypted.
               Typically, this would be a password or any other
               sensitive information requiring secure handling.
        :param key: The secret key used for encrypting the hashed
               string. This key should be generated and managed using
               secure cryptographic practices and must be a 32-byte key
               for AES-256.
        :return: The encrypted hash of the input string.
                 This output includes both the Scrypt-derived
                 hash and the salt, encrypted for additional security.
                 The resulting binary data is suitable for secure
                 storage in a database or file system, where it can
                 later be decrypted and verified against a user-provided
                 string.
        """

        # Encode raw_password to bytes
        b_raw_string = raw_string.encode()

        # Generate a random salt for the password encryption
        salt = self.create_key(KeyType.AES128, KeyOutputType.BYTES)
        # Encode the salt to url-safe byte array
        salt_base64 = base64.urlsafe_b64encode(salt)

        # Derive key using Scrypt
        b_hashed = self._derive_key_scrypt(salt, b_raw_string)

        # Encode derived_key to url-safe byte array
        b_hashed_base64 = base64.urlsafe_b64encode(b_hashed)

        # Embed salt into hashed string joining them together with
        # byte "&"
        b_hashed_salt = b_hashed_base64 + b"&" + salt_base64

        # It's now time to encrypt it for additional security as at this
        # stage the string is simply urlsafe_b64encoded therefore would
        # be pretty straight forward for someone to decode it with
        # urlsafe_b64decode and find the special "&" which separates the
        # hashed_string and the salt

        # Decode to pass to encrypt function
        s_hashed_salt = b_hashed_salt.decode()

        # Encrypt
        ciphertext = self.encrypt_string(s_hashed_salt, key, EncryptionAlgorithm.AES_256)

        return ciphertext

    def validate_hash_match(
        self,
        raw_string: str,
        hashed_to_match: str,
        key: bytes,
    ) -> bool:
        """
        Validates whether a provided raw string matches the encrypted
        and hashed string stored. This function is designed to work in
        conjunction with hash_string function, reversing its hashing and
        encryption process to verify user input against stored values
        securely.

        :param raw_string: The plaintext string provided by the user,
               typically a password or sensitive information that needs
               validation against a stored, hashed version.
        :param hashed_to_match: The encrypted and hashed data that the
               raw_string is compared against. This should have been
               previously generated by the hash_string function.
        :param key: The secret key used for decrypting the hashed
               string. It must be the same key used for
               encrypting the string initially with the `hash_string`
               function.
        :return: True if the raw_string, when hashed and processed,
                 matches the hashed_string_to_match; False otherwise.
                 The function also returns False in the case of
                 decryption or verification failures.
        """

        if not raw_string and hashed_to_match:
            return False

        try:
            # Decrypt
            s_hashed_salt = self.decrypt_string(hashed_to_match, key, EncryptionAlgorithm.AES_256)

            # Encode
            b_hashed_salt = s_hashed_salt.encode()

            # Split
            # b_hashed_string_url_safe_clean and salt_url_safe_clean
            b_hashed_base64, salt_base64 = b_hashed_salt.split(b"&")

            # Retrieve original salt and original b_hashed_string by
            # decoding urlsafe_b64decode
            b_hashed = base64.urlsafe_b64decode(b_hashed_base64)
            salt = base64.urlsafe_b64decode(salt_base64)

            # Now we are ready to compare with the string to validate,
            # we need to convert the raw string to bytes
            b_raw_string = raw_string.encode()

            # Verify derived key using Scrypt
            self._verify_derived_key_scrypt(salt, b_raw_string, b_hashed)

            return True

        except Exception as ex:
            self.logger.warning(f"Hash validation failed w/ error: {ex}")

            return False

    def sign(self, data_to_sign: bytes, key: bytes) -> bytes:
        """
        Signs the given data using HMAC with SHA256 hash function.

        First, the data is encoded to Base64. Then, an HMAC signature is
        generated using the provided key and the SHA256 hash function.
        The data and its HMAC signature are concatenated, base64
        encoded, and returned.

        :param data_to_sign: Data to be signed.
        :param key: Secret key used for HMAC.
        :returns: Base64 encoded signature of the data.
        """

        # Encode the data_to_sign to Base64
        data_to_sign_base64 = base64.urlsafe_b64encode(data_to_sign)

        # Create Hash-based message authentication codes (HMAC)
        hmac_hash = cryptography.hazmat.primitives.hmac.HMAC(
            key, cryptography.hazmat.primitives.hashes.SHA256()
        )

        # Hash the data to create the signature
        hmac_hash.update(data_to_sign)
        hash_signature = hmac_hash.finalize()
        hash_signature_base64 = base64.urlsafe_b64encode(hash_signature)

        # The Hashing Signature need to be stored with the data
        data_and_hash_signature = data_to_sign_base64 + b"&" + hash_signature_base64

        # Base64 encode the data and the signature
        signature = base64.urlsafe_b64encode(data_and_hash_signature)

        self.logger.debug("Data signed successfully")

        return signature

    def verify_signature(self, signature: bytes, key: bytes) -> dict[str, Union[str, bool, bytes]]:
        """
        Verifies the signature of the provided data.

        Decodes the signature from Base64, extracts the data and its
        HMAC signature, and verifies it using HMAC with SHA256. Returns
        a dict indicating whether the signature is valid, the original
        data, and the hash signature.

        :param signature: Base64 encoded data and signature.
        :param key: Secret key used for HMAC verification.
        :return: A dictionary containing the verification result, the
                 original data, and the hash signature with the keys
                 'data', 'signature', 'signature_valid', and possibly
                 'response_info' if an error occurs.
        """

        response: dict[str, Union[str, bool, bytes]] = {
            'data': b"",
            'signature': b"",
            'signature_valid': False,
        }

        try:
            # Decode the Base64 encoded data
            data_and_hash_signature = base64.urlsafe_b64decode(signature)

            # Extract the data_to_sign_base64 and the
            # hash_signature_base64
            data_base64, hash_signature_base64 = data_and_hash_signature.split(b"&")

            # Decode the Base64
            data = base64.urlsafe_b64decode(data_base64)
            hash_signature = base64.urlsafe_b64decode(hash_signature_base64)

            # Update return dict with data and hash_signature
            response.update(data=data, signature=hash_signature)

        except Exception as ex:
            # Update the return dict with failed validation
            response.update(response_info=repr(ex))
            return response

        try:
            # Create Hash-based message authentication codes (HMAC)
            hmac_hash = cryptography.hazmat.primitives.hmac.HMAC(
                key, cryptography.hazmat.primitives.hashes.SHA256()
            )

            # Validate the Signature
            hmac_hash.update(data)
            hmac_hash.verify(hash_signature)

            self.logger.debug("Signature verified successfully")

            # Update the return dict with successful validation
            response.update(signature_valid=True)

            return response

        except Exception as ex:
            self.logger.warning(f"Signature verification failed w/ error: {ex}")

            # Update the return dict with failed validation
            response.update(response_info=repr(ex))

            return response

    def encrypt_string(
        self,
        plaintext: str,
        key: bytes,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
    ) -> str:
        """
        Encrypts a string using the specified symmetric encryption
        algorithm.

        This function provides a unified interface to encrypt strings
        using different encryption algorithms specified by the
        'algorithm' parameter. It delegates the encryption process to
        the appropriate internal function based on the chosen algorithm.

        :param plaintext: The plaintext string to be encrypted.
        :param key: The secret key used for encryption. The format and
               length depend on the algorithm being used.
               For AES-128, must be a URL-safe base64-encoded 32-byte
               key. For AES-256, must be a 32-byte key.
        :param algorithm: An instance of the
               EncryptionEncryptionAlgorithm enum indicating the
               encryption algorithm to use.
               Default EncryptionAlgorithm.AES_256
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe. With padding removed for
                 storage efficiency.
        """

        if algorithm is EncryptionAlgorithm.AES_128:
            return self._encrypt_aes128(plaintext=plaintext, fernet_key=key)

        elif algorithm is EncryptionAlgorithm.AES_256:
            return self._encrypt_aes256(plaintext=plaintext, key=key)

        else:
            raise ValueError(f"algorthm must be one of the following {list(EncryptionAlgorithm)}")

    def decrypt_string(
        self,
        ciphertext: str,
        key: bytes,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
    ) -> str:
        """
        Decrypts a string previously encrypted by the `encrypt_string`
        function using the specified symmetric encryption algorithm.

        This function provides a unified interface to decrypt strings
        using different encryption algorithms specified by the
        'algorithm' parameter. It delegates the decryption process to
        the appropriate internal function based on the chosen algorithm.

        :param ciphertext: The encrypted string to be decrypted.
               It is expected to be Base64 encoded and without padding.
        :param key: The secret key used for decryption. Must match the
               key used for encryption and be appropriate for the
               specified algorithm.
        :param algorithm: An instance of the EncryptionAlgorithm enum
               indicating the encryption algorithm to use.
               Default EncryptionAlgorithm.AES_256
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        if algorithm is EncryptionAlgorithm.AES_128:
            return self._decrypt_aes128(ciphertext=ciphertext, fernet_key=key)

        elif algorithm is EncryptionAlgorithm.AES_256:
            return self._decrypt_aes256(ciphertext=ciphertext, key=key)

        else:
            raise ValueError(f"algorthm must be one of the following {list(EncryptionAlgorithm)}")

    def re_encrypt_string(
        self,
        ciphertext_to_re_encrypt: str,
        old_key: bytes,
        new_key: bytes,
        old_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
        new_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
    ) -> str:
        """
        Re-encrypts data, transitioning it from an old key to a new key.

        This function first decrypts the given encrypted data with the
        old key, then re-encrypts it using the new key. It supports key
        rotation and the update of the encryption scheme for securely
        stored data.

        Ideal for key rotation or encryption scheme updates, ensuring
        data remains secure during key transitions or algorithm updates.

        :param ciphertext_to_re_encrypt: Encrypted data with old key.
        :param old_key: The old encryption key.
        :param new_key: The new encryption key for re-encryption.
        :param old_algorithm: An instance of the EncryptionAlgorithm
               enum indicating the encryption algorithm to use.
               Default EncryptionAlgorithm.AES_256
        :param new_algorithm: An instance of the EncryptionAlgorithm
               enum indicating the encryption algorithm to use.
               Default EncryptionAlgorithm.AES_256
        :return: Re-encrypted data as a string with the new key.
        """

        # Decrypt data with old key
        plaintext = self.decrypt_string(
            ciphertext_to_re_encrypt,
            old_key,
            old_algorithm,
        )

        # Encrypt the data with the new key
        ciphertext_re_encrypted = self.encrypt_string(
            plaintext,
            new_key,
            new_algorithm,
        )

        return ciphertext_re_encrypted

    def create_token(
        self, length: int, validity_secs: int, key: bytes, population: Sequence = ()
    ) -> dict[str, Union[str, int]]:
        """
        Generates a secure token and its expiry time. The token is
        encrypted with a given key to produce a cipher token.

        :param length: Length of the random token
               maximum is 62 characters.
        :param validity_secs: Time in seconds until the token expires.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :param population: Lets you define a different set of characters
               that the token can be composed of.
               Default letters and digits
        :raise ValueError: If length is greater than 62.
        :return: A dictionary with 'token', 'expiry', and 'ciphertoken'
                 keys.
        """

        if length > 62:
            raise ValueError("length cannot be greater than 62")

        population = population or string.ascii_letters + string.digits

        random_string = "".join(random.sample(population, length))
        random_string_hashed = self.hash_string(random_string, key)
        random_string_hashed_base64 = base64.urlsafe_b64encode(random_string_hashed.encode())

        now = time.time_ns()
        expires = now + validity_secs * 1_000_000_000
        expires_base64 = base64.urlsafe_b64encode(str(expires).encode())

        combined = random_string_hashed_base64 + b"&" + expires_base64

        combined_encrypted = self.encrypt_string(combined.decode(), key)

        response: dict[str, Union[str, int]] = {
            'token': random_string,
            'expiry': expires,
            'ciphertoken': combined_encrypted,
        }

        return response

    def verify_token(
        self, token: str, ciphertoken: str, key: bytes
    ) -> dict[str, Union[str, int, bool]]:
        """
        Verifies the validity of the given token by decrypting the
        cipher token using the provided key, and checks if it's expired
        based on the current time and the expiry time embedded in the
        cipher token.

        :param token: The original token to be validated.
        :param ciphertoken: The encrypted string containing the token
               and expiry.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :return: A dictionary with the keys 'token_valid', 'token',
                 'expiry', and possibly 'response_info' if an error
                 occurs.
        """

        # Initializing code validity response and override if True
        response: dict[str, Union[str, int, bool]] = {
            'token_valid': False,
            'token': "",
            'expiry': 0,
        }

        combined = self.decrypt_string(ciphertoken, key).encode()

        try:
            random_string_hashed_base64, expiry_base64 = combined.split(b"&")
            random_string_hashed = base64.urlsafe_b64decode(random_string_hashed_base64).decode()

            expiry = int(base64.urlsafe_b64decode(expiry_base64).decode())
            now = time.time_ns()

            response.update(token=token, expiry=expiry)

        except Exception as ex:
            response.update(response_info=repr(ex))
            return response

        if now < expiry:
            confirmation_code_valid = self.validate_hash_match(token, random_string_hashed, key)
            response.update(token_valid=confirmation_code_valid)
        else:
            response.update(response_info="Token expired")

        return response

    def _encrypt_aes128(self, plaintext: str, fernet_key: bytes) -> str:
        """
        Encrypts a string using Fernet symmetric encryption.

        This function encrypts a given string with Fernet, encoding the
        input to bytes, then encrypting. It removes the padding ("=") at
        the end of the encrypted byte array to minimize storage.

        :param plaintext: The plaintext string to be encrypted.
        :param fernet_key: The secret key used for encryption. Must be a
               URL-safe base64-encoded 32-byte key.
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe. With padding removed for
                 storage efficiency.
        """

        # Ensure the Fernet key length is valid
        # For a bytes_length of 32, the length of the Base64-encoded
        # string without stripping padding would be 44 characters.
        if len(fernet_key) != 44:
            msg = "Fernet key must be a URL-safe base64-encoded 32-byte key."
            self.logger.error(msg)
            raise ValueError(msg)

        cipher_suite = cryptography.fernet.Fernet(key=fernet_key)

        b_string_to_encrypt = plaintext.encode()
        b_encrypted = cipher_suite.encrypt(b_string_to_encrypt)

        # Strip last two "==" at the end as Fernet always return a 64
        # bytes array which ends with two "=="
        b_encrypted_clean = b_encrypted.rstrip(b"=")

        s_encrypted_clean = b_encrypted_clean.decode()

        return s_encrypted_clean

    def _decrypt_aes128(self, ciphertext: str, fernet_key: bytes) -> str:
        """
        Decrypts a string previously encrypted by _encrypt_string_aes128

        Attempts to decrypt the provided string using the given Fernet
        key. If decryption fails, it catches the exception, logs a
        warning, and returns an empty string to indicate failure.

        :param ciphertext: The encrypted string to be decrypted.
               Padding will be re-added internally for decryption.
        :param fernet_key: The secret key used for decryption.
               Must match the key used for encryption.
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        # Ensure the Fernet key length is valid
        # For a bytes_length of 32, the length of the Base64-encoded
        # string without stripping padding would be 44 characters.
        if len(fernet_key) != 44:
            msg = "Fernet key must be a URL-safe base64-encoded 32-byte key."
            self.logger.error(msg)
            raise ValueError(msg)

        # Correct the Base64 padding if necessary
        missing_padding = len(ciphertext) % 4
        if missing_padding:
            ciphertext += "=" * (4 - missing_padding)

        cipher_suite = cryptography.fernet.Fernet(key=fernet_key)

        b_encrypted = ciphertext.encode()

        try:
            b_decrypted = cipher_suite.decrypt(b_encrypted)
            s_decrypted = b_decrypted.decode()

            return s_decrypted

        except Exception as ex:
            self.logger.warning(f"Decryption failed w/ error: {ex}")

            return ""

    def _encrypt_aes256(self, plaintext: str, key: bytes) -> str:
        """
        Encrypts a string using AES-256 symmetric encryption in CBC mode
        and adds an HMAC for message authentication.

        The function performs AES-256 encryption on the input string
        with a given key, then computes an HMAC signature of the
        encrypted data for verification. This approach provides both
        confidentiality and integrity/authentication of the message.

        :param plaintext: The plaintext string to be encrypted.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe. With padding removed for
                 storage efficiency.
        """

        # Ensure the AES key length is valid for AES-256
        if len(key) != 32:
            msg = "AES key must be 32 bytes long for AES-256."
            self.logger.error(msg)
            raise ValueError(msg)

        # Generate a random salt used to randomizes the KDF’s output
        # Used to derive 2 keys, one for encryption and one for signing
        salt = self.create_key(KeyType.AES256, KeyOutputType.BYTES)
        # Encode the salt to url-safe byte array
        salt_base64 = base64.urlsafe_b64encode(salt)

        # Derive keys from master key
        aes_key, hash_key = self._derive_key_hkdf(salt, key)

        # Generate a random 16-byte IV (Initialization Vector)
        iv = self.create_key(KeyType.INITIALIZATION_VECTOR, KeyOutputType.BYTES)

        b_plaintext = plaintext.encode()

        # Pad the input string to ensure it's a multiple of block size
        padder = cryptography.hazmat.primitives.padding.PKCS7(
            cryptography.hazmat.primitives.ciphers.algorithms.AES.block_size
        ).padder()
        b_plaintext_padded = padder.update(b_plaintext) + padder.finalize()

        # Create a Cipher object for AES-256 in CBC mode
        cipher = cryptography.hazmat.primitives.ciphers.Cipher(
            cryptography.hazmat.primitives.ciphers.algorithms.AES(aes_key),
            cryptography.hazmat.primitives.ciphers.modes.CBC(iv),
        )

        # Encrypt the padded data
        encryptor = cipher.encryptor()
        b_ciphertext = encryptor.update(b_plaintext_padded) + encryptor.finalize()

        # The IV needs to be stored with the ciphertext for decryption
        b_ciphertext_iv = iv + b_ciphertext

        # Sign the encrypted data with IV
        b_ciphertext_signed_base64 = self.sign(b_ciphertext_iv, hash_key)

        # Add the salt used to derive the 2 keys to the data so that the
        # decrypt function can derive the same keys again
        b_ciphertext_signed_salt = b_ciphertext_signed_base64 + b"&" + salt_base64

        # Encode base64 to remove the &
        b_ciphertext_signed_salt_base64 = base64.urlsafe_b64encode(b_ciphertext_signed_salt)

        # Decode Base64 and strip the "=" padding at the end if not a
        # multiple of 4
        ciphertext = b_ciphertext_signed_salt_base64.decode().rstrip("=")

        return ciphertext

    def _decrypt_aes256(self, ciphertext: str, key: bytes) -> str:
        """
        Decrypts a string that was encrypted using AES-256 symmetric
        encryption in CBC mode and verifies its HMAC signature.

        This function attempts to decrypt a provided string using a
        specified AES key. Before decryption, it verifies the HMAC to
        ensure the message's integrity and authenticity.
        If the HMAC verification fails, the function logs a warning and
        returns an empty string, indicating a potential tampering or
        authenticity issue.

        :param ciphertext: The encrypted string to be decrypted.
               Padding will be re-added internally for decryption.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        # Ensure the AES key length is valid for AES-256
        if len(key) != 32:
            msg = "AES key must be 32 bytes long for AES-256."
            self.logger.error(msg)
            raise ValueError(msg)

        # Correct the Base64 padding if necessary
        missing_padding = len(ciphertext) % 4
        if missing_padding:
            ciphertext += "=" * (4 - missing_padding)

        b_ciphertext_signed_salt_base64 = ciphertext.encode()

        # Decode base64 to reveal the &
        b_ciphertext_signed_salt = base64.urlsafe_b64decode(b_ciphertext_signed_salt_base64)

        # Split the data and salt at the &
        b_ciphertext_signed_base64, salt_base64 = b_ciphertext_signed_salt.split(b"&")

        # Decode the salt to bytes
        salt = base64.urlsafe_b64decode(salt_base64)

        # Derive keys from master key
        aes_key, hash_key = self._derive_key_hkdf(salt, key)

        # Verify signature
        response = self.verify_signature(b_ciphertext_signed_base64, hash_key)

        if not response['signature_valid']:
            return ""

        # If verification is successful get the data
        b_ciphertext_iv = response['data']
        assert isinstance(b_ciphertext_iv, bytes)

        # Extract the IV (Initialization Vector) and the encrypted
        # string
        iv = b_ciphertext_iv[:16]
        b_ciphertext = b_ciphertext_iv[16:]

        # Create a Cipher object for AES-256 in CBC mode
        cipher = cryptography.hazmat.primitives.ciphers.Cipher(
            cryptography.hazmat.primitives.ciphers.algorithms.AES(aes_key),
            cryptography.hazmat.primitives.ciphers.modes.CBC(iv),
        )

        # Decrypt the data
        decryptor = cipher.decryptor()
        b_plaintext_padded = decryptor.update(b_ciphertext) + decryptor.finalize()

        # Remove padding
        unpadder = cryptography.hazmat.primitives.padding.PKCS7(
            cryptography.hazmat.primitives.ciphers.algorithms.AES.block_size
        ).unpadder()
        b_plaintext = unpadder.update(b_plaintext_padded) + unpadder.finalize()

        # Decode
        plaintext = b_plaintext.decode()

        return plaintext

    def _derive_key_hkdf(self, salt: bytes, key_material: bytes) -> tuple[bytes, bytes]:
        """
        Derives two distinct keys (an AES encryption key and a hash key)
        from a given master key.

        This function uses the HMAC-based Key Derivation Function (HKDF)
        with SHA-256 hash algorithm to derive two separate 32-byte keys
        from the provided master key. A 16-bytes salt is use in the
        HKDF, ensuring the uniqueness of the derived keys even when the
        same master key is used.
        The 'info' parameter is utilized to differentiate the purpose of
        each derived key.

        :param salt: A byte string used to salt the key derivation to
               prevent rainbow table attacks. The salt should be unique
               for each credential to be protected but does not need to
               be kept secret.
        :param key_material: The master key from which the AES and hash
               keys are derived.
        :return: A tuple containing two bytes objects:
                 the AES key and the hash key.
        """

        # Derive the AES encryption key
        aes_key_hkdf = cryptography.hazmat.primitives.kdf.hkdf.HKDF(
            algorithm=cryptography.hazmat.primitives.hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"aes-key",
        )
        aes_key = aes_key_hkdf.derive(key_material)

        self.logger.debug("AES key derived successfully")

        # Derive the hash key
        hash_key_hkdf = cryptography.hazmat.primitives.kdf.hkdf.HKDF(
            algorithm=cryptography.hazmat.primitives.hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"hash-key",
        )
        hash_key = hash_key_hkdf.derive(key_material)

        self.logger.debug("Hashing key derived successfully")

        return aes_key, hash_key

    def _derive_key_scrypt(self, salt: bytes, key_material: bytes) -> bytes:
        """
        Derives a cryptographic key from a given key material using the
        Scrypt KDF.

        Scrypt is designed to be resistant against hardware-assisted
        attacks by allowing tunable memory and CPU cost parameters.
        It is particularly suitable for password storage and protection.

        :param salt: A byte string used to salt the key derivation to
               prevent rainbow table attacks. The salt should be unique
               for each credential to be protected but does not need to
               be kept secret.
        :param key_material: The input key material from which to derive
               the key.
        :return: The derived cryptographic key.
        """

        # Scrypt configuration
        length = 32  # The desired length of the derived key in bytes
        n = 2**14  # CPU/Memory cost parameter. It must be larger than 1 and be a power of 2
        r = 8  # Block size parameter
        p = 1  # Parallelization parameter

        scrypt = cryptography.hazmat.primitives.kdf.scrypt.Scrypt(
            salt=salt, length=length, n=n, r=r, p=p
        )

        # Derive the key
        key_derived = scrypt.derive(key_material)

        self.logger.debug("Scrypt key derived successfully")

        return key_derived

    def _verify_derived_key_scrypt(
        self, salt: bytes, key_material: bytes, expected_key: bytes
    ) -> None:
        """
        Verifies a derived key against an expected key using the Scrypt
        KDF.

        :param salt: A byte string used to salt the key derivation to
               prevent rainbow table attacks. The salt should be unique
               for each credential to be protected but does not need to
               be kept secret.
        :param key_material: The original key material used for key
               derivation.
        :param expected_key: The expected derived key to verify against.
        :raise: Exception is raised when the derived key does not match
                the expected key.
        """

        # Re-configure Scrypt with the same parameters used for deriving
        # the key
        length = 32  # The desired length of the derived key in bytes
        n = 2**14  # CPU/Memory cost parameter. It must be larger than 1 and be a power of 2
        r = 8  # Block size parameter
        p = 1  # Parallelization parameter

        scrypt = cryptography.hazmat.primitives.kdf.scrypt.Scrypt(
            salt=salt, length=length, n=n, r=r, p=p
        )

        # Attempt to verify the derived key
        scrypt.verify(key_material, expected_key)

        self.logger.debug("Scrypt key verified successfully")
