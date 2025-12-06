"""
Password Hashing - Secure password hashing with multiple algorithms.
"""

import hashlib
import secrets
from abc import ABC, abstractmethod
from typing import Optional


class Hasher(ABC):
    """Base class for password hashers."""

    @abstractmethod
    def make(self, value: str, options: Optional[dict] = None) -> str:
        """Hash a value."""
        pass

    @abstractmethod
    def check(self, value: str, hashed_value: str) -> bool:
        """Check if a value matches a hash."""
        pass

    @abstractmethod
    def needs_rehash(self, hashed_value: str, options: Optional[dict] = None) -> bool:
        """Check if the hash needs to be rehashed."""
        pass

    @abstractmethod
    def get_info(self, hashed_value: str) -> dict:
        """Get information about a hash."""
        pass


class BcryptHasher(Hasher):
    """Bcrypt password hasher."""

    def __init__(self, rounds: int = 13):
        # SECURITY: Default to 13 rounds (2^13 iterations)
        # Increase this value over time as hardware improves
        # 12 is the minimum recommended, 13-14 provides better security margin
        self.rounds = rounds

    def make(self, value: str, options: Optional[dict] = None) -> str:
        """Hash a value using bcrypt."""
        try:
            import bcrypt
        except ImportError as err:
            raise ImportError(
                "bcrypt package required. Install with: pip install bcrypt"
            ) from err

        options = options or {}
        rounds = options.get("rounds", self.rounds)

        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(value.encode("utf-8"), salt).decode("utf-8")

    def check(self, value: str, hashed_value: str) -> bool:
        """Verify a value against a bcrypt hash."""
        try:
            import bcrypt
        except ImportError as err:
            raise ImportError(
                "bcrypt package required. Install with: pip install bcrypt"
            ) from err

        try:
            return bcrypt.checkpw(
                value.encode("utf-8"), hashed_value.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    def needs_rehash(self, hashed_value: str, options: Optional[dict] = None) -> bool:
        """Check if bcrypt hash needs rehashing."""
        options = options or {}
        desired_rounds = options.get("rounds", self.rounds)

        info = self.get_info(hashed_value)
        if info.get("algorithm") != "bcrypt":
            return True

        return info.get("rounds", 0) < desired_rounds

    def get_info(self, hashed_value: str) -> dict:
        """Get bcrypt hash information."""
        try:
            # Bcrypt format: $2a$12$...
            parts = hashed_value.split("$")
            if len(parts) >= 4 and parts[1] in ("2a", "2b", "2y"):
                return {
                    "algorithm": "bcrypt",
                    "algorithm_version": parts[1],
                    "rounds": int(parts[2]),
                }
        except (ValueError, IndexError):
            pass

        return {"algorithm": "unknown"}


class Argon2Hasher(Hasher):
    """Argon2 password hasher (recommended for new applications)."""

    def __init__(
        self,
        memory_cost: int = 65536,
        time_cost: int = 3,
        parallelism: int = 4,
    ):
        self.memory_cost = memory_cost
        self.time_cost = time_cost
        self.parallelism = parallelism

    def make(self, value: str, options: Optional[dict] = None) -> str:
        """Hash a value using Argon2."""
        try:
            from argon2 import PasswordHasher
        except ImportError as err:
            raise ImportError(
                "argon2-cffi package required. Install with: pip install argon2-cffi"
            ) from err

        options = options or {}
        ph = PasswordHasher(
            memory_cost=options.get("memory_cost", self.memory_cost),
            time_cost=options.get("time_cost", self.time_cost),
            parallelism=options.get("parallelism", self.parallelism),
        )
        return ph.hash(value)

    def check(self, value: str, hashed_value: str) -> bool:
        """Verify a value against an Argon2 hash."""
        try:
            from argon2 import PasswordHasher
            from argon2.exceptions import InvalidHashError, VerifyMismatchError
        except ImportError as err:
            raise ImportError(
                "argon2-cffi package required. Install with: pip install argon2-cffi"
            ) from err

        ph = PasswordHasher()
        try:
            return ph.verify(hashed_value, value)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, hashed_value: str, options: Optional[dict] = None) -> bool:
        """Check if Argon2 hash needs rehashing."""
        try:
            from argon2 import PasswordHasher
        except ImportError:
            return True

        options = options or {}
        ph = PasswordHasher(
            memory_cost=options.get("memory_cost", self.memory_cost),
            time_cost=options.get("time_cost", self.time_cost),
            parallelism=options.get("parallelism", self.parallelism),
        )
        return ph.check_needs_rehash(hashed_value)

    def get_info(self, hashed_value: str) -> dict:
        """Get Argon2 hash information."""
        try:
            from argon2 import extract_parameters
            params = extract_parameters(hashed_value)
            return {
                "algorithm": "argon2",
                "memory_cost": params.memory_cost,
                "time_cost": params.time_cost,
                "parallelism": params.parallelism,
            }
        except Exception:
            return {"algorithm": "unknown"}


class SHA256Hasher(Hasher):
    """
    SHA256 hasher with salt using PBKDF2.

    Note: Not recommended for passwords. Use bcrypt or argon2 instead.
    This is provided as a fallback when bcrypt/argon2 are not available.
    """

    def __init__(self, iterations: int = 600000):
        # SECURITY: OWASP recommends 600,000+ iterations for PBKDF2-SHA256 (2023)
        # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
        self.iterations = iterations

    def make(self, value: str, options: Optional[dict] = None) -> str:
        """Hash a value using PBKDF2-SHA256."""
        options = options or {}
        iterations = options.get("iterations", self.iterations)

        salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return f"$pbkdf2-sha256${iterations}${salt}${dk.hex()}"

    def check(self, value: str, hashed_value: str) -> bool:
        """Verify a value against a PBKDF2-SHA256 hash."""
        try:
            parts = hashed_value.split("$")
            if len(parts) != 5 or parts[1] != "pbkdf2-sha256":
                return False

            iterations = int(parts[2])
            salt = parts[3]
            stored_hash = parts[4]

            dk = hashlib.pbkdf2_hmac(
                "sha256",
                value.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            return secrets.compare_digest(dk.hex(), stored_hash)
        except (ValueError, IndexError):
            return False

    def needs_rehash(self, hashed_value: str, options: Optional[dict] = None) -> bool:
        """Check if hash needs rehashing."""
        options = options or {}
        desired_iterations = options.get("iterations", self.iterations)

        info = self.get_info(hashed_value)
        if info.get("algorithm") != "pbkdf2-sha256":
            return True

        return info.get("iterations", 0) < desired_iterations

    def get_info(self, hashed_value: str) -> dict:
        """Get hash information."""
        try:
            parts = hashed_value.split("$")
            if len(parts) == 5 and parts[1] == "pbkdf2-sha256":
                return {
                    "algorithm": "pbkdf2-sha256",
                    "iterations": int(parts[2]),
                }
        except (ValueError, IndexError):
            pass

        return {"algorithm": "unknown"}
