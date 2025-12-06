"""
Hash Manager - Manages multiple hashing drivers.
"""

from typing import Optional

from fastpy_cli.libs.hashing.hasher import (
    Argon2Hasher,
    BcryptHasher,
    Hasher,
    SHA256Hasher,
)


class HashManager:
    """
    Hash manager that supports multiple hashing algorithms.

    Usage:
        manager = HashManager()
        hashed = manager.make('password')
        is_valid = manager.check('password', hashed)
    """

    _drivers: dict[str, type[Hasher]] = {
        "bcrypt": BcryptHasher,
        "argon2": Argon2Hasher,
        "sha256": SHA256Hasher,
    }

    _instances: dict[str, Hasher] = {}

    def __init__(self, default_driver: str = "bcrypt"):
        self._default_driver = default_driver
        self._config: dict[str, dict] = {}

    def driver(self, name: Optional[str] = None) -> Hasher:
        """Get a hasher driver."""
        name = name or self._default_driver

        if name not in self._instances:
            if name not in self._drivers:
                raise ValueError(f"Hash driver '{name}' not registered")

            config = self._config.get(name, {})
            self._instances[name] = self._drivers[name](**config)

        return self._instances[name]

    def configure(self, driver: str, config: dict) -> "HashManager":
        """Configure a driver."""
        self._config[driver] = config

        # Clear instance to force reconfiguration
        if driver in self._instances:
            del self._instances[driver]

        return self

    def extend(self, name: str, driver_class: type[Hasher]) -> "HashManager":
        """Register a custom hasher."""
        self._drivers[name] = driver_class
        return self

    def set_default(self, driver: str) -> "HashManager":
        """Set the default driver."""
        self._default_driver = driver
        return self

    def make(self, value: str, options: Optional[dict] = None) -> str:
        """Hash a value using the default driver."""
        return self.driver().make(value, options)

    def check(self, value: str, hashed_value: str) -> bool:
        """Check a value against a hash using the appropriate driver."""
        # Try to detect the algorithm from the hash
        driver = self._detect_driver(hashed_value)
        return self.driver(driver).check(value, hashed_value)

    def needs_rehash(self, hashed_value: str, options: Optional[dict] = None) -> bool:
        """Check if hash needs rehashing."""
        driver = self._detect_driver(hashed_value)

        # If the detected driver is not the default, it needs rehashing
        if driver != self._default_driver:
            return True

        return self.driver(driver).needs_rehash(hashed_value, options)

    def get_info(self, hashed_value: str) -> dict:
        """Get information about a hash."""
        driver = self._detect_driver(hashed_value)
        return self.driver(driver).get_info(hashed_value)

    def _detect_driver(self, hashed_value: str) -> str:
        """Detect the hashing algorithm from a hash."""
        if hashed_value.startswith("$2"):
            return "bcrypt"
        elif hashed_value.startswith("$argon2"):
            return "argon2"
        elif hashed_value.startswith("$pbkdf2-sha256"):
            return "sha256"

        return self._default_driver
