# ======================================================================
# MODULE DETAILS
# This section provides metadata about the module, including its
# creation date, author, copyright information, and a brief description
# of the module's purpose and functionality.
# ======================================================================

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# src/carlogtt_python_library/utils/encryption.py
# Created 10/2/23 - 9:25 AM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

"""
Utilities for authenticated encryption and password hashing.
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
import secrets
import string
import warnings
from collections.abc import Sequence
from typing import Optional, TypedDict, Union

# Third Party Library Imports
import cryptography.fernet
import cryptography.hazmat.primitives.ciphers.aead
import cryptography.hazmat.primitives.ciphers.algorithms
import cryptography.hazmat.primitives.ciphers.modes
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.hmac
import cryptography.hazmat.primitives.kdf.hkdf
import cryptography.hazmat.primitives.kdf.scrypt
import cryptography.hazmat.primitives.padding

# Local Folder (Relative) Imports
from .. import exceptions

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


class ScryptParamsType(TypedDict):
    n: int
    r: int
    p: int
    length: int


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
    Defines supported encryption algorithms anf their envelope prefixes.
    """

    AES_128 = "v1:fernet:"
    AES_256 = "v1:cbc:"
    AES_GCM = "v2:gcm:"

    @classmethod
    def all_alg_prefixes(cls) -> tuple[str, ...]:
        return tuple(alg.value for alg in cls)


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

        if not isinstance(key_type, KeyType):
            raise exceptions.CryptographyError(f"Invalid key type: {key_type}")

        # Create a random bytes
        key = self._rand_bytes(n=key_type.value)

        # Return the key based on the output format
        self.logger.debug(
            f"{key_type.value}-Bytes Key for {key_type.name} - {key_output.name} created"
        )

        if key_output is KeyOutputType.BYTES:
            return key

        elif key_output is KeyOutputType.BASE64:
            return base64.urlsafe_b64encode(key)

        else:
            raise exceptions.CryptographyError(f"Invalid key output type: {key_output}")

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
        DEPRECATED — use `hash_string_v2()`.
        Note: the key parameter is ignored in this deprecated API.

        Hashes a given string using the Scrypt Key Derivation Function

        :param raw_string: The raw string to be hashed.
               Typically, this would be a password or any other
               sensitive information requiring secure handling.
        :param key: The secret key used for hashing the hashed
               string. This key should be generated and managed using
               secure cryptographic practices and must be a 32-byte key
               for AES-256.
        :return: The hash of the input string.
        """

        msg = (
            f"[DEPRECATED] '{self.hash_string.__name__}' is deprecated in Class"
            f" '{self.__class__.__name__}'. Use the new method '{self.hash_string_v2.__name__}()'"
            " instead."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=3)
        module_logger.warning(msg)

        return self.hash_string_v2(raw_string=raw_string)

    def hash_string_v2(
        self, raw_string: str, scrypt_params: Optional[ScryptParamsType] = None
    ) -> str:
        """
        Hash a given string with scrypt and return a PHC-style string:

        scrypt$ln=<n2exp>,r=<r>,p=<p>$<salt_b64>$<hash_b64>

        A new 16-byte random salt is generated per given string.

        :param raw_string: The raw string to be hashed.
               Typically, this would be a password or any other
               sensitive information requiring secure handling.
        :param scrypt_params: The scrypt parameters to be used for
               hashing. If not provided, secure defaults are used.
        :return: The hash of the input string PHC-style scrypt string.
        """

        if not scrypt_params:
            scrypt_params = {
                "n": 2**17,
                "r": 8,
                "p": 1,
                "length": 32,
            }

        n = scrypt_params['n']
        if n <= 1 or (n & (n - 1)) != 0:
            raise ValueError("scrypt 'n' must be a power of two > 1")

        # since n is power of two
        ln = n.bit_length() - 1

        salt = self._rand_bytes(16)

        kdf = cryptography.hazmat.primitives.kdf.scrypt.Scrypt(
            salt=salt,
            length=scrypt_params['length'],
            n=scrypt_params['n'],
            r=scrypt_params['r'],
            p=scrypt_params['p'],
        )

        # Derive the key
        dk = kdf.derive(raw_string.encode())

        self.logger.debug("Scrypt key derived successfully")

        hash_string = f"scrypt$ln={ln},r={scrypt_params['r']},p={scrypt_params['p']}${self._b64u_encode(salt)}${self._b64u_encode(dk)}"  # noqa

        return hash_string

    def validate_hash_match(self, raw_string: str, hashed_to_match: str, key: bytes) -> bool:
        """
        DEPRECATED — use `validate_hash_match_v2()`.
        Note: the key parameter is ignored in this deprecated API.

        Validates whether a provided raw string matches the hashed
        string stored.

        :param raw_string: The plaintext string provided by the user,
               typically a password or sensitive information that needs
               validation against a stored, hashed version.
        :param hashed_to_match: The hashed data that the
               raw_string is compared against.
        :param key: The secret key used for hashing the hashed
               string.
        :return: True if the raw_string, when hashed and processed,
                 matches the hashed_string_to_match; False otherwise.
        """

        msg = (
            f"[DEPRECATED] '{self.validate_hash_match.__name__}' is deprecated in Class"
            f" '{self.__class__.__name__}'. Use the new method"
            f" '{self.validate_hash_match_v2.__name__}()' instead."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=3)
        module_logger.warning(msg)

        return self.validate_hash_match_v2(raw_string=raw_string, hashed_to_match=hashed_to_match)

    def validate_hash_match_v2(self, raw_string: str, hashed_to_match: str) -> bool:
        """
        Verify a provided raw string against a PHC-style scrypt string
        in constant time.

        :param raw_string: The plaintext string provided by the user,
               typically a password or sensitive information that needs
               validation against a stored, hashed version.
        :param hashed_to_match: The hashed data that the
               raw_string is compared against.
        :return: True if the raw_string, when hashed and processed,
                 matches the hashed_string_to_match; False otherwise.
        """

        if not raw_string and hashed_to_match:
            return False

        try:
            scheme, param_str, salt_b64, dk_b64 = hashed_to_match.split("$", 3)

            if scheme != "scrypt":
                return False

            scrypt_params = dict(kv.split("=", 1) for kv in param_str.split(","))
            n = 1 << int(scrypt_params["ln"])
            r = int(scrypt_params["r"])
            p = int(scrypt_params["p"])

            salt = self._b64u_decode(salt_b64)
            expected = self._b64u_decode(dk_b64)

            length = len(expected)

            kdf = cryptography.hazmat.primitives.kdf.scrypt.Scrypt(
                salt=salt, length=length, n=n, r=r, p=p
            )

            # Attempt to verify the derived key
            kdf.verify(raw_string.encode(), expected)

            self.logger.debug("Scrypt key verified successfully")

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
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_GCM,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """
        Encrypts plaintext using the selected algorithm and returns a
        versioned, Base64-url-safe string.

        Envelope prefixes:
          - v2:gcm:...    → AES-256-GCM (default)
          - v1:cbc:...    → AES-256-CBC + HMAC-SHA256 (legacy)
          - v1:fernet:... → Fernet (legacy)

        - AES_GCM: expects a 32-byte key (AES-256-GCM). Optional AAD.
        - AES_256 (CBC+HMAC): expects a 32-byte key; integrity via HMAC.
        - AES_128 (Fernet): expects a 44-byte urlsafe base64-encoded
          key.

        :param plaintext: The plaintext string to be encrypted.
        :param key: The secret key used for encryption. The format and
               length depend on the algorithm being used.
        :param algorithm: An instance of the
               EncryptionAlgorithm enum indicating the
               encryption algorithm to use.
               Default EncryptionAlgorithm.AES_GCM
        :param associated_data: Additional authenticated data (AAD) to
               be authenticated but not encrypted. It must be provided
               as a byte string if used.
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe.
        """

        if algorithm is EncryptionAlgorithm.AES_GCM:
            return self._encrypt_aes_gcm(plaintext=plaintext, key=key, aad=associated_data)

        elif algorithm is EncryptionAlgorithm.AES_256:
            return self._encrypt_aes256(plaintext=plaintext, key=key)

        elif algorithm is EncryptionAlgorithm.AES_128:
            return self._encrypt_aes128(plaintext=plaintext, fernet_key=key)

        else:
            raise ValueError(f"algorthm must be one of the following {list(EncryptionAlgorithm)}")

    def decrypt_string(
        self,
        ciphertext: str,
        key: bytes,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_GCM,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """
        Decrypts a string previously encrypted by the `encrypt_string`
        function.

        If a version prefix is present, auto-detect the algorithm:
          - v2:gcm:...    → AES-GCM
          - v1:cbc:...    → AES-CBC + HMAC (legacy)
          - v1:fernet:... → Fernet (legacy)
        Otherwise, fall back to the provided `algorithm`.

        :param ciphertext: The encrypted string to be decrypted.
               It is expected to be Base64 encoded.
        :param key: The secret key used for decryption. Must match the
               key used for encryption and be appropriate for the
               specified algorithm.
        :param algorithm: An instance of the EncryptionAlgorithm enum
               indicating the encryption algorithm to use.
               Default EncryptionAlgorithm.AES_GCM
        :param associated_data: Additional authenticated data (AAD) to
               be authenticated but not encrypted. It must be provided
               as a byte string if used.
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        # Try auto-detect alg first then fall back to user provided alg
        if ciphertext.startswith(EncryptionAlgorithm.AES_GCM.value):
            return self._decrypt_aes_gcm(ciphertext=ciphertext, key=key, aad=associated_data)

        if ciphertext.startswith(EncryptionAlgorithm.AES_256.value):
            return self._decrypt_aes256(ciphertext=ciphertext, key=key)

        if ciphertext.startswith(EncryptionAlgorithm.AES_128.value):
            return self._decrypt_aes128(ciphertext=ciphertext, fernet_key=key)

        # manual selection
        if algorithm is EncryptionAlgorithm.AES_GCM:
            return self._decrypt_aes_gcm(ciphertext=ciphertext, key=key, aad=associated_data)

        elif algorithm is EncryptionAlgorithm.AES_256:
            return self._decrypt_aes256(ciphertext=ciphertext, key=key)

        elif algorithm is EncryptionAlgorithm.AES_128:
            return self._decrypt_aes128(ciphertext=ciphertext, fernet_key=key)

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
        self,
        length: int,
        validity_secs: Union[int, float],
        now_epoch: float,
        key: bytes,
        population: Sequence = (),
    ) -> dict[str, Union[str, float]]:
        """
        Generates a secure token and its expiry time. The token is
        encrypted with a given key to produce a cipher token.

        :param length: Length of the random token.
        :param validity_secs: Time in seconds until the token expires.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :param now_epoch: Current time in seconds since the epoch.
        :param population: Lets you define a different set of characters
               that the token can be composed of.
               Default letters and digits
        :raise ValueError: If length is greater than 62.
        :return: A dictionary with 'token', 'expiry', and 'ciphertoken'
                 keys.
        """

        alphabet = string.ascii_letters + string.digits
        population = population or alphabet

        random_string = "".join(secrets.choice(population) for _ in range(length))
        random_string_hashed = self.hash_string_v2(raw_string=random_string)
        random_string_hashed_base64 = base64.urlsafe_b64encode(random_string_hashed.encode())

        expires = float(now_epoch) + float(validity_secs)
        expires_base64 = base64.urlsafe_b64encode(str(expires).encode())

        combined = random_string_hashed_base64 + b"&" + expires_base64

        combined_encrypted = self.encrypt_string(plaintext=combined.decode(), key=key)

        response: dict[str, Union[str, float]] = {
            'token': random_string,
            'expiry': expires,
            'ciphertoken': combined_encrypted,
        }

        return response

    def verify_token(
        self, token: str, ciphertoken: str, now_epoch: float, key: bytes
    ) -> dict[str, Union[str, float, bool]]:
        """
        Verifies the validity of the given token by decrypting the
        cipher token using the provided key, and checks if it's expired
        based on the current time and the expiry time embedded in the
        cipher token.

        :param token: The original token to be validated.
        :param ciphertoken: The encrypted string containing the token
               and expiry.
        :param now_epoch: Current time in seconds since the epoch.
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :return: A dictionary with the keys 'token_valid', 'token',
                 'expiry', and possibly 'response_info' if an error
                 occurs.
        """

        # Initializing code validity response and override if True
        response: dict[str, Union[str, float, bool]] = {
            'token_valid': False,
            'token': "",
            'expiry': 0.0,
        }

        combined = self.decrypt_string(ciphertext=ciphertoken, key=key).encode()

        try:
            random_string_hashed_base64, expiry_base64 = combined.split(b"&")
            random_string_hashed = base64.urlsafe_b64decode(random_string_hashed_base64).decode()

            expiry = float(base64.urlsafe_b64decode(expiry_base64).decode())

            response.update(token=token, expiry=expiry)

        except Exception as ex:
            response.update(response_info=repr(ex))
            return response

        if float(now_epoch) < expiry:
            confirmation_code_valid = self.validate_hash_match_v2(
                raw_string=token, hashed_to_match=random_string_hashed
            )
            response.update(token_valid=confirmation_code_valid)
        else:
            response.update(response_info="Token expired")

        return response

    def _encrypt_aes128(self, plaintext: str, fernet_key: bytes) -> str:
        """
        Encrypts a string using Fernet symmetric encryption.

        This function encrypts a given string with Fernet, encoding the
        input to bytes, then encrypting.

        :param plaintext: The plaintext string to be encrypted.
        :param fernet_key: The secret key used for encryption. Must be a
               URL-safe base64-encoded 32-byte key.
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe.
        """

        # Ensure the Fernet key length is valid
        # For a bytes_length of 32, the length of the Base64-encoded
        # string without stripping padding would be 44 characters.
        self._ensure_len(
            key=fernet_key,
            n=44,
            exc_msg="Fernet key must be a URL-safe base64-encoded and 32-byte key",
        )

        cipher_suite = cryptography.fernet.Fernet(key=fernet_key)

        b_string_to_encrypt = plaintext.encode()
        b_encrypted = cipher_suite.encrypt(b_string_to_encrypt)

        s_encrypted_clean = b_encrypted.decode()

        # Add alg info prefix
        alg_prefix = EncryptionAlgorithm.AES_128.value
        s_encrypted_clean_with_alg = f"{alg_prefix}{s_encrypted_clean}"

        return s_encrypted_clean_with_alg

    def _decrypt_aes128(self, ciphertext: str, fernet_key: bytes) -> str:
        """
        Decrypts a string previously encrypted by _encrypt_string_aes128

        Attempts to decrypt the provided string using the given Fernet
        key. If decryption fails, it catches the exception, logs a
        warning, and returns an empty string to indicate failure.

        :param ciphertext: The encrypted string to be decrypted.
        :param fernet_key: The secret key used for decryption.
               Must match the key used for encryption.
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        # Ensure the Fernet key length is valid
        # For a bytes_length of 32, the length of the Base64-encoded
        # string without stripping padding would be 44 characters.
        self._ensure_len(
            key=fernet_key,
            n=44,
            exc_msg="Fernet key must be a URL-safe base64-encoded and 32-byte key",
        )

        ciphertext = self._get_encrypted_ciphertext(ciphertext=ciphertext)

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
                 encrypted data is text-safe.
        """

        # Ensure the AES key length is valid for AES-256
        self._ensure_len(key=key, n=32, exc_msg="AES-256 must be 32-byte key")

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
        ciphertext = self._b64u_encode(b_ciphertext_signed_salt)

        # Add alg info prefix
        alg_prefix = EncryptionAlgorithm.AES_256.value
        ciphertext = f"{alg_prefix}{ciphertext}"

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
        :param key: The secret key used for encryption.
               Must be a 32-byte key for AES-256.
        :return: The decrypted plaintext string. Returns an empty string
                 and logs a warning if decryption fails.
        """

        # Ensure the AES key length is valid for AES-256
        self._ensure_len(key=key, n=32, exc_msg="AES-256 must be 32-byte key")

        ciphertext = self._get_encrypted_ciphertext(ciphertext=ciphertext)

        # Decode base64 to reveal the &
        b_ciphertext_signed_salt = self._b64u_decode(ciphertext)

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

    def _encrypt_aes_gcm(self, plaintext: str, key: bytes, aad: Optional[bytes] = None) -> str:
        """
        Encrypts a string using AES-GCM symmetric encryption.

        :param plaintext: The plaintext string to be encrypted.
        :param key: The secret key used for encryption. Must be a
               32-byte key.
        :param aad: Additional authenticated data (AAD) to be
               authenticated but not encrypted. It must be provided
               as a byte string if used.
        :return: The encrypted string, encoded with Base64 to ensure the
                 encrypted data is text-safe.
        """

        # Ensure the AES key length is valid for AES-GCM
        self._ensure_len(key=key, n=32, exc_msg="AES-GCM must be 32-byte key")

        # 96-bit recommended
        nonce = self._rand_bytes(12)
        aead = cryptography.hazmat.primitives.ciphers.aead.AESGCM(key)

        ct = aead.encrypt(nonce=nonce, data=plaintext.encode(), associated_data=aad)

        # Envelope: nonce || ct (ct already includes tag)
        blob = self._b64u_encode(nonce + ct)

        # Add alg info prefix
        alg_prefix = EncryptionAlgorithm.AES_GCM.value
        encrypted = f"{alg_prefix}{blob}"

        return encrypted

    def _decrypt_aes_gcm(self, ciphertext: str, key: bytes, aad: Optional[bytes] = None) -> str:
        """
        Decrypts a string that was encrypted using AES-GCM symmetric
        encryption.

        :param ciphertext: The encrypted string to be decrypted.
        :param key: The secret key used for encryption. Must be a
               32-byte key.
        :param aad: Additional authenticated data (AAD) that was
               authenticated but not encrypted. It must be provided
               as a byte string if used.
        :return: The decrypted plaintext string.
        """

        # Ensure the AES key length is valid for AES-GCM
        self._ensure_len(key=key, n=32, exc_msg="AES-GCM must be 32-byte key")

        ciphertext = self._get_encrypted_ciphertext(ciphertext=ciphertext)

        blob = self._b64u_decode(ciphertext)

        nonce, ct = blob[:12], blob[12:]
        aead = cryptography.hazmat.primitives.ciphers.aead.AESGCM(key)

        try:
            pt = aead.decrypt(nonce=nonce, data=ct, associated_data=aad)
        except Exception as ex:
            self.logger.warning(f"GCM decryption failed (bad tag/AAD/nonce): {ex}")
            return ""

        decrypted = pt.decode()

        return decrypted

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

    def _get_encrypted_ciphertext(self, ciphertext: str) -> str:
        """
        Extracts the encrypted ciphertext from the input string.

        :param ciphertext: The input string containing the encrypted
               ciphertext and other information.
        :return: The encrypted ciphertext as a string.
        """

        self.logger.debug("Getting encrypted ciphertext")

        # Remove alg info prefix
        # Using if for older stored values
        for alg in EncryptionAlgorithm.all_alg_prefixes():
            if ciphertext.startswith(alg):
                start = len(alg)
                ciphertext = ciphertext[start:]
                break

        # Correct the Base64 padding if necessary
        missing_padding = len(ciphertext) % 4
        if missing_padding:
            ciphertext += "=" * (4 - missing_padding)

        return ciphertext

    def _b64u_encode(self, b: bytes) -> str:
        """
        Encodes a byte string to a Base64 URL-safe string.

        :param b: The byte string to be encoded.
        :return: The Base64 URL-safe encoded string.
        """

        encoded = base64.urlsafe_b64encode(b).decode()

        return encoded

    def _b64u_decode(self, s: str) -> bytes:
        """
        Decodes a Base64 URL-safe encoded string to a byte string.

        :param s: The Base64 URL-safe encoded string to be decoded.
        :return: The decoded byte string.
        """

        decoded = base64.urlsafe_b64decode(s.encode())

        return decoded

    def _rand_bytes(self, n: int) -> bytes:
        """
        Generates cryptographically secure random bytes.

        :param n: The number of random bytes to generate.
        :return: A byte string containing the generated random bytes.
        """

        self.logger.debug(f"Generating {n} random bytes")

        b = os.urandom(n)

        return b

    def _ensure_len(self, key: bytes, n: int, exc_msg: str) -> None:
        """
        Ensures that a byte string is of a specific length.

        :param key: The byte string to be checked.
        :param n: The expected length of the byte string.
        :param exc_msg: The exception message to be raised if the
               length check fails.
        :raise: ValueError is raised if the byte string's length does
                not match the expected length.
        """

        self.logger.debug(f"Ensuring key length is {n} bytes")

        if len(key) != n:
            self.logger.error(exc_msg)
            raise ValueError(exc_msg)
