"""
Notification Facade - Static interface to notification manager.
"""

from typing import Any, List, Optional, Union

from fastpy_cli.libs.notifications.notification import Notification
from fastpy_cli.libs.notifications.manager import NotificationManager, AnonymousNotifiable
from fastpy_cli.libs.notifications.channels import NotificationChannel
from fastpy_cli.libs.support.container import container


# Register the notification manager in the container
container.singleton("notifications", lambda c: NotificationManager())


class Notify:
    """
    Notification Facade providing static access to notification manager.

    Usage:
        # Send to a user
        Notify.send(user, OrderShippedNotification(order))

        # Send to multiple users
        Notify.send(users, OrderShippedNotification(order))

        # On-demand notification
        Notify.route('mail', 'guest@example.com').notify(WelcomeNotification())

        # Send later
        Notify.later(60, user, ReminderNotification())
    """

    @staticmethod
    def _manager() -> NotificationManager:
        """Get the notification manager from container."""
        return container.make("notifications")

    @classmethod
    def send(
        cls,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> bool:
        """Send a notification."""
        return cls._manager().send(notifiables, notification)

    @classmethod
    def send_now(
        cls,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> bool:
        """Send a notification immediately."""
        return cls._manager().send_now(notifiables, notification)

    @classmethod
    def later(
        cls,
        delay: int,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> str:
        """Queue a notification to be sent later."""
        return cls._manager().send_later(delay, notifiables, notification)

    @classmethod
    def route(cls, channel: str, route: Any) -> AnonymousNotifiable:
        """Create an anonymous notifiable with a route."""
        return cls._manager().route(channel, route)

    @classmethod
    def channel(cls, name: str) -> NotificationChannel:
        """Get a notification channel."""
        return cls._manager().channel(name)

    @classmethod
    def register_channel(cls, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        cls._manager().register_channel(name, channel)

    # Testing utilities
    @classmethod
    def fake(cls) -> "NotificationFake":
        """
        Fake notifications for testing.

        Usage:
            Notify.fake()
            Notify.send(user, OrderShippedNotification(order))
            Notify.assert_sent_to(user, OrderShippedNotification)
        """
        fake = NotificationFake()
        container.instance("notifications", fake)
        return fake


class NotificationFake:
    """Fake notification manager for testing."""

    def __init__(self):
        self._sent: List[tuple] = []

    def send(
        self,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> bool:
        if not isinstance(notifiables, list):
            notifiables = [notifiables]

        for notifiable in notifiables:
            self._sent.append((notifiable, notification))

        return True

    def send_now(
        self,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> bool:
        return self.send(notifiables, notification)

    def send_later(
        self,
        delay: int,
        notifiables: Union[Any, List[Any]],
        notification: Notification,
    ) -> str:
        self.send(notifiables, notification)
        return "fake-job-id"

    def route(self, channel: str, route: Any) -> AnonymousNotifiable:
        return AnonymousNotifiable().route(channel, route)

    def assert_sent_to(
        self,
        notifiable: Any,
        notification_class: type,
        count: Optional[int] = None,
    ) -> bool:
        """Assert a notification was sent to a notifiable."""
        matching = [
            (n, notif) for n, notif in self._sent
            if n == notifiable and isinstance(notif, notification_class)
        ]

        if count is not None and len(matching) != count:
            raise AssertionError(
                f"Expected {count} {notification_class.__name__} to {notifiable}, "
                f"got {len(matching)}"
            )

        if not matching:
            raise AssertionError(
                f"No {notification_class.__name__} was sent to {notifiable}"
            )

        return True

    def assert_not_sent_to(
        self,
        notifiable: Any,
        notification_class: type,
    ) -> bool:
        """Assert a notification was not sent to a notifiable."""
        matching = [
            (n, notif) for n, notif in self._sent
            if n == notifiable and isinstance(notif, notification_class)
        ]

        if matching:
            raise AssertionError(
                f"{notification_class.__name__} was sent to {notifiable}"
            )

        return True

    def assert_nothing_sent(self) -> bool:
        """Assert no notifications were sent."""
        if self._sent:
            raise AssertionError(f"{len(self._sent)} notifications were sent")
        return True

    def assert_count(self, count: int) -> bool:
        """Assert the total number of notifications sent."""
        if len(self._sent) != count:
            raise AssertionError(
                f"Expected {count} notifications, got {len(self._sent)}"
            )
        return True

    @property
    def sent(self) -> List[tuple]:
        """Get all sent notifications."""
        return self._sent
