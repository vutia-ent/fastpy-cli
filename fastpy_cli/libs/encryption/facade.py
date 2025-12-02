"""
Crypt Facade - Static interface to encryption.
"""

from typing import Any, Optional, Type

from fastpy_cli.libs.encryption.encrypter import (
    Encrypter,
    FernetEncrypter,
    AESEncrypter,
)
from fastpy_cli.libs.support.container import container


class Crypt:
    """
    Crypt Facade providing static access to encryption.

    Usage:
        # Generate a key (do this once, save to .env)
        key = Crypt.generate_key()

        # Encrypt a value
        encrypted = Crypt.encrypt('secret data')

        # Decrypt a value
        decrypted = Crypt.decrypt(encrypted)

        # Encrypt complex data (auto JSON serialized)
        encrypted = Crypt.encrypt({'user_id': 123, 'token': 'abc'})
        data = Crypt.decrypt(encrypted)  # Returns dict

        # Use specific driver
        encrypted = Crypt.driver('aes').encrypt('secret')

    Environment:
        Set APP_KEY environment variable with your encryption key.
    """

    _default_driver: str = "fernet"
    _drivers: dict = {}
    _driver_classes: dict = {
        "fernet": FernetEncrypter,
        "aes": AESEncrypter,
    }
    _key: Optional[str] = None

    @classmethod
    def set_key(cls, key: str) -> None:
        """
        Set the encryption key.

        Args:
            key: The encryption key
        """
        cls._key = key
        cls._drivers.clear()  # Clear cached drivers

    @classmethod
    def driver(cls, name: Optional[str] = None) -> Encrypter:
        """
        Get an encrypter driver.

        Args:
            name: Driver name ('fernet', 'aes')

        Returns:
            Encrypter instance
        """
        name = name or cls._default_driver

        if name not in cls._drivers:
            if name not in cls._driver_classes:
                raise ValueError(f"Encryption driver '{name}' not registered")

            cls._drivers[name] = cls._driver_classes[name](cls._key)

        return cls._drivers[name]

    @classmethod
    def encrypt(cls, value: Any) -> str:
        """
        Encrypt a value.

        Args:
            value: Value to encrypt (strings, dicts, lists, etc.)

        Returns:
            Encrypted string
        """
        return cls.driver().encrypt(value)

    @classmethod
    def decrypt(cls, payload: str) -> Any:
        """
        Decrypt a value.

        Args:
            payload: Encrypted string

        Returns:
            Decrypted value
        """
        return cls.driver().decrypt(payload)

    @classmethod
    def encrypt_string(cls, value: str) -> str:
        """
        Encrypt a string value.

        Args:
            value: String to encrypt

        Returns:
            Encrypted string
        """
        return cls.encrypt(value)

    @classmethod
    def decrypt_string(cls, payload: str) -> str:
        """
        Decrypt to a string.

        Args:
            payload: Encrypted string

        Returns:
            Decrypted string
        """
        result = cls.decrypt(payload)
        if not isinstance(result, str):
            raise ValueError("Decrypted value is not a string")
        return result

    @classmethod
    def generate_key(cls, cipher: str = "fernet") -> str:
        """
        Generate a secure encryption key.

        Args:
            cipher: Cipher type ('fernet', 'AES-256-CBC', 'AES-128-CBC')

        Returns:
            Base64-encoded key

        Example:
            key = Crypt.generate_key()
            # Add to .env: APP_KEY=<key>
        """
        if cipher == "fernet":
            return FernetEncrypter.generate_key()
        else:
            return AESEncrypter.generate_key(cipher)

    @classmethod
    def set_default(cls, driver: str) -> None:
        """
        Set the default encryption driver.

        Args:
            driver: Driver name ('fernet', 'aes')
        """
        cls._default_driver = driver

    @classmethod
    def extend(cls, name: str, driver_class: Type[Encrypter]) -> None:
        """
        Register a custom encrypter.

        Args:
            name: Driver name
            driver_class: Encrypter subclass
        """
        cls._driver_classes[name] = driver_class


class StringEncrypter:
    """
    Helper for encrypting/decrypting strings with a specific key.

    Usage:
        encrypter = StringEncrypter(key)
        encrypted = encrypter.encrypt('secret')
        decrypted = encrypter.decrypt(encrypted)
    """

    def __init__(self, key: str, driver: str = "fernet"):
        if driver == "fernet":
            self._encrypter = FernetEncrypter(key)
        elif driver == "aes":
            self._encrypter = AESEncrypter(key)
        else:
            raise ValueError(f"Unknown driver: {driver}")

    def encrypt(self, value: str) -> str:
        """Encrypt a string."""
        return self._encrypter.encrypt(value)

    def decrypt(self, payload: str) -> str:
        """Decrypt a string."""
        result = self._encrypter.decrypt(payload)
        if not isinstance(result, str):
            raise ValueError("Decrypted value is not a string")
        return result
