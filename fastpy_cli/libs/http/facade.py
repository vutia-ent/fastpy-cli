"""
HTTP Facade - Static interface to HTTP client.
"""

from typing import Any, Optional

from fastpy_cli.libs.http.client import HttpClient, HttpResponse, PendingRequest
from fastpy_cli.libs.support.container import container

# Register the HTTP client in the container
container.singleton("http", lambda c: HttpClient())


class Http:
    """
    HTTP Facade providing static access to HTTP client.

    Usage:
        # Simple requests
        response = Http.get('https://api.example.com/users')
        response = Http.post('https://api.example.com/users', json={'name': 'John'})

        # With fluent configuration
        response = Http.with_token('api_key').get('https://api.example.com/data')
        response = Http.timeout(60).retry(3).get('https://api.slow.com/data')

        # Base URL for API clients
        api = Http.base_url('https://api.example.com')
        users = api.get('/users')
        user = api.get('/users/1')
    """

    @staticmethod
    def _client() -> HttpClient:
        """Get the HTTP client from container."""
        return container.make("http")

    @classmethod
    def create(cls) -> PendingRequest:
        """Create a new pending request."""
        return cls._client().create()

    @classmethod
    def base_url(cls, url: str) -> PendingRequest:
        """Create a request with a base URL."""
        return cls._client().base_url(url)

    @classmethod
    def with_headers(cls, headers: dict[str, str]) -> PendingRequest:
        """Create a request with headers."""
        return cls._client().with_headers(headers)

    @classmethod
    def with_header(cls, name: str, value: str) -> PendingRequest:
        """Create a request with a single header."""
        return PendingRequest().with_header(name, value)

    @classmethod
    def with_token(cls, token: str, type: str = "Bearer") -> PendingRequest:
        """Create a request with bearer token."""
        return cls._client().with_token(token, type)

    @classmethod
    def with_basic_auth(cls, username: str, password: str) -> PendingRequest:
        """Create a request with basic auth."""
        return cls._client().with_basic_auth(username, password)

    @classmethod
    def accept_json(cls) -> PendingRequest:
        """Create a request that accepts JSON."""
        return PendingRequest().accept_json()

    @classmethod
    def content_type(cls, content_type: str) -> PendingRequest:
        """Create a request with content type."""
        return PendingRequest().content_type(content_type)

    @classmethod
    def timeout(cls, seconds: float) -> PendingRequest:
        """Create a request with timeout."""
        return cls._client().timeout(seconds)

    @classmethod
    def retry(cls, times: int, delay: float = 1.0) -> PendingRequest:
        """Create a request with retry."""
        return cls._client().retry(times, delay)

    @classmethod
    def without_verifying(cls) -> PendingRequest:
        """Create a request without SSL verification."""
        return PendingRequest().without_verifying()

    @classmethod
    def async_(cls) -> PendingRequest:
        """Create an async request."""
        return cls._client().async_()

    @classmethod
    def get(cls, url: str, params: Optional[dict[str, Any]] = None) -> HttpResponse:
        """Make a GET request."""
        return cls._client().get(url, params)

    @classmethod
    def post(
        cls,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a POST request."""
        return cls._client().post(url, data, json)

    @classmethod
    def put(
        cls,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PUT request."""
        return cls._client().put(url, data, json)

    @classmethod
    def patch(
        cls,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PATCH request."""
        return cls._client().patch(url, data, json)

    @classmethod
    def delete(cls, url: str) -> HttpResponse:
        """Make a DELETE request."""
        return cls._client().delete(url)

    @classmethod
    def head(cls, url: str) -> HttpResponse:
        """Make a HEAD request."""
        return PendingRequest().head(url)

    @classmethod
    def options(cls, url: str) -> HttpResponse:
        """Make an OPTIONS request."""
        return PendingRequest().options(url)

    # Testing utilities
    @classmethod
    def fake(cls, responses: Optional[dict[str, Any]] = None) -> "HttpFake":
        """
        Fake HTTP requests for testing.

        Usage:
            Http.fake({
                'https://api.example.com/users': {'users': []},
                'https://api.example.com/users/*': {'id': 1, 'name': 'John'},
            })
        """
        fake = HttpFake(responses or {})
        container.instance("http", fake)
        return fake


class HttpFake:
    """
    Fake HTTP client for testing.
    """

    def __init__(self, responses: dict[str, Any]):
        self._responses = responses
        self._recorded: list = []

    def get(self, url: str, **kwargs) -> "FakeResponse":
        self._recorded.append(("GET", url, kwargs))
        return self._find_response(url)

    def post(self, url: str, **kwargs) -> "FakeResponse":
        self._recorded.append(("POST", url, kwargs))
        return self._find_response(url)

    def put(self, url: str, **kwargs) -> "FakeResponse":
        self._recorded.append(("PUT", url, kwargs))
        return self._find_response(url)

    def patch(self, url: str, **kwargs) -> "FakeResponse":
        self._recorded.append(("PATCH", url, kwargs))
        return self._find_response(url)

    def delete(self, url: str, **kwargs) -> "FakeResponse":
        self._recorded.append(("DELETE", url, kwargs))
        return self._find_response(url)

    def _find_response(self, url: str) -> "FakeResponse":
        # Exact match
        if url in self._responses:
            return FakeResponse(self._responses[url])

        # Wildcard match
        for pattern, response in self._responses.items():
            if "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(url, pattern):
                    return FakeResponse(response)

        return FakeResponse(None, status=404)

    def assert_sent(self, method: str, url: str) -> bool:
        """Assert that a request was sent."""
        for m, u, _ in self._recorded:
            if m == method and u == url:
                return True
        raise AssertionError(f"No {method} request to {url} was recorded")

    def assert_not_sent(self, method: str, url: str) -> bool:
        """Assert that a request was not sent."""
        for m, u, _ in self._recorded:
            if m == method and u == url:
                raise AssertionError(f"A {method} request to {url} was recorded")
        return True

    @property
    def recorded(self) -> list:
        """Get recorded requests."""
        return self._recorded


class FakeResponse:
    """Fake HTTP response."""

    def __init__(self, data: Any, status: int = 200):
        self._data = data
        self._status = status

    @property
    def status(self) -> int:
        return self._status

    @property
    def ok(self) -> bool:
        return 200 <= self._status < 300

    def json(self) -> Any:
        return self._data

    @property
    def body(self) -> str:
        import json
        return json.dumps(self._data) if self._data else ""
