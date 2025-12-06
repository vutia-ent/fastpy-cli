"""
Notification Channels - Different delivery mechanisms.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class NotificationChannel(ABC):
    """Base class for notification channels."""

    @abstractmethod
    def send(self, notifiable: Any, notification: Any) -> bool:
        """Send a notification."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the channel name."""
        pass


class MailChannel(NotificationChannel):
    """Email notification channel."""

    def get_name(self) -> str:
        return "mail"

    def send(self, notifiable: Any, notification: Any) -> bool:
        """Send email notification."""
        from fastpy_cli.libs.mail import Mail

        data = notification.to_mail(notifiable)
        if not data:
            return False

        # Get recipient email
        email = self._get_recipient(notifiable)
        if not email:
            return False

        # Build and send email
        mail = Mail.to(email)

        if data.get("subject"):
            mail = mail.subject(data["subject"])

        if data.get("from_address"):
            mail = mail.from_address(data["from_address"], data.get("from_name"))

        if data.get("template"):
            return mail.send(data["template"], data.get("data", {}))
        elif data.get("html"):
            mail = mail.html(data["html"])
            if data.get("text"):
                mail = mail.text(data["text"])
            return mail.send()

        return False

    def _get_recipient(self, notifiable: Any) -> Optional[str]:
        """Get the recipient email."""
        if hasattr(notifiable, "route_notification_for_mail"):
            return notifiable.route_notification_for_mail()
        if hasattr(notifiable, "email"):
            return notifiable.email
        if isinstance(notifiable, dict):
            return notifiable.get("email")
        return None


class DatabaseChannel(NotificationChannel):
    """Database notification channel."""

    def get_name(self) -> str:
        return "database"

    def send(self, notifiable: Any, notification: Any) -> bool:
        """Store notification in database."""
        data = notification.to_database(notifiable) or notification.to_array(notifiable)

        # Get the notifiable ID
        notifiable_id = self._get_notifiable_id(notifiable)
        notifiable_type = type(notifiable).__name__

        # Store in database (this would use your ORM)
        # For now, we'll emit an event that can be handled
        from fastpy_cli.libs.events import Event

        Event.dispatch(
            "notification.stored",
            {
                "notifiable_id": notifiable_id,
                "notifiable_type": notifiable_type,
                "notification_type": data.get("type", notification.__class__.__name__),
                "data": data.get("data", data),
                "read_at": None,
            },
        )

        return True

    def _get_notifiable_id(self, notifiable: Any) -> Optional[Any]:
        """Get the notifiable ID."""
        if hasattr(notifiable, "id"):
            return notifiable.id
        if isinstance(notifiable, dict):
            return notifiable.get("id")
        return None


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def get_name(self) -> str:
        return "slack"

    def send(self, notifiable: Any, notification: Any) -> bool:
        """Send Slack notification."""
        from fastpy_cli.libs.http import Http

        data = notification.to_slack(notifiable)
        if not data:
            return False

        # Get webhook URL
        webhook_url = self._get_webhook_url(notifiable) or self.webhook_url
        if not webhook_url:
            return False

        # Build payload
        payload = {}

        if data.get("text"):
            payload["text"] = data["text"]

        if data.get("channel"):
            payload["channel"] = data["channel"]

        if data.get("username"):
            payload["username"] = data["username"]

        if data.get("icon_emoji"):
            payload["icon_emoji"] = data["icon_emoji"]

        if data.get("blocks"):
            payload["blocks"] = data["blocks"]

        if data.get("attachments"):
            payload["attachments"] = data["attachments"]

        # Send to Slack
        response = Http.post(webhook_url, json=payload)
        return response.ok

    def _get_webhook_url(self, notifiable: Any) -> Optional[str]:
        """Get the Slack webhook URL."""
        if hasattr(notifiable, "route_notification_for_slack"):
            return notifiable.route_notification_for_slack()
        if isinstance(notifiable, dict):
            return notifiable.get("slack_webhook_url")
        return None


class SMSChannel(NotificationChannel):
    """SMS notification channel."""

    def __init__(
        self,
        provider: str = "twilio",
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.provider = provider
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def get_name(self) -> str:
        return "sms"

    def send(self, notifiable: Any, notification: Any) -> bool:
        """Send SMS notification."""
        message = notification.to_sms(notifiable)
        if not message:
            return False

        # Get recipient phone
        phone = self._get_recipient(notifiable)
        if not phone:
            return False

        if self.provider == "twilio":
            return self._send_twilio(phone, message)
        elif self.provider == "nexmo":
            return self._send_nexmo(phone, message)

        return False

    def _get_recipient(self, notifiable: Any) -> Optional[str]:
        """Get the recipient phone number."""
        if hasattr(notifiable, "route_notification_for_sms"):
            return notifiable.route_notification_for_sms()
        if hasattr(notifiable, "phone"):
            return notifiable.phone
        if isinstance(notifiable, dict):
            return notifiable.get("phone")
        return None

    def _send_twilio(self, to: str, message: str) -> bool:
        """Send via Twilio."""
        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)
            client.messages.create(
                body=message,
                from_=self.from_number,
                to=to,
            )
            return True
        except ImportError:
            print("Twilio requires twilio package. Install with: pip install twilio")
            return False
        except Exception as e:
            print(f"Twilio error: {e}")
            return False

    def _send_nexmo(self, to: str, message: str) -> bool:
        """Send via Nexmo/Vonage."""
        from fastpy_cli.libs.http import Http

        response = Http.post(
            "https://rest.nexmo.com/sms/json",
            json={
                "api_key": self.account_sid,
                "api_secret": self.auth_token,
                "to": to,
                "from": self.from_number,
                "text": message,
            },
        )
        return response.ok
