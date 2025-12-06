"""
Encryption - AES encryption with multiple modes.
"""

import base64
import json
import os
import secrets
from abc import ABC, abstractmethod
from typing import Any, Optional


class Encrypter(ABC):
    """Base class for encrypters."""

    @abstractmethod
    def encrypt(self, value: Any) -> str:
        """Encrypt a value."""
        pass

    @abstractmethod
    def decrypt(self, payload: str) -> Any:
        """Decrypt a value."""
        pass

    @staticmethod
    def generate_key(cipher: str = "AES-256-CBC") -> str:
        """Generate a secure encryption key."""
        if cipher == "AES-256-CBC":
            # 256-bit key
            return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
        elif cipher == "AES-128-CBC":
            # 128-bit key
            return base64.b64encode(secrets.token_bytes(16)).decode("utf-8")
        else:
            raise ValueError(f"Unsupported cipher: {cipher}")


class FernetEncrypter(Encrypter):
    """
    Fernet (AES-128-CBC) encrypter using cryptography library.

    This is the recommended encrypter for most use cases.
    """

    def __init__(self, key: Optional[str] = None):
        try:
            from cryptography.fernet import Fernet
        except ImportError as err:
            raise ImportError(
                "cryptography package required. Install with: pip install cryptography"
            ) from err

        if key is None:
            key = os.environ.get("APP_KEY")

        if not key:
            raise ValueError(
                "No encryption key provided. Set APP_KEY environment variable "
                "or pass key to constructor."
            )

        # Ensure key is properly formatted for Fernet
        try:
            if len(base64.urlsafe_b64decode(key)) != 32:
                raise ValueError("Key must be 32 bytes when decoded")
            self._key = key.encode() if isinstance(key, str) else key
        except Exception:
            # Try to use key as raw bytes
            if len(key) == 32:
                self._key = base64.urlsafe_b64encode(key.encode())
            else:
                raise ValueError(
                    "Invalid key format. Use Crypt.generate_key() to create a valid key."
                ) from None

        self._fernet = Fernet(self._key)

    def encrypt(self, value: Any) -> str:
        """
        Encrypt a value.

        Args:
            value: Value to encrypt (will be JSON serialized if not string)

        Returns:
            Base64-encoded encrypted string
        """
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)

        if isinstance(value, str):
            value = value.encode("utf-8")

        encrypted = self._fernet.encrypt(value)
        return encrypted.decode("utf-8")

    def decrypt(self, payload: str) -> Any:
        """
        Decrypt a value.

        Args:
            payload: Encrypted string

        Returns:
            Decrypted value
        """
        from cryptography.fernet import InvalidToken

        try:
            decrypted = self._fernet.decrypt(payload.encode("utf-8"))
            value = decrypted.decode("utf-8")

            # Try to JSON decode
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except InvalidToken:
            raise ValueError("Invalid or corrupted payload") from None

    @staticmethod
    def generate_key(cipher: str = "fernet") -> str:
        """Generate a Fernet-compatible key."""
        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode("utf-8")


class AESEncrypter(Encrypter):
    """
    Raw AES-256-CBC encrypter for more control.

    Note: FernetEncrypter is recommended for most use cases.
    """

    def __init__(self, key: Optional[str] = None):
        try:
            from cryptography.hazmat.primitives.ciphers import (  # noqa: F401
                Cipher,
                algorithms,
                modes,
            )
        except ImportError as err:
            raise ImportError(
                "cryptography package required. Install with: pip install cryptography"
            ) from err

        if key is None:
            key = os.environ.get("APP_KEY")

        if not key:
            raise ValueError("No encryption key provided")

        # Decode key from base64
        try:
            self._key = base64.b64decode(key)
            if len(self._key) not in (16, 24, 32):
                raise ValueError("Key must be 16, 24, or 32 bytes")
        except Exception:
            raise ValueError("Invalid key format") from None

    def encrypt(self, value: Any) -> str:
        """Encrypt a value using AES-256-CBC."""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)

        if isinstance(value, str):
            value = value.encode("utf-8")

        # Generate random IV
        iv = secrets.token_bytes(16)

        # Pad the data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(value) + padder.finalize()

        # Encrypt
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # Create payload with IV
        payload = {
            "iv": base64.b64encode(iv).decode("utf-8"),
            "value": base64.b64encode(encrypted).decode("utf-8"),
            "mac": self._create_mac(iv, encrypted),
        }

        return base64.b64encode(json.dumps(payload).encode()).decode("utf-8")

    def decrypt(self, payload: str) -> Any:
        """Decrypt an AES-256-CBC encrypted value."""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        try:
            # Decode payload
            data = json.loads(base64.b64decode(payload))
            iv = base64.b64decode(data["iv"])
            encrypted = base64.b64decode(data["value"])
            mac = data["mac"]

            # Verify MAC
            if not secrets.compare_digest(mac, self._create_mac(iv, encrypted)):
                raise ValueError("MAC verification failed")

            # Decrypt
            cipher = Cipher(algorithms.AES(self._key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted) + decryptor.finalize()

            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            value = unpadder.update(decrypted) + unpadder.finalize()

            # Try to JSON decode
            value_str = value.decode("utf-8")
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str

        except (KeyError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid or corrupted payload: {e}") from e

    def _create_mac(self, iv: bytes, value: bytes) -> str:
        """Create HMAC for payload verification."""
        import hashlib
        import hmac

        data = base64.b64encode(iv) + base64.b64encode(value)
        mac = hmac.new(self._key, data, hashlib.sha256)
        return mac.hexdigest()

    @staticmethod
    def generate_key(cipher: str = "AES-256-CBC") -> str:
        """Generate an AES key."""
        if "256" in cipher:
            return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
        elif "192" in cipher:
            return base64.b64encode(secrets.token_bytes(24)).decode("utf-8")
        else:
            return base64.b64encode(secrets.token_bytes(16)).decode("utf-8")
