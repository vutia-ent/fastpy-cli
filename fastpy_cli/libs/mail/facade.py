"""
Mail Facade - Static interface to mailer.
"""

from typing import Any, Callable, Optional, Union

from fastpy_cli.libs.mail.drivers import (
    MailDriver,
    MailgunDriver,
    SendGridDriver,
    SESDriver,
    SMTPDriver,
)
from fastpy_cli.libs.mail.mailer import Mailer, PendingMail
from fastpy_cli.libs.support.container import container


# Factory function for creating the mailer
def _create_mailer(c) -> Mailer:
    """Create and configure the mailer from config."""
    mailer = Mailer()

    # Try to get configuration
    try:
        from fastpy_cli.libs.support.config import config

        # SMTP configuration
        if config.has("mail.smtp.host"):
            smtp = SMTPDriver(
                host=config.get("mail.smtp.host", "localhost"),
                port=config.get("mail.smtp.port", 587),
                username=config.get("mail.smtp.username"),
                password=config.get("mail.smtp.password"),
                use_tls=config.get("mail.smtp.tls", True),
            )
            mailer.register_driver("smtp", smtp)

        # SendGrid configuration
        if config.has("mail.sendgrid.api_key"):
            sendgrid = SendGridDriver(
                api_key=config.get("mail.sendgrid.api_key"),
            )
            mailer.register_driver("sendgrid", sendgrid)

        # Mailgun configuration
        if config.has("mail.mailgun.api_key"):
            mailgun = MailgunDriver(
                api_key=config.get("mail.mailgun.api_key"),
                domain=config.get("mail.mailgun.domain"),
                region=config.get("mail.mailgun.region", "us"),
            )
            mailer.register_driver("mailgun", mailgun)

        # AWS SES configuration
        if config.has("mail.ses.access_key"):
            ses = SESDriver(
                access_key=config.get("mail.ses.access_key"),
                secret_key=config.get("mail.ses.secret_key"),
                region=config.get("mail.ses.region", "us-east-1"),
            )
            mailer.register_driver("ses", ses)

        # Set default driver
        default_driver = config.get("mail.driver", "log")
        mailer.set_default_driver(default_driver)

        # Set default from
        if config.has("mail.from.address"):
            mailer.set_default_from(
                config.get("mail.from.address"),
                config.get("mail.from.name"),
            )

    except Exception:
        pass  # Use defaults

    return mailer


# Register the mailer in the container
container.singleton("mail", _create_mailer)


class Mail:
    """
    Mail Facade providing static access to mailer.

    Usage:
        # Simple email
        Mail.to('user@example.com').send('welcome', {'name': 'John'})

        # With options
        Mail.to('user@example.com') \\
            .subject('Welcome!') \\
            .from_address('noreply@app.com', 'My App') \\
            .send('welcome', {'name': 'John'})

        # Multiple recipients
        Mail.to(['user1@example.com', 'user2@example.com']) \\
            .cc('manager@example.com') \\
            .send('newsletter')

        # Queue for background sending
        Mail.to('user@example.com').queue('welcome', {'name': 'John'})
    """

    @staticmethod
    def _mailer() -> Mailer:
        """Get the mailer from container."""
        return container.make("mail")

    @classmethod
    def to(cls, addresses: Union[str, list[str]]) -> PendingMail:
        """Create a pending mail with recipient(s)."""
        return cls._mailer().to(addresses)

    @classmethod
    def raw(cls) -> PendingMail:
        """Create a raw pending mail."""
        return cls._mailer().raw()

    @classmethod
    def using(cls, driver: str) -> PendingMail:
        """Use a specific mail driver."""
        return cls._mailer().using(driver)

    @classmethod
    def driver(cls, name: str) -> MailDriver:
        """Get a specific driver."""
        return cls._mailer().driver(name)

    @classmethod
    def register_driver(cls, name: str, driver: MailDriver) -> None:
        """Register a mail driver."""
        cls._mailer().register_driver(name, driver)

    @classmethod
    def set_default_driver(cls, name: str) -> None:
        """Set the default driver."""
        cls._mailer().set_default_driver(name)

    @classmethod
    def set_default_from(cls, email: str, name: Optional[str] = None) -> None:
        """Set the default from address."""
        cls._mailer().set_default_from(email, name)

    @classmethod
    def set_template_renderer(
        cls,
        renderer: Callable[[str, dict[str, Any]], str],
    ) -> None:
        """Set a custom template renderer."""
        cls._mailer().set_template_renderer(renderer)

    # Testing utilities
    @classmethod
    def fake(cls) -> "MailFake":
        """
        Fake mail sending for testing.

        Usage:
            Mail.fake()
            # ... code that sends mail ...
            Mail.assert_sent('welcome')
        """
        fake = MailFake()
        container.instance("mail", fake)
        return fake


class MailFake:
    """
    Fake mailer for testing.
    """

    def __init__(self):
        self._sent: list[dict[str, Any]] = []
        self._queued: list[dict[str, Any]] = []

    def to(self, addresses: Union[str, list[str]]) -> "FakePendingMail":
        """Create a fake pending mail."""
        return FakePendingMail(self, addresses)

    def raw(self) -> "FakePendingMail":
        return FakePendingMail(self, [])

    def using(self, driver: str) -> "FakePendingMail":
        return FakePendingMail(self, [])

    def record_sent(self, mail_data: dict[str, Any]) -> None:
        """Record a sent email."""
        self._sent.append(mail_data)

    def record_queued(self, mail_data: dict[str, Any]) -> None:
        """Record a queued email."""
        self._queued.append(mail_data)

    def assert_sent(self, template: Optional[str] = None, count: Optional[int] = None) -> bool:
        """Assert emails were sent."""
        matching = self._sent
        if template:
            matching = [m for m in matching if m.get("template") == template]

        if count is not None and len(matching) != count:
            raise AssertionError(
                f"Expected {count} emails to be sent, but {len(matching)} were sent"
            )

        if not matching:
            raise AssertionError("No emails were sent")

        return True

    def assert_not_sent(self, template: Optional[str] = None) -> bool:
        """Assert no emails were sent."""
        matching = self._sent
        if template:
            matching = [m for m in matching if m.get("template") == template]

        if matching:
            raise AssertionError(f"Expected no emails, but {len(matching)} were sent")

        return True

    def assert_queued(self, template: Optional[str] = None) -> bool:
        """Assert emails were queued."""
        matching = self._queued
        if template:
            matching = [m for m in matching if m.get("template") == template]

        if not matching:
            raise AssertionError("No emails were queued")

        return True

    @property
    def sent(self) -> list[dict[str, Any]]:
        """Get sent emails."""
        return self._sent

    @property
    def queued(self) -> list[dict[str, Any]]:
        """Get queued emails."""
        return self._queued


class FakePendingMail:
    """Fake pending mail for testing."""

    def __init__(self, fake: MailFake, to: Union[str, list[str]]):
        self._fake = fake
        self._data = {
            "to": [to] if isinstance(to, str) else to,
            "cc": [],
            "bcc": [],
        }

    def to(self, addresses: Union[str, list[str]]) -> "FakePendingMail":
        self._data["to"] = [addresses] if isinstance(addresses, str) else addresses
        return self

    def cc(self, addresses: Union[str, list[str]]) -> "FakePendingMail":
        if isinstance(addresses, str):
            self._data["cc"].append(addresses)
        else:
            self._data["cc"].extend(addresses)
        return self

    def bcc(self, addresses: Union[str, list[str]]) -> "FakePendingMail":
        if isinstance(addresses, str):
            self._data["bcc"].append(addresses)
        else:
            self._data["bcc"].extend(addresses)
        return self

    def from_address(self, email: str, name: Optional[str] = None) -> "FakePendingMail":
        self._data["from_address"] = email
        self._data["from_name"] = name
        return self

    def subject(self, subject: str) -> "FakePendingMail":
        self._data["subject"] = subject
        return self

    def html(self, content: str) -> "FakePendingMail":
        self._data["html"] = content
        return self

    def text(self, content: str) -> "FakePendingMail":
        self._data["text"] = content
        return self

    def view(self, template: str, data: Optional[dict[str, Any]] = None) -> "FakePendingMail":
        self._data["template"] = template
        self._data["template_data"] = data
        return self

    def attach(self, *args, **kwargs) -> "FakePendingMail":
        return self

    def attach_data(self, *args, **kwargs) -> "FakePendingMail":
        return self

    def send(self, template: Optional[str] = None, data: Optional[dict[str, Any]] = None) -> bool:
        if template:
            self._data["template"] = template
            self._data["template_data"] = data
        self._fake.record_sent(self._data)
        return True

    def queue(self, template: Optional[str] = None, data: Optional[dict[str, Any]] = None) -> bool:
        if template:
            self._data["template"] = template
            self._data["template_data"] = data
        self._fake.record_queued(self._data)
        return True

    def later(
        self, delay: int, template: Optional[str] = None, data: Optional[dict[str, Any]] = None
    ) -> bool:
        return self.queue(template, data)
