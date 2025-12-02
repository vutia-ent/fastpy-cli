"""
Cache Drivers - Different cache backend implementations.
"""

import hashlib
import json
import os
import pickle
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import threading


class CacheDriver(ABC):
    """Base class for cache drivers."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get a value from the cache."""
        pass

    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache."""
        pass

    @abstractmethod
    def forget(self, key: str) -> bool:
        """Remove a value from the cache."""
        pass

    @abstractmethod
    def flush(self) -> bool:
        """Clear all values from the cache."""
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache."""
        return {key: self.get(key) for key in keys}

    def put_many(self, values: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store multiple values in the cache."""
        for key, value in values.items():
            if not self.put(key, value, ttl):
                return False
        return True

    def forget_many(self, keys: List[str]) -> bool:
        """Remove multiple values from the cache."""
        for key in keys:
            self.forget(key)
        return True

    def increment(self, key: str, value: int = 1) -> int:
        """Increment a value."""
        current = self.get(key) or 0
        new_value = current + value
        self.put(key, new_value)
        return new_value

    def decrement(self, key: str, value: int = 1) -> int:
        """Decrement a value."""
        return self.increment(key, -value)

    def remember(
        self,
        key: str,
        ttl: Optional[int],
        callback: Callable[[], Any],
    ) -> Any:
        """Get or set a value."""
        value = self.get(key)
        if value is not None:
            return value

        value = callback()
        self.put(key, value, ttl)
        return value

    def forever(self, key: str, value: Any) -> bool:
        """Store a value forever."""
        return self.put(key, value, ttl=None)


class MemoryDriver(CacheDriver):
    """In-memory cache driver."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                return None

            value, expires_at = self._cache[key]

            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None

            return value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            expires_at = time.time() + ttl if ttl else None
            self._cache[key] = (value, expires_at)
            return True

    def forget(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def flush(self) -> bool:
        with self._lock:
            self._cache.clear()
            return True

    def has(self, key: str) -> bool:
        return self.get(key) is not None


class FileDriver(CacheDriver):
    """File-based cache driver."""

    def __init__(self, path: str = ".cache"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        """Get the file path for a key."""
        hashed = hashlib.sha256(key.encode()).hexdigest()
        return self.path / f"{hashed}.cache"

    def get(self, key: str) -> Any:
        path = self._key_path(key)

        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            expires_at = data.get("expires_at")
            if expires_at is not None and time.time() > expires_at:
                path.unlink()
                return None

            return data["value"]

        except Exception:
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        path = self._key_path(key)

        try:
            data = {
                "value": value,
                "expires_at": time.time() + ttl if ttl else None,
            }

            with open(path, "wb") as f:
                pickle.dump(data, f)

            return True

        except Exception:
            return False

    def forget(self, key: str) -> bool:
        path = self._key_path(key)

        if path.exists():
            path.unlink()
            return True

        return False

    def flush(self) -> bool:
        for file in self.path.glob("*.cache"):
            file.unlink()
        return True

    def has(self, key: str) -> bool:
        return self.get(key) is not None


class RedisDriver(CacheDriver):
    """Redis cache driver."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "fastpy:cache:",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._client = None

    def _get_client(self):
        """Get Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                )
            except ImportError:
                raise ImportError(
                    "Redis driver requires redis package. Install with: pip install redis"
                )
        return self._client

    def _prefixed(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any:
        client = self._get_client()
        data = client.get(self._prefixed(key))

        if data is None:
            return None

        return pickle.loads(data)

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        client = self._get_client()
        data = pickle.dumps(value)

        if ttl:
            client.setex(self._prefixed(key), ttl, data)
        else:
            client.set(self._prefixed(key), data)

        return True

    def forget(self, key: str) -> bool:
        client = self._get_client()
        return client.delete(self._prefixed(key)) > 0

    def flush(self) -> bool:
        client = self._get_client()
        keys = client.keys(f"{self.prefix}*")
        if keys:
            client.delete(*keys)
        return True

    def has(self, key: str) -> bool:
        client = self._get_client()
        return client.exists(self._prefixed(key)) > 0

    def increment(self, key: str, value: int = 1) -> int:
        client = self._get_client()
        return client.incrby(self._prefixed(key), value)

    def decrement(self, key: str, value: int = 1) -> int:
        client = self._get_client()
        return client.decrby(self._prefixed(key), value)

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        client = self._get_client()
        prefixed_keys = [self._prefixed(k) for k in keys]
        values = client.mget(prefixed_keys)

        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                result[key] = pickle.loads(value)
            else:
                result[key] = None

        return result
