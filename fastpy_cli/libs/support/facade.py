"""
Facade Pattern - Static proxy to underlying services.

Inspired by Laravel's Facade pattern.
"""

from typing import Any, Optional, Type, TypeVar
from fastpy_cli.libs.support.container import Container, container

T = TypeVar("T")


class Facade:
    """
    Base Facade class.

    Facades provide a static interface to classes that are available in the container.

    Usage:
        class Http(Facade):
            @classmethod
            def get_facade_accessor(cls) -> str:
                return 'http'

        # Now you can use:
        Http.get('https://api.example.com')

        # Which proxies to:
        container.make('http').get('https://api.example.com')
    """

    _resolved_instance: Optional[Any] = None

    @classmethod
    def get_facade_accessor(cls) -> str:
        """
        Get the registered name of the component in the container.

        Override this in subclasses.
        """
        raise NotImplementedError(
            f"{cls.__name__} does not implement get_facade_accessor method."
        )

    @classmethod
    def get_facade_root(cls) -> Any:
        """Get the root object behind the facade."""
        accessor = cls.get_facade_accessor()

        if cls._resolved_instance is not None:
            return cls._resolved_instance

        if container.bound(accessor):
            cls._resolved_instance = container.make(accessor)
            return cls._resolved_instance

        raise RuntimeError(
            f"A facade root has not been set for '{accessor}'. "
            f"Make sure to bind it in the container."
        )

    @classmethod
    def swap(cls, instance: Any) -> None:
        """Swap the underlying instance (useful for testing)."""
        cls._resolved_instance = instance
        container.instance(cls.get_facade_accessor(), instance)

    @classmethod
    def clear_resolved_instance(cls) -> None:
        """Clear the resolved instance."""
        cls._resolved_instance = None

    @classmethod
    def get_container(cls) -> Container:
        """Get the container instance."""
        return container

    def __class_getitem__(cls, item: Type[T]) -> Type[T]:
        """Support for generic type hints."""
        return item

    @classmethod
    def __getattr__(cls, name: str) -> Any:
        """Proxy attribute access to the facade root."""
        instance = cls.get_facade_root()
        return getattr(instance, name)


class FacadeManager:
    """
    Manages facade resolution and testing utilities.
    """

    _facades: dict[str, Type[Facade]] = {}

    @classmethod
    def register(cls, name: str, facade: Type[Facade]) -> None:
        """Register a facade."""
        cls._facades[name] = facade

    @classmethod
    def clear_resolved_instances(cls) -> None:
        """Clear all resolved facade instances."""
        for facade in cls._facades.values():
            facade.clear_resolved_instance()

    @classmethod
    def fake(cls, facade: Type[Facade], fake_instance: Any) -> Any:
        """
        Replace a facade with a fake for testing.

        Usage:
            fake_http = FacadeManager.fake(Http, MockHttpClient())
        """
        facade.swap(fake_instance)
        return fake_instance
