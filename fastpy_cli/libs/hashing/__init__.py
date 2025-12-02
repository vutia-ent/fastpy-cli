"""
Hashing Facade - Secure password hashing.

Usage:
    from fastpy_cli.libs import Hash

    # Hash a password
    hashed = Hash.make('password')

    # Verify a password
    if Hash.check('password', hashed):
        print('Password is valid')

    # Check if rehash needed (for upgrading parameters)
    if Hash.needs_rehash(hashed):
        new_hash = Hash.make('password')

    # Use specific driver
    hashed = Hash.driver('argon2').make('password')

Supported Drivers:
    - bcrypt: Industry standard, good default (default)
    - argon2: Modern, memory-hard algorithm (recommended for new apps)
    - sha256: PBKDF2-SHA256 (fallback, not recommended for passwords)
"""

from fastpy_cli.libs.hashing.hasher import (
    Hasher,
    BcryptHasher,
    Argon2Hasher,
    SHA256Hasher,
)
from fastpy_cli.libs.hashing.manager import HashManager
from fastpy_cli.libs.hashing.facade import Hash

__all__ = [
    "Hash",
    "Hasher",
    "HashManager",
    "BcryptHasher",
    "Argon2Hasher",
    "SHA256Hasher",
]
