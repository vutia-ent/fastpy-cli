"""
Cache Facade - Static interface to cache manager.
"""

from typing import Any, Callable, Optional

from fastpy_cli.libs.cache.drivers import CacheDriver
from fastpy_cli.libs.cache.manager import CacheManager, TaggedCache
from fastpy_cli.libs.support.container import container

# Register the cache manager in the container
container.singleton("cache", lambda c: CacheManager())


class Cache:
    """
    Cache Facade providing static access to cache manager.

    Usage:
        # Basic operations
        Cache.put('key', 'value', ttl=3600)
        value = Cache.get('key', default='fallback')

        # Remember pattern
        user = Cache.remember('user:1', 3600, lambda: User.find(1))

        # Tags
        Cache.tags(['users']).put('user:1', user)
        Cache.tags(['users']).flush()
    """

    @staticmethod
    def _manager() -> CacheManager:
        """Get the cache manager from container."""
        return container.make("cache")

    @classmethod
    def store(cls, name: str) -> CacheDriver:
        """Get a specific cache store."""
        return cls._manager().store(name)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from the cache."""
        return cls._manager().get(key, default)

    @classmethod
    def put(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache."""
        return cls._manager().put(key, value, ttl)

    @classmethod
    def forget(cls, key: str) -> bool:
        """Remove a value from the cache."""
        return cls._manager().forget(key)

    @classmethod
    def flush(cls) -> bool:
        """Clear all values from the cache."""
        return cls._manager().flush()

    @classmethod
    def has(cls, key: str) -> bool:
        """Check if a key exists."""
        return cls._manager().has(key)

    @classmethod
    def get_many(cls, keys: list[str]) -> dict[str, Any]:
        """Get multiple values."""
        return cls._manager().get_many(keys)

    @classmethod
    def put_many(cls, values: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store multiple values."""
        return cls._manager().put_many(values, ttl)

    @classmethod
    def increment(cls, key: str, value: int = 1) -> int:
        """Increment a value."""
        return cls._manager().increment(key, value)

    @classmethod
    def decrement(cls, key: str, value: int = 1) -> int:
        """Decrement a value."""
        return cls._manager().decrement(key, value)

    @classmethod
    def remember(
        cls,
        key: str,
        ttl: Optional[int],
        callback: Callable[[], Any],
    ) -> Any:
        """Get or set a value."""
        return cls._manager().remember(key, ttl, callback)

    @classmethod
    def forever(cls, key: str, value: Any) -> bool:
        """Store a value forever."""
        return cls._manager().forever(key, value)

    @classmethod
    def tags(cls, tags: list[str]) -> TaggedCache:
        """Get a tagged cache instance."""
        return cls._manager().tags(tags)

    @classmethod
    def register_store(cls, name: str, driver: CacheDriver) -> None:
        """Register a cache store."""
        cls._manager().register_store(name, driver)

    @classmethod
    def set_default_store(cls, name: str) -> None:
        """Set the default store."""
        cls._manager().set_default_store(name)

    # Testing utilities
    @classmethod
    def fake(cls) -> "CacheFake":
        """
        Fake cache for testing.

        Usage:
            Cache.fake()
            Cache.put('key', 'value')
            Cache.assert_has('key')
        """
        fake = CacheFake()
        container.instance("cache", fake)
        return fake


class CacheFake:
    """Fake cache for testing."""

    def __init__(self):
        self._store: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self._store[key] = value
        return True

    def forget(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def flush(self) -> bool:
        self._store.clear()
        return True

    def has(self, key: str) -> bool:
        return key in self._store

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        return {k: self._store.get(k) for k in keys}

    def put_many(self, values: dict[str, Any], ttl: Optional[int] = None) -> bool:
        self._store.update(values)
        return True

    def increment(self, key: str, value: int = 1) -> int:
        current = self._store.get(key, 0)
        self._store[key] = current + value
        return self._store[key]

    def decrement(self, key: str, value: int = 1) -> int:
        return self.increment(key, -value)

    def remember(self, key: str, ttl: Optional[int], callback: Callable[[], Any]) -> Any:
        if key in self._store:
            return self._store[key]
        value = callback()
        self._store[key] = value
        return value

    def forever(self, key: str, value: Any) -> bool:
        return self.put(key, value)

    def tags(self, tags: list[str]) -> "CacheFake":
        return self

    def assert_has(self, key: str) -> bool:
        if key not in self._store:
            raise AssertionError(f"Key '{key}' not found in cache")
        return True

    def assert_missing(self, key: str) -> bool:
        if key in self._store:
            raise AssertionError(f"Key '{key}' was found in cache")
        return True
