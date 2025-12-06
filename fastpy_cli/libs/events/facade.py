"""
Event Facade - Static interface to event dispatcher.
"""

from typing import Any, Callable, Optional, Union

from fastpy_cli.libs.events.dispatcher import EventDispatcher
from fastpy_cli.libs.support.container import container

# Register the event dispatcher in the container
container.singleton("events", lambda c: EventDispatcher())


class Event:
    """
    Event Facade providing static access to event dispatcher.

    Usage:
        # Listen to events
        @Event.listen('user.created')
        def on_user_created(data):
            print(f"User created: {data['name']}")

        # Dispatch events
        Event.dispatch('user.created', {'name': 'John', 'email': 'john@example.com'})

        # Wildcard listeners
        @Event.listen('user.*')
        def on_any_user_event(data):
            print(f"User event: {data}")
    """

    @staticmethod
    def _dispatcher() -> EventDispatcher:
        """Get the event dispatcher from container."""
        return container.make("events")

    @classmethod
    def listen(
        cls,
        event: Union[str, list[str]],
        listener: Optional[Callable] = None,
    ) -> Callable:
        """Register an event listener."""
        return cls._dispatcher().listen(event, listener)

    @classmethod
    def dispatch(
        cls,
        event: str,
        payload: Optional[dict[str, Any]] = None,
        halt: bool = False,
    ) -> list[Any]:
        """Dispatch an event."""
        return cls._dispatcher().dispatch(event, payload, halt)

    @classmethod
    def dispatch_async(
        cls,
        event: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> str:
        """Dispatch an event asynchronously."""
        return cls._dispatcher().dispatch_async(event, payload)

    @classmethod
    def subscribe(cls, subscriber: Union[type, object]) -> None:
        """Register an event subscriber."""
        cls._dispatcher().subscribe(subscriber)

    @classmethod
    def has_listeners(cls, event: str) -> bool:
        """Check if an event has listeners."""
        return cls._dispatcher().has_listeners(event)

    @classmethod
    def forget(cls, event: str) -> None:
        """Remove all listeners for an event."""
        cls._dispatcher().forget(event)

    @classmethod
    def flush(cls) -> None:
        """Remove all listeners."""
        cls._dispatcher().flush()

    @classmethod
    def until(
        cls,
        event: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Dispatch until first response."""
        return cls._dispatcher().until(event, payload)

    @classmethod
    def push(cls, event: str, payload: Optional[dict[str, Any]] = None) -> None:
        """Push an event to the queue."""
        cls._dispatcher().push(event, payload)

    # Testing utilities
    @classmethod
    def fake(cls) -> "EventFake":
        """
        Fake events for testing.

        Usage:
            Event.fake()
            # ... code that dispatches events ...
            Event.assert_dispatched('user.created')
        """
        fake = EventFake()
        container.instance("events", fake)
        return fake


class EventFake:
    """Fake event dispatcher for testing."""

    def __init__(self):
        self._dispatched: list[tuple] = []
        self._listeners: dict[str, list[Callable]] = {}

    def listen(
        self,
        event: Union[str, list[str]],
        listener: Optional[Callable] = None,
    ) -> Callable:
        events = [event] if isinstance(event, str) else event

        def decorator(func: Callable) -> Callable:
            for e in events:
                if e not in self._listeners:
                    self._listeners[e] = []
                self._listeners[e].append(func)
            return func

        if listener is not None:
            for e in events:
                if e not in self._listeners:
                    self._listeners[e] = []
                self._listeners[e].append(listener)
            return listener

        return decorator

    def dispatch(
        self,
        event: str,
        payload: Optional[dict[str, Any]] = None,
        halt: bool = False,
    ) -> list[Any]:
        self._dispatched.append((event, payload or {}))
        return []

    def dispatch_async(
        self,
        event: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> str:
        self._dispatched.append((event, payload or {}))
        return "fake-job-id"

    def subscribe(self, subscriber: Union[type, object]) -> None:
        pass

    def has_listeners(self, event: str) -> bool:
        return event in self._listeners

    def forget(self, event: str) -> None:
        if event in self._listeners:
            del self._listeners[event]

    def flush(self) -> None:
        self._listeners.clear()
        self._dispatched.clear()

    def until(self, event: str, payload: Optional[dict[str, Any]] = None) -> Any:
        self._dispatched.append((event, payload or {}))
        return None

    def push(self, event: str, payload: Optional[dict[str, Any]] = None) -> None:
        self.dispatch_async(event, payload)

    def assert_dispatched(self, event: str, count: Optional[int] = None) -> bool:
        """Assert an event was dispatched."""
        matching = [e for e, _ in self._dispatched if e == event]

        if count is not None and len(matching) != count:
            raise AssertionError(f"Expected {count} '{event}' events, got {len(matching)}")

        if not matching:
            raise AssertionError(f"Event '{event}' was not dispatched")

        return True

    def assert_not_dispatched(self, event: str) -> bool:
        """Assert an event was not dispatched."""
        matching = [e for e, _ in self._dispatched if e == event]

        if matching:
            raise AssertionError(f"Event '{event}' was dispatched {len(matching)} time(s)")

        return True

    def assert_dispatched_with(self, event: str, **kwargs) -> bool:
        """Assert an event was dispatched with specific data."""
        for e, payload in self._dispatched:
            if e == event and all(payload.get(k) == v for k, v in kwargs.items()):
                return True

        raise AssertionError(f"Event '{event}' was not dispatched with {kwargs}")

    @property
    def dispatched(self) -> list[tuple]:
        """Get all dispatched events."""
        return self._dispatched
