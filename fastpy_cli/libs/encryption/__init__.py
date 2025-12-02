"""
Encryption Facade - Secure data encryption.

Usage:
    from fastpy_cli.libs import Crypt

    # Generate a key (do this once, save to .env as APP_KEY)
    key = Crypt.generate_key()

    # Set the key (or use APP_KEY environment variable)
    Crypt.set_key(key)

    # Encrypt data
    encrypted = Crypt.encrypt('secret data')
    encrypted = Crypt.encrypt({'user': 'john', 'id': 123})

    # Decrypt data
    data = Crypt.decrypt(encrypted)

    # Use specific driver
    encrypted = Crypt.driver('aes').encrypt('secret')

Supported Drivers:
    - fernet: Fernet (AES-128-CBC with HMAC) - recommended, default
    - aes: Raw AES-256-CBC - more control, less abstraction
"""

from fastpy_cli.libs.encryption.encrypter import (
    Encrypter,
    FernetEncrypter,
    AESEncrypter,
)
from fastpy_cli.libs.encryption.facade import Crypt, StringEncrypter

__all__ = [
    "Crypt",
    "Encrypter",
    "FernetEncrypter",
    "AESEncrypter",
    "StringEncrypter",
]
