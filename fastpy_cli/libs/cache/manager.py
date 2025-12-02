"""
Cache Manager implementation.
"""

from typing import Any, Callable, Dict, List, Optional

from fastpy_cli.libs.cache.drivers import CacheDriver, MemoryDriver


class TaggedCache:
    """Cache with tag support for grouped invalidation."""

    def __init__(self, driver: CacheDriver, tags: List[str]):
        self._driver = driver
        self._tags = tags

    def _tag_key(self, key: str) -> str:
        """Create a tagged key."""
        tag_prefix = ":".join(sorted(self._tags))
        return f"tag:{tag_prefix}:{key}"

    def get(self, key: str) -> Any:
        return self._driver.get(self._tag_key(key))

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # Store the key in tag sets for later flushing
        for tag in self._tags:
            tag_set_key = f"tag_set:{tag}"
            keys = self._driver.get(tag_set_key) or []
            if key not in keys:
                keys.append(key)
                self._driver.put(tag_set_key, keys)

        return self._driver.put(self._tag_key(key), value, ttl)

    def forget(self, key: str) -> bool:
        return self._driver.forget(self._tag_key(key))

    def flush(self) -> bool:
        """Flush all keys with these tags."""
        for tag in self._tags:
            tag_set_key = f"tag_set:{tag}"
            keys = self._driver.get(tag_set_key) or []

            for key in keys:
                self._driver.forget(self._tag_key(key))

            self._driver.forget(tag_set_key)

        return True


class CacheManager:
    """
    Cache manager supporting multiple stores.
    """

    _stores: Dict[str, CacheDriver] = {}
    _default_store: str = "memory"

    def __init__(self):
        # Register default memory store
        if "memory" not in self._stores:
            self._stores["memory"] = MemoryDriver()

    @classmethod
    def store(cls, name: str) -> CacheDriver:
        """Get a specific cache store."""
        if name not in cls._stores:
            raise ValueError(f"Cache store '{name}' not registered")
        return cls._stores[name]

    @classmethod
    def register_store(cls, name: str, driver: CacheDriver) -> None:
        """Register a cache store."""
        cls._stores[name] = driver

    @classmethod
    def set_default_store(cls, name: str) -> None:
        """Set the default store."""
        cls._default_store = name

    @classmethod
    def get_default_store(cls) -> CacheDriver:
        """Get the default store."""
        if cls._default_store not in cls._stores:
            cls._stores["memory"] = MemoryDriver()
        return cls._stores[cls._default_store]

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from the cache."""
        value = cls.get_default_store().get(key)
        return value if value is not None else default

    @classmethod
    def put(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache."""
        return cls.get_default_store().put(key, value, ttl)

    @classmethod
    def forget(cls, key: str) -> bool:
        """Remove a value from the cache."""
        return cls.get_default_store().forget(key)

    @classmethod
    def flush(cls) -> bool:
        """Clear all values from the cache."""
        return cls.get_default_store().flush()

    @classmethod
    def has(cls, key: str) -> bool:
        """Check if a key exists."""
        return cls.get_default_store().has(key)

    @classmethod
    def get_many(cls, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values."""
        return cls.get_default_store().get_many(keys)

    @classmethod
    def put_many(cls, values: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store multiple values."""
        return cls.get_default_store().put_many(values, ttl)

    @classmethod
    def increment(cls, key: str, value: int = 1) -> int:
        """Increment a value."""
        return cls.get_default_store().increment(key, value)

    @classmethod
    def decrement(cls, key: str, value: int = 1) -> int:
        """Decrement a value."""
        return cls.get_default_store().decrement(key, value)

    @classmethod
    def remember(
        cls,
        key: str,
        ttl: Optional[int],
        callback: Callable[[], Any],
    ) -> Any:
        """Get or set a value."""
        return cls.get_default_store().remember(key, ttl, callback)

    @classmethod
    def forever(cls, key: str, value: Any) -> bool:
        """Store a value forever."""
        return cls.get_default_store().forever(key, value)

    @classmethod
    def tags(cls, tags: List[str]) -> TaggedCache:
        """Get a tagged cache instance."""
        return TaggedCache(cls.get_default_store(), tags)
