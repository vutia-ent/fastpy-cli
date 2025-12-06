# Hash

Secure password hashing.

## Installation

```bash
pip install bcrypt
```

## Import

```python
from fastpy_cli.libs import Hash
```

## Basic Usage

```python
# Hash a password
hashed = Hash.make('secret-password')

# Verify a password
if Hash.check('secret-password', hashed):
    print('Password is correct!')
else:
    print('Invalid password')
```

## Rehashing

Check if a hash needs to be upgraded (e.g., after changing algorithm):

```python
if Hash.needs_rehash(hashed):
    new_hash = Hash.make('password')
    user.password = new_hash
    user.save()
```

## Algorithms

```python
# bcrypt (default)
hashed = Hash.make('password')

# Argon2 (recommended for new projects)
hashed = Hash.driver('argon2').make('password')

# PBKDF2-SHA256
hashed = Hash.driver('pbkdf2').make('password')
```

## Configuration

```python
# Configure bcrypt rounds
Hash.configure('bcrypt', {'rounds': 14})

# Configure Argon2
Hash.configure('argon2', {
    'time_cost': 3,
    'memory_cost': 65536,
    'parallelism': 4
})
```

## Algorithms Comparison

| Algorithm | Security | Speed | Notes |
|-----------|----------|-------|-------|
| bcrypt | High | Slow | Default, widely used |
| Argon2 | Highest | Configurable | Recommended, winner of PHC |
| PBKDF2 | High | Fast | NIST approved |

## Secure Defaults

- **bcrypt**: 13 rounds
- **Argon2**: time_cost=3, memory_cost=64MB
- **PBKDF2**: 600,000 iterations

## Best Practices

1. Never store plain-text passwords
2. Use Argon2 for new projects
3. Increase rounds/iterations over time
4. Rehash passwords on login when needed
