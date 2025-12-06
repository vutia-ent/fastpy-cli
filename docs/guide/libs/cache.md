# Cache

Data caching with multiple backend support.

## Import

```python
from fastpy_cli.libs import Cache
```

## Basic Operations

```python
# Store value (1 hour TTL)
Cache.put('key', 'value', ttl=3600)

# Get value
value = Cache.get('key', default='fallback')

# Check existence
if Cache.has('key'):
    print('Cached!')

# Delete
Cache.forget('key')

# Clear all
Cache.flush()
```

## Remember Pattern

Get from cache or compute and store:

```python
# Fetch users from cache, or compute if not cached
users = Cache.remember('all_users', lambda: User.all(), ttl=600)

# Forever (no expiration)
config = Cache.remember_forever('app_config', lambda: load_config())
```

## Increment/Decrement

```python
Cache.increment('page_views')
Cache.increment('page_views', 5)  # Increment by 5

Cache.decrement('available_seats')
Cache.decrement('available_seats', 2)  # Decrement by 2
```

## Tagged Cache

Group related items for bulk operations:

```python
# Store with tags
Cache.tags(['users', 'permissions']).put('user:1:roles', roles)
Cache.tags(['users']).put('user:1:profile', profile)

# Flush all user-related cache
Cache.tags(['users']).flush()
```

## Using Specific Store

```python
# Redis
Cache.store('redis').put('key', 'value')

# File
Cache.store('file').put('key', 'value')

# Memory
Cache.store('memory').put('key', 'value')
```

## Drivers

| Driver | Description |
|--------|-------------|
| `memory` | In-memory (default, not persistent) |
| `file` | File-based storage |
| `redis` | Redis server |

## Configuration

```ini
# Redis
CACHE_DRIVER=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# File
CACHE_DRIVER=file
CACHE_PATH=./storage/cache
```
