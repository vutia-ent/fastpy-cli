# Fastpy Libs

Laravel-style facades for common development tasks. Clean, expressive APIs for HTTP requests, email, caching, file storage, job queues, events, notifications, password hashing, and encryption.

## Overview

| Lib | Facade | Description |
|-----|--------|-------------|
| [Http](/guide/libs/http) | `Http` | HTTP client with fluent API |
| [Mail](/guide/libs/mail) | `Mail` | Email sending with templates |
| [Cache](/guide/libs/cache) | `Cache` | Data caching with multiple drivers |
| [Storage](/guide/libs/storage) | `Storage` | File storage (local, S3) |
| [Queue](/guide/libs/queue) | `Queue` | Background job processing |
| [Events](/guide/libs/events) | `Event` | Event dispatching and listeners |
| [Notifications](/guide/libs/notifications) | `Notify` | Multi-channel notifications |
| [Hash](/guide/libs/hash) | `Hash` | Password hashing |
| [Crypt](/guide/libs/crypt) | `Crypt` | Data encryption |

## Quick Start

```python
from fastpy_cli.libs import Http, Mail, Cache, Storage, Queue, Event, Notify, Hash, Crypt
```

## CLI Commands

```bash
# List all libs
fastpy libs

# View lib info
fastpy libs http

# Show usage examples
fastpy libs http --usage
```

## Common Patterns

### Http Requests

```python
from fastpy_cli.libs import Http

response = Http.get('https://api.example.com/users')
data = response.json()

Http.with_token('api-key').post('/api/data', json={'key': 'value'})
```

### Email

```python
from fastpy_cli.libs import Mail

Mail.to('user@example.com') \
    .subject('Welcome!') \
    .send('emails/welcome', {'name': 'John'})
```

### Caching

```python
from fastpy_cli.libs import Cache

Cache.put('key', 'value', ttl=3600)
value = Cache.get('key', default='fallback')
users = Cache.remember('users', lambda: fetch_users(), ttl=600)
```

### File Storage

```python
from fastpy_cli.libs import Storage

Storage.put('avatars/user.jpg', file_content)
url = Storage.url('avatars/user.jpg')
```

### Password Hashing

```python
from fastpy_cli.libs import Hash

hashed = Hash.make('password')
if Hash.check('password', hashed):
    print('Valid!')
```

### Encryption

```python
from fastpy_cli.libs import Crypt

Crypt.set_key(key)  # Or use APP_KEY env var
encrypted = Crypt.encrypt('sensitive data')
decrypted = Crypt.decrypt(encrypted)
```

## Dependencies

Some libs require additional packages:

| Lib | Dependencies |
|-----|--------------|
| Http | httpx |
| Hash | bcrypt |
| Crypt | cryptography |

Install with:

```bash
pip install httpx bcrypt cryptography
```
