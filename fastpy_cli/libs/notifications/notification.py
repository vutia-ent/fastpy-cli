"""
Base Notification class.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Notification(ABC):
    """
    Base class for notifications.

    Subclass this to create custom notifications:

        class WelcomeNotification(Notification):
            def __init__(self, user):
                self.user = user

            def via(self, notifiable) -> list:
                return ['mail', 'database']

            def to_mail(self, notifiable):
                return {
                    'subject': 'Welcome!',
                    'template': 'welcome',
                    'data': {'name': self.user.name}
                }

            def to_database(self, notifiable):
                return {
                    'type': 'welcome',
                    'data': {'user_id': self.user.id}
                }
    """

    # Notification ID (set when sent)
    id: Optional[str] = None

    # Queue settings
    queue: Optional[str] = None
    delay: int = 0

    @abstractmethod
    def via(self, notifiable: Any) -> list[str]:
        """
        Get the notification's delivery channels.

        Args:
            notifiable: The entity being notified

        Returns:
            List of channel names (e.g., ['mail', 'database', 'slack'])
        """
        pass

    def to_mail(self, notifiable: Any) -> Optional[dict[str, Any]]:
        """
        Get the mail representation.

        Returns:
            Dict with keys: subject, template, data, from_address, etc.
        """
        return None

    def to_database(self, notifiable: Any) -> Optional[dict[str, Any]]:
        """
        Get the database representation.

        Returns:
            Dict with keys: type, data
        """
        return None

    def to_slack(self, notifiable: Any) -> Optional[dict[str, Any]]:
        """
        Get the Slack representation.

        Returns:
            Dict with keys: text, channel, username, icon_emoji, blocks, etc.
        """
        return None

    def to_sms(self, notifiable: Any) -> Optional[str]:
        """
        Get the SMS representation.

        Returns:
            SMS message text
        """
        return None

    def to_broadcast(self, notifiable: Any) -> Optional[dict[str, Any]]:
        """
        Get the broadcast (WebSocket) representation.

        Returns:
            Dict with event data
        """
        return None

    def to_array(self, notifiable: Any) -> dict[str, Any]:
        """
        Get the array representation.

        Default implementation for database storage.
        """
        return {
            "type": self.__class__.__name__,
            "data": self.__dict__.copy(),
        }

    def should_send(self, notifiable: Any, channel: str) -> bool:
        """
        Determine if the notification should be sent.

        Override to add conditions.
        """
        return True

    def on_queue(self, queue: str) -> "Notification":
        """Set the queue for this notification."""
        self.queue = queue
        return self

    def with_delay(self, seconds: int) -> "Notification":
        """Set the delay for this notification."""
        self.delay = seconds
        return self
