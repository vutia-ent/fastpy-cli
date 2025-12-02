"""
Event Dispatcher implementation.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
import threading


class EventDispatcher:
    """
    Event dispatcher for pub/sub pattern.
    """

    _listeners: Dict[str, List[Callable]] = {}
    _wildcards: List[tuple] = []
    _lock = threading.Lock()

    def __init__(self):
        pass

    @classmethod
    def listen(
        cls,
        event: Union[str, List[str]],
        listener: Optional[Callable] = None,
    ) -> Callable:
        """
        Register an event listener.

        Can be used as a decorator:
            @Event.listen('user.registered')
            def on_registered(data):
                ...

        Or directly:
            Event.listen('user.registered', on_registered)
        """
        events = [event] if isinstance(event, str) else event

        def decorator(func: Callable) -> Callable:
            for e in events:
                cls._add_listener(e, func)
            return func

        if listener is not None:
            for e in events:
                cls._add_listener(e, listener)
            return listener

        return decorator

    @classmethod
    def _add_listener(cls, event: str, listener: Callable) -> None:
        """Add a listener for an event."""
        with cls._lock:
            # Check for wildcard
            if "*" in event:
                cls._wildcards.append((event, listener))
            else:
                if event not in cls._listeners:
                    cls._listeners[event] = []
                cls._listeners[event].append(listener)

    @classmethod
    def has_listeners(cls, event: str) -> bool:
        """Check if an event has listeners."""
        if event in cls._listeners and cls._listeners[event]:
            return True

        # Check wildcards
        for pattern, _ in cls._wildcards:
            if cls._matches_wildcard(event, pattern):
                return True

        return False

    @classmethod
    def _matches_wildcard(cls, event: str, pattern: str) -> bool:
        """Check if an event matches a wildcard pattern."""
        import fnmatch
        return fnmatch.fnmatch(event, pattern)

    @classmethod
    def dispatch(
        cls,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        halt: bool = False,
    ) -> List[Any]:
        """
        Dispatch an event to all listeners.

        Args:
            event: Event name
            payload: Event data
            halt: Stop on first non-None response

        Returns:
            List of listener responses
        """
        payload = payload or {}
        responses = []

        # Get direct listeners
        listeners = cls._listeners.get(event, []).copy()

        # Add wildcard listeners
        for pattern, listener in cls._wildcards:
            if cls._matches_wildcard(event, pattern):
                listeners.append(listener)

        for listener in listeners:
            response = cls._call_listener(listener, event, payload)

            if response is not None:
                responses.append(response)

                if halt:
                    return responses

        return responses

    @classmethod
    def _call_listener(
        cls,
        listener: Callable,
        event: str,
        payload: Dict[str, Any],
    ) -> Any:
        """Call a listener with the event data."""
        # Check if it's a class with handle method
        if isinstance(listener, type):
            instance = listener()
            if hasattr(instance, "handle"):
                return instance.handle(payload)
        elif hasattr(listener, "handle"):
            return listener.handle(payload)
        else:
            return listener(payload)

    @classmethod
    def dispatch_async(
        cls,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Dispatch an event asynchronously via the queue.
        """
        from fastpy_cli.libs.queue import Queue

        return Queue.push({
            "type": "event",
            "event": event,
            "payload": payload or {},
        })

    @classmethod
    def subscribe(cls, subscriber: Union[Type, object]) -> None:
        """
        Register an event subscriber.

        The subscriber should have a `subscribe` method that receives
        the event dispatcher.
        """
        instance = subscriber() if isinstance(subscriber, type) else subscriber

        if hasattr(instance, "subscribe"):
            instance.subscribe(cls)

    @classmethod
    def forget(cls, event: str) -> None:
        """Remove all listeners for an event."""
        with cls._lock:
            if event in cls._listeners:
                del cls._listeners[event]

            # Remove matching wildcards
            cls._wildcards = [
                (p, l) for p, l in cls._wildcards
                if not cls._matches_wildcard(event, p)
            ]

    @classmethod
    def flush(cls) -> None:
        """Remove all listeners."""
        with cls._lock:
            cls._listeners.clear()
            cls._wildcards.clear()

    @classmethod
    def until(
        cls,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Dispatch event until first non-None response.
        """
        responses = cls.dispatch(event, payload, halt=True)
        return responses[0] if responses else None

    @classmethod
    def push(cls, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Push an event onto the queue without dispatching.
        Alias for dispatch_async.
        """
        cls.dispatch_async(event, payload)
