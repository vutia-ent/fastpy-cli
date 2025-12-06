# Http

HTTP client with a fluent, chainable API.

## Installation

```bash
pip install httpx
```

## Import

```python
from fastpy_cli.libs import Http
```

## Basic Requests

```python
# GET request
response = Http.get('https://api.example.com/users')
data = response.json()

# POST with JSON
response = Http.post('https://api.example.com/users', json={
    'name': 'John',
    'email': 'john@example.com'
})

# PUT
response = Http.put('https://api.example.com/users/1', json={'name': 'Jane'})

# PATCH
response = Http.patch('https://api.example.com/users/1', json={'name': 'Jane'})

# DELETE
response = Http.delete('https://api.example.com/users/1')
```

## Authentication

```python
# Bearer token
response = Http.with_token('your-api-token').get('/api/protected')

# Basic auth
response = Http.with_basic_auth('username', 'password').get('/api/auth')
```

## Headers

```python
response = Http.with_headers({
    'X-Custom-Header': 'value',
    'Accept': 'application/json'
}).get('https://api.example.com/data')
```

## Timeout and Retry

```python
response = Http.timeout(60) \
    .retry(3) \
    .get('https://api.slow.com/data')
```

## Async Requests

```python
response = await Http.async_().aget('https://api.example.com/data')
```

## Chaining

```python
response = Http.with_token('token') \
    .with_headers({'X-Custom': 'value'}) \
    .timeout(30) \
    .retry(3) \
    .post('https://api.example.com/data', json={'key': 'value'})
```

## Testing with Fakes

```python
# Set up fake responses
Http.fake({
    'https://api.example.com/*': {'status': 200, 'json': {'ok': True}}
})

# Make request (returns fake response)
response = Http.get('https://api.example.com/test')

# Assert requests were made
Http.assert_sent('https://api.example.com/test')
```

## Security

The Http client includes SSRF protection, blocking requests to private IP ranges by default.
