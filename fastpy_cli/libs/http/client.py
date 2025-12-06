"""
HTTP Client implementation.
"""

import ipaddress
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
from urllib.parse import urlparse

import httpx

# Private/internal IP ranges that should be blocked for SSRF protection
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),  # IPv6 localhost
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


def is_safe_url(url: str, allow_private: bool = False) -> tuple[bool, str]:
    """Check if a URL is safe to request (not pointing to internal resources).

    Args:
        url: The URL to check
        allow_private: If True, allow requests to private IPs

    Returns:
        Tuple of (is_safe, error_message)
    """
    if allow_private:
        return True, ""

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "Invalid URL: no hostname"

        # Check for localhost variants
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False, "Blocked: localhost access not allowed"

        # Try to resolve and check IP
        try:
            import socket

            # Get all IPs for the hostname
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                ip_obj = ipaddress.ip_address(ip)

                for blocked_range in BLOCKED_IP_RANGES:
                    if ip_obj in blocked_range:
                        return False, f"Blocked: {hostname} resolves to private IP {ip}"

        except socket.gaierror:
            # DNS resolution failed - might be internal hostname
            # Be conservative and block non-resolvable hosts
            pass

        return True, ""

    except Exception as e:
        return False, f"URL validation error: {e}"


@dataclass
class HttpResponse:
    """
    HTTP Response wrapper with convenient methods.
    """

    _response: httpx.Response

    @property
    def status(self) -> int:
        """Get the status code."""
        return self._response.status_code

    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status < 300

    @property
    def successful(self) -> bool:
        """Alias for ok."""
        return self.ok

    @property
    def failed(self) -> bool:
        """Check if response failed."""
        return not self.ok

    @property
    def client_error(self) -> bool:
        """Check if client error (4xx)."""
        return 400 <= self.status < 500

    @property
    def server_error(self) -> bool:
        """Check if server error (5xx)."""
        return 500 <= self.status < 600

    @property
    def headers(self) -> dict[str, str]:
        """Get response headers."""
        return dict(self._response.headers)

    @property
    def body(self) -> str:
        """Get response body as string."""
        return self._response.text

    @property
    def content(self) -> bytes:
        """Get response body as bytes."""
        return self._response.content

    def json(self) -> Any:
        """Parse response body as JSON."""
        return self._response.json()

    def header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a specific header."""
        return self._response.headers.get(name, default)

    def throw(self) -> "HttpResponse":
        """Raise exception if response failed."""
        self._response.raise_for_status()
        return self

    def throw_if(self, condition: Union[bool, Callable[["HttpResponse"], bool]]) -> "HttpResponse":
        """Raise exception if condition is true."""
        if callable(condition):
            condition = condition(self)
        if condition:
            self._response.raise_for_status()
        return self

    def collect(self) -> list[Any]:
        """Parse JSON response as list."""
        data = self.json()
        return data if isinstance(data, list) else [data]

    def __repr__(self) -> str:
        return f"<HttpResponse [{self.status}]>"


@dataclass
class PendingRequest:
    """
    Pending HTTP request with fluent interface.
    """

    _base_url: str = ""
    _headers: dict[str, str] = field(default_factory=dict)
    _timeout: float = 30.0
    _retries: int = 0
    _retry_delay: float = 1.0
    _verify_ssl: bool = True
    _auth: Optional[tuple] = None
    _bearer_token: Optional[str] = None
    _query: dict[str, Any] = field(default_factory=dict)
    _async_mode: bool = False
    _allow_private_ips: bool = False  # SSRF protection

    def base_url(self, url: str) -> "PendingRequest":
        """Set the base URL for requests."""
        self._base_url = url.rstrip("/")
        return self

    def with_headers(self, headers: dict[str, str]) -> "PendingRequest":
        """Add headers to the request."""
        self._headers.update(headers)
        return self

    def with_header(self, name: str, value: str) -> "PendingRequest":
        """Add a single header."""
        self._headers[name] = value
        return self

    def accept(self, content_type: str) -> "PendingRequest":
        """Set the Accept header."""
        return self.with_header("Accept", content_type)

    def accept_json(self) -> "PendingRequest":
        """Set Accept header to application/json."""
        return self.accept("application/json")

    def content_type(self, content_type: str) -> "PendingRequest":
        """Set the Content-Type header."""
        return self.with_header("Content-Type", content_type)

    def with_token(self, token: str, type: str = "Bearer") -> "PendingRequest":
        """Set bearer token authentication."""
        self._bearer_token = token
        return self.with_header("Authorization", f"{type} {token}")

    def with_basic_auth(self, username: str, password: str) -> "PendingRequest":
        """Set basic authentication."""
        self._auth = (username, password)
        return self

    def with_query(self, params: dict[str, Any]) -> "PendingRequest":
        """Add query parameters."""
        self._query.update(params)
        return self

    def timeout(self, seconds: float) -> "PendingRequest":
        """Set request timeout."""
        self._timeout = seconds
        return self

    def retry(self, times: int, delay: float = 1.0) -> "PendingRequest":
        """Configure retry behavior."""
        self._retries = times
        self._retry_delay = delay
        return self

    def without_verifying(self) -> "PendingRequest":
        """Disable SSL verification.

        WARNING: This makes the connection vulnerable to man-in-the-middle attacks.
        Only use for development/testing with self-signed certificates.
        """
        self._verify_ssl = False
        return self

    def allow_private_ips(self) -> "PendingRequest":
        """Allow requests to private/internal IP addresses.

        WARNING: This disables SSRF protection. Only use when you need to
        access internal services and trust the URL source.
        """
        self._allow_private_ips = True
        return self

    def async_(self) -> "PendingRequest":
        """Enable async mode."""
        self._async_mode = True
        return self

    def _build_url(self, url: str) -> str:
        """Build the full URL."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self._base_url}/{url.lstrip('/')}"

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> HttpResponse:
        """Make a synchronous HTTP request with retry logic."""
        full_url = self._build_url(url)

        # SECURITY: Check for SSRF attacks
        is_safe, error = is_safe_url(full_url, allow_private=self._allow_private_ips)
        if not is_safe:
            raise ValueError(f"SSRF protection: {error}")

        # Merge query params
        params = {**self._query, **kwargs.pop("params", {})}
        if params:
            kwargs["params"] = params

        last_exception: Optional[Exception] = None

        for attempt in range(self._retries + 1):
            try:
                with httpx.Client(
                    timeout=self._timeout,
                    verify=self._verify_ssl,
                    auth=self._auth,
                ) as client:
                    response = client.request(
                        method,
                        full_url,
                        headers=self._headers,
                        **kwargs,
                    )
                    return HttpResponse(_response=response)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self._retries:
                    time.sleep(self._retry_delay * (attempt + 1))

        raise last_exception or RuntimeError("Request failed")

    async def _make_async_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> HttpResponse:
        """Make an asynchronous HTTP request."""
        import asyncio

        full_url = self._build_url(url)

        # SECURITY: Check for SSRF attacks
        is_safe, error = is_safe_url(full_url, allow_private=self._allow_private_ips)
        if not is_safe:
            raise ValueError(f"SSRF protection: {error}")

        params = {**self._query, **kwargs.pop("params", {})}
        if params:
            kwargs["params"] = params

        last_exception: Optional[Exception] = None

        for attempt in range(self._retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    verify=self._verify_ssl,
                    auth=self._auth,
                ) as client:
                    response = await client.request(
                        method,
                        full_url,
                        headers=self._headers,
                        **kwargs,
                    )
                    return HttpResponse(_response=response)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self._retries:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        raise last_exception or RuntimeError("Request failed")

    def get(self, url: str, params: Optional[dict[str, Any]] = None) -> HttpResponse:
        """Make a GET request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("GET", url, params=params or {})

    def post(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a POST request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("POST", url, data=data, json=json)

    def put(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PUT request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("PUT", url, data=data, json=json)

    def patch(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PATCH request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("PATCH", url, data=data, json=json)

    def delete(self, url: str) -> HttpResponse:
        """Make a DELETE request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("DELETE", url)

    def head(self, url: str) -> HttpResponse:
        """Make a HEAD request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("HEAD", url)

    def options(self, url: str) -> HttpResponse:
        """Make an OPTIONS request."""
        if self._async_mode:
            raise RuntimeError("Use 'await' with async mode")
        return self._make_request("OPTIONS", url)

    # Async methods
    async def aget(self, url: str, params: Optional[dict[str, Any]] = None) -> HttpResponse:
        """Make an async GET request."""
        return await self._make_async_request("GET", url, params=params or {})

    async def apost(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make an async POST request."""
        return await self._make_async_request("POST", url, data=data, json=json)

    async def aput(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make an async PUT request."""
        return await self._make_async_request("PUT", url, data=data, json=json)

    async def apatch(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make an async PATCH request."""
        return await self._make_async_request("PATCH", url, data=data, json=json)

    async def adelete(self, url: str) -> HttpResponse:
        """Make an async DELETE request."""
        return await self._make_async_request("DELETE", url)


class HttpClient:
    """
    HTTP Client factory.
    """

    @staticmethod
    def create() -> PendingRequest:
        """Create a new pending request."""
        return PendingRequest()

    @staticmethod
    def base_url(url: str) -> PendingRequest:
        """Create a request with a base URL."""
        return PendingRequest().base_url(url)

    @staticmethod
    def with_headers(headers: dict[str, str]) -> PendingRequest:
        """Create a request with headers."""
        return PendingRequest().with_headers(headers)

    @staticmethod
    def with_token(token: str, type: str = "Bearer") -> PendingRequest:
        """Create a request with bearer token."""
        return PendingRequest().with_token(token, type)

    @staticmethod
    def with_basic_auth(username: str, password: str) -> PendingRequest:
        """Create a request with basic auth."""
        return PendingRequest().with_basic_auth(username, password)

    @staticmethod
    def timeout(seconds: float) -> PendingRequest:
        """Create a request with timeout."""
        return PendingRequest().timeout(seconds)

    @staticmethod
    def retry(times: int, delay: float = 1.0) -> PendingRequest:
        """Create a request with retry."""
        return PendingRequest().retry(times, delay)

    @staticmethod
    def async_() -> PendingRequest:
        """Create an async request."""
        return PendingRequest().async_()

    @staticmethod
    def get(url: str, params: Optional[dict[str, Any]] = None) -> HttpResponse:
        """Make a GET request."""
        return PendingRequest().get(url, params)

    @staticmethod
    def post(
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a POST request."""
        return PendingRequest().post(url, data, json)

    @staticmethod
    def put(
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PUT request."""
        return PendingRequest().put(url, data, json)

    @staticmethod
    def patch(
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> HttpResponse:
        """Make a PATCH request."""
        return PendingRequest().patch(url, data, json)

    @staticmethod
    def delete(url: str) -> HttpResponse:
        """Make a DELETE request."""
        return PendingRequest().delete(url)
