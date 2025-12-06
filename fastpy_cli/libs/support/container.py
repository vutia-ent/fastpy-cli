"""
Service Container - Dependency injection container for Fastpy.

Inspired by Laravel's IoC container.
"""

import threading
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")


class Container:
    """
    Service container for dependency injection.

    Usage:
        container = Container()

        # Bind a class
        container.bind('mailer', SMTPMailer)

        # Bind a singleton
        container.singleton('cache', RedisCache)

        # Bind with factory
        container.bind('http', lambda c: HttpClient(timeout=c.make('config').get('http.timeout')))

        # Resolve
        mailer = container.make('mailer')
    """

    _instance: Optional["Container"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "Container":
        """Singleton pattern for global container."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._bindings: dict[str, dict[str, Any]] = {}
                    cls._instance._instances: dict[str, Any] = {}
                    cls._instance._aliases: dict[str, str] = {}
        return cls._instance

    def bind(
        self,
        abstract: str,
        concrete: Union[type[T], Callable[["Container"], T]],
        shared: bool = False,
    ) -> "Container":
        """
        Bind a class or factory to the container.

        Args:
            abstract: The abstract name/interface
            concrete: The concrete implementation or factory
            shared: Whether to share the instance (singleton)
        """
        self._bindings[abstract] = {
            "concrete": concrete,
            "shared": shared,
        }
        return self

    def singleton(
        self,
        abstract: str,
        concrete: Union[type[T], Callable[["Container"], T]],
    ) -> "Container":
        """Bind a singleton to the container."""
        return self.bind(abstract, concrete, shared=True)

    def instance(self, abstract: str, instance: Any) -> "Container":
        """Bind an existing instance to the container."""
        self._instances[abstract] = instance
        return self

    def alias(self, abstract: str, alias: str) -> "Container":
        """Create an alias for an abstract."""
        self._aliases[alias] = abstract
        return self

    def make(self, abstract: str, parameters: Optional[dict[str, Any]] = None) -> Any:
        """
        Resolve an abstract from the container.

        Args:
            abstract: The abstract name to resolve
            parameters: Optional parameters to pass to the constructor
        """
        # Resolve alias
        abstract = self._aliases.get(abstract, abstract)

        # Check for existing instance
        if abstract in self._instances:
            return self._instances[abstract]

        # Check for binding
        if abstract not in self._bindings:
            raise KeyError(f"No binding found for '{abstract}'")

        binding = self._bindings[abstract]
        concrete = binding["concrete"]

        # Build the instance
        if callable(concrete) and not isinstance(concrete, type):
            # Factory function
            instance = concrete(self)
        else:
            # Class
            instance = concrete(**(parameters or {}))

        # Store singleton
        if binding["shared"]:
            self._instances[abstract] = instance

        return instance

    def bound(self, abstract: str) -> bool:
        """Check if an abstract is bound."""
        abstract = self._aliases.get(abstract, abstract)
        return abstract in self._bindings or abstract in self._instances

    def forget(self, abstract: str) -> "Container":
        """Remove a binding from the container."""
        abstract = self._aliases.get(abstract, abstract)
        self._bindings.pop(abstract, None)
        self._instances.pop(abstract, None)
        return self

    def flush(self) -> "Container":
        """Clear all bindings and instances."""
        self._bindings.clear()
        self._instances.clear()
        self._aliases.clear()
        return self

    @classmethod
    def get_instance(cls) -> "Container":
        """Get the global container instance."""
        return cls()

    def __getitem__(self, abstract: str) -> Any:
        """Dictionary-style access."""
        return self.make(abstract)

    def __contains__(self, abstract: str) -> bool:
        """Check if abstract is bound."""
        return self.bound(abstract)


# Global container instance
container = Container()
