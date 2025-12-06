"""
Hash Facade - Static interface to hash manager.
"""

from typing import Optional

from fastpy_cli.libs.hashing.hasher import Hasher
from fastpy_cli.libs.hashing.manager import HashManager
from fastpy_cli.libs.support.container import container

# Register the hash manager in the container
container.singleton("hash", lambda c: HashManager())


class Hash:
    """
    Hash Facade providing static access to password hashing.

    Usage:
        # Hash a password
        hashed = Hash.make('password')

        # Verify a password
        if Hash.check('password', hashed):
            print('Password is valid')

        # Check if rehash is needed
        if Hash.needs_rehash(hashed):
            new_hash = Hash.make('password')

        # Use a specific driver
        hashed = Hash.driver('argon2').make('password')

        # Configure a driver
        Hash.configure('bcrypt', {'rounds': 14})
    """

    @staticmethod
    def _manager() -> HashManager:
        """Get the hash manager from container."""
        return container.make("hash")

    @classmethod
    def make(cls, value: str, options: Optional[dict] = None) -> str:
        """
        Hash a value.

        Args:
            value: The value to hash
            options: Optional driver-specific options

        Returns:
            The hashed value
        """
        return cls._manager().make(value, options)

    @classmethod
    def check(cls, value: str, hashed_value: str) -> bool:
        """
        Check if a value matches a hash.

        Args:
            value: The plain value
            hashed_value: The hashed value to check against

        Returns:
            True if the value matches the hash
        """
        return cls._manager().check(value, hashed_value)

    @classmethod
    def needs_rehash(
        cls, hashed_value: str, options: Optional[dict] = None
    ) -> bool:
        """
        Check if a hash needs to be rehashed.

        This is useful for upgrading hash parameters over time.

        Args:
            hashed_value: The hash to check
            options: Optional desired options

        Returns:
            True if the hash should be regenerated
        """
        return cls._manager().needs_rehash(hashed_value, options)

    @classmethod
    def get_info(cls, hashed_value: str) -> dict:
        """
        Get information about a hash.

        Args:
            hashed_value: The hash to inspect

        Returns:
            Dict with algorithm info
        """
        return cls._manager().get_info(hashed_value)

    @classmethod
    def driver(cls, name: str) -> Hasher:
        """
        Get a specific hashing driver.

        Args:
            name: Driver name ('bcrypt', 'argon2', 'sha256')

        Returns:
            The hasher instance
        """
        return cls._manager().driver(name)

    @classmethod
    def configure(cls, driver: str, config: dict) -> None:
        """
        Configure a driver.

        Args:
            driver: Driver name
            config: Configuration dict

        Example:
            Hash.configure('bcrypt', {'rounds': 14})
            Hash.configure('argon2', {'memory_cost': 131072})
        """
        cls._manager().configure(driver, config)

    @classmethod
    def extend(cls, name: str, driver_class: type[Hasher]) -> None:
        """
        Register a custom hasher.

        Args:
            name: Driver name
            driver_class: Hasher subclass
        """
        cls._manager().extend(name, driver_class)

    @classmethod
    def set_default(cls, driver: str) -> None:
        """
        Set the default hashing driver.

        Args:
            driver: Driver name
        """
        cls._manager().set_default(driver)
