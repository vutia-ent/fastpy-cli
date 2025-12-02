"""
Events Facade - Laravel-style event system.

Usage:
    from fastpy_cli.libs import Event

    # Register listeners
    @Event.listen('user.registered')
    def send_welcome_email(event_data):
        Mail.to(event_data['email']).send('welcome')

    @Event.listen('user.registered')
    def log_registration(event_data):
        logger.info(f"User registered: {event_data['email']}")

    # Dispatch events
    Event.dispatch('user.registered', {'email': 'user@example.com', 'name': 'John'})

    # Class-based listeners
    class SendWelcomeEmail:
        def handle(self, event_data):
            Mail.to(event_data['email']).send('welcome')

    Event.listen('user.registered', SendWelcomeEmail)

    # Event subscribers
    class UserEventSubscriber:
        def subscribe(self, events):
            events.listen('user.registered', self.on_registered)
            events.listen('user.deleted', self.on_deleted)

        def on_registered(self, data): ...
        def on_deleted(self, data): ...

    Event.subscribe(UserEventSubscriber)

    # Async events (queued)
    Event.dispatch_async('order.shipped', {'order_id': 123})
"""

from fastpy_cli.libs.events.dispatcher import EventDispatcher
from fastpy_cli.libs.events.facade import Event

__all__ = ["Event", "EventDispatcher"]
