# Crypt

Data encryption.

## Installation

```bash
pip install cryptography
```

## Import

```python
from fastpy_cli.libs import Crypt
```

## Generate Key

Generate a key once and save to `.env`:

```python
key = Crypt.generate_key()
print(key)  # Add to .env as APP_KEY=<key>
```

## Set Key

```python
# Set manually
Crypt.set_key(key)

# Or use APP_KEY environment variable (automatic)
```

## Encrypt/Decrypt Strings

```python
encrypted = Crypt.encrypt('sensitive data')
decrypted = Crypt.decrypt(encrypted)
```

## Encrypt Complex Data

Data is automatically JSON serialized:

```python
encrypted = Crypt.encrypt({
    'user_id': 123,
    'session_token': 'abc123',
    'expires_at': '2024-12-31'
})

data = Crypt.decrypt(encrypted)  # Returns dict
```

## Algorithms

```python
# Fernet (default - AES-128-CBC with HMAC)
encrypted = Crypt.encrypt('secret')

# AES-256-CBC
encrypted = Crypt.driver('aes').encrypt('secret')
```

## Algorithms Comparison

| Algorithm | Key Size | Description |
|-----------|----------|-------------|
| Fernet | 128-bit | AES-128-CBC + HMAC, recommended |
| AES-256-CBC | 256-bit | Standard AES encryption |

## Use Cases

```python
# Encrypt API tokens
encrypted_token = Crypt.encrypt(api_token)
# Store encrypted_token in database

# Decrypt when needed
api_token = Crypt.decrypt(encrypted_token)

# Encrypt sensitive user data
encrypted_ssn = Crypt.encrypt(user.ssn)
```

## Security Notes

1. Never commit encryption keys to version control
2. Use environment variables for keys
3. Rotate keys periodically
4. Encrypted data is base64 encoded

## Configuration

Add to `.env`:

```ini
APP_KEY=your-generated-key-here
```
