"""
Notification Manager implementation.
"""

import uuid
from typing import Any, Optional, Union

from fastpy_cli.libs.notifications.channels import (
    DatabaseChannel,
    MailChannel,
    NotificationChannel,
)
from fastpy_cli.libs.notifications.notification import Notification


class AnonymousNotifiable:
    """
    Anonymous notifiable for on-demand notifications.

    Usage:
        Notify.route('mail', 'guest@example.com') \\
            .route('sms', '+1234567890') \\
            .notify(WelcomeNotification())
    """

    def __init__(self):
        self._routes: dict[str, Any] = {}

    def route(self, channel: str, route: Any) -> "AnonymousNotifiable":
        """Add a route for a channel."""
        self._routes[channel] = route
        return self

    def route_notification_for_mail(self) -> Optional[str]:
        return self._routes.get("mail")

    def route_notification_for_sms(self) -> Optional[str]:
        return self._routes.get("sms")

    def route_notification_for_slack(self) -> Optional[str]:
        return self._routes.get("slack")

    def route_notification_for_database(self) -> Optional[str]:
        return self._routes.get("database")

    def notify(self, notification: Notification) -> bool:
        """Send a notification to this anonymous notifiable."""
        return NotificationManager.send(self, notification)


class NotificationManager:
    """
    Notification manager for sending notifications through multiple channels.
    """

    _channels: dict[str, NotificationChannel] = {}

    def __init__(self):
        # Register default channels
        if "mail" not in self._channels:
            self._channels["mail"] = MailChannel()
        if "database" not in self._channels:
            self._channels["database"] = DatabaseChannel()

    @classmethod
    def channel(cls, name: str) -> NotificationChannel:
        """Get a notification channel."""
        if name not in cls._channels:
            raise ValueError(f"Notification channel '{name}' not registered")
        return cls._channels[name]

    @classmethod
    def register_channel(cls, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        cls._channels[name] = channel

    @classmethod
    def send(
        cls,
        notifiables: Union[Any, list[Any]],
        notification: Notification,
    ) -> bool:
        """
        Send a notification to one or more notifiables.

        Args:
            notifiables: Single notifiable or list of notifiables
            notification: The notification to send

        Returns:
            True if all notifications sent successfully
        """
        if not isinstance(notifiables, list):
            notifiables = [notifiables]

        # Generate notification ID
        notification.id = str(uuid.uuid4())

        all_success = True

        for notifiable in notifiables:
            # Get channels for this notification
            channels = notification.via(notifiable)

            for channel_name in channels:
                # Check if should send
                if not notification.should_send(notifiable, channel_name):
                    continue

                # Get the channel
                if channel_name not in cls._channels:
                    print(f"Warning: Channel '{channel_name}' not registered")
                    continue

                channel = cls._channels[channel_name]

                # Send notification
                try:
                    success = channel.send(notifiable, notification)
                    if not success:
                        all_success = False
                except Exception as e:
                    print(f"Error sending via {channel_name}: {e}")
                    all_success = False

        return all_success

    @classmethod
    def send_now(
        cls,
        notifiables: Union[Any, list[Any]],
        notification: Notification,
    ) -> bool:
        """Send a notification immediately (bypass queue)."""
        return cls.send(notifiables, notification)

    @classmethod
    def send_later(
        cls,
        delay: int,
        notifiables: Union[Any, list[Any]],
        notification: Notification,
    ) -> str:
        """Queue a notification to be sent after a delay."""
        from fastpy_cli.libs.queue import Queue

        notification.delay = delay

        return Queue.later(delay, {
            "type": "send_notification",
            "notification": notification,
            "notifiables": notifiables,
        })

    @classmethod
    def route(cls, channel: str, route: Any) -> AnonymousNotifiable:
        """
        Create an anonymous notifiable with a route.

        Usage:
            Notify.route('mail', 'guest@example.com').notify(notification)
        """
        return AnonymousNotifiable().route(channel, route)
