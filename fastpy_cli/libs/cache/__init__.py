"""
Cache Facade - Laravel-style caching.

Usage:
    from fastpy_cli.libs import Cache

    # Basic operations
    Cache.put('key', 'value', ttl=3600)  # Store for 1 hour
    value = Cache.get('key')
    value = Cache.get('key', default='fallback')

    # Check and delete
    if Cache.has('key'):
        Cache.forget('key')

    # Remember pattern (get or set)
    user = Cache.remember('user:1', 3600, lambda: User.find(1))

    # Forever (no expiration)
    Cache.forever('settings', settings_dict)

    # Increment/Decrement
    Cache.increment('visits')
    Cache.decrement('stock', 5)

    # Tags for grouped invalidation
    Cache.tags(['users', 'profiles']).put('user:1', user)
    Cache.tags(['users']).flush()

    # Multiple operations
    Cache.put_many({'key1': 'val1', 'key2': 'val2'})
    values = Cache.get_many(['key1', 'key2'])
"""

from fastpy_cli.libs.cache.manager import CacheManager
from fastpy_cli.libs.cache.facade import Cache
from fastpy_cli.libs.cache.drivers import (
    CacheDriver,
    MemoryDriver,
    FileDriver,
    RedisDriver,
)

__all__ = [
    "Cache",
    "CacheManager",
    "CacheDriver",
    "MemoryDriver",
    "FileDriver",
    "RedisDriver",
]
