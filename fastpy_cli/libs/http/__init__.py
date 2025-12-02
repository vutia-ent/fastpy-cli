"""
HTTP Client Facade - Laravel-style HTTP client.

Usage:
    from fastpy_cli.libs import Http

    # Simple GET request
    response = Http.get('https://api.example.com/users')

    # POST with JSON
    response = Http.post('https://api.example.com/users', json={
        'name': 'John',
        'email': 'john@example.com'
    })

    # With headers
    response = Http.with_headers({
        'Authorization': 'Bearer token123'
    }).get('https://api.example.com/profile')

    # With authentication
    response = Http.with_token('api_token').get('https://api.example.com/data')
    response = Http.with_basic_auth('user', 'pass').get('https://api.example.com/data')

    # Timeout and retries
    response = Http.timeout(30).retry(3, delay=1).get('https://api.example.com/slow')

    # Async support
    response = await Http.async_().get('https://api.example.com/users')

    # Response handling
    if response.ok:
        data = response.json()
    else:
        print(f"Error: {response.status}")
"""

from fastpy_cli.libs.http.client import HttpClient, HttpResponse, PendingRequest
from fastpy_cli.libs.http.facade import Http

__all__ = ["Http", "HttpClient", "HttpResponse", "PendingRequest"]
