"""
Mailer implementation with fluent interface.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Union

from fastpy_cli.libs.mail.drivers import LogDriver, MailDriver, MailMessage


@dataclass
class PendingMail:
    """
    Pending email with fluent interface.
    """

    _driver: MailDriver
    _to: list[str] = field(default_factory=list)
    _cc: list[str] = field(default_factory=list)
    _bcc: list[str] = field(default_factory=list)
    _from_address: Optional[str] = None
    _from_name: Optional[str] = None
    _reply_to: Optional[str] = None
    _subject: str = ""
    _html: Optional[str] = None
    _text: Optional[str] = None
    _attachments: list[dict[str, Any]] = field(default_factory=list)
    _headers: dict[str, str] = field(default_factory=dict)
    _template_renderer: Optional[Callable[[str, dict[str, Any]], str]] = None

    def to(self, addresses: Union[str, list[str]]) -> "PendingMail":
        """Set recipient(s)."""
        if isinstance(addresses, str):
            self._to = [addresses]
        else:
            self._to = addresses
        return self

    def cc(self, addresses: Union[str, list[str]]) -> "PendingMail":
        """Add CC recipient(s)."""
        if isinstance(addresses, str):
            self._cc.append(addresses)
        else:
            self._cc.extend(addresses)
        return self

    def bcc(self, addresses: Union[str, list[str]]) -> "PendingMail":
        """Add BCC recipient(s)."""
        if isinstance(addresses, str):
            self._bcc.append(addresses)
        else:
            self._bcc.extend(addresses)
        return self

    def from_address(self, email: str, name: Optional[str] = None) -> "PendingMail":
        """Set the sender address."""
        self._from_address = email
        self._from_name = name
        return self

    def reply_to(self, email: str) -> "PendingMail":
        """Set the reply-to address."""
        self._reply_to = email
        return self

    def subject(self, subject: str) -> "PendingMail":
        """Set the email subject."""
        self._subject = subject
        return self

    def html(self, content: str) -> "PendingMail":
        """Set the HTML body."""
        self._html = content
        return self

    def text(self, content: str) -> "PendingMail":
        """Set the plain text body."""
        self._text = content
        return self

    def view(self, template: str, data: Optional[dict[str, Any]] = None) -> "PendingMail":
        """Render a template for the email body."""
        if self._template_renderer:
            self._html = self._template_renderer(template, data or {})
        else:
            # Default: try to load from templates directory
            self._html = self._render_template(template, data or {})
        return self

    def _render_template(self, template: str, data: dict[str, Any]) -> str:
        """Render a template using Jinja2 if available."""
        try:
            from jinja2 import Environment, FileSystemLoader

            templates_dir = Path.cwd() / "templates" / "emails"
            if templates_dir.exists():
                env = Environment(loader=FileSystemLoader(str(templates_dir)))
                tpl = env.get_template(f"{template}.html")
                return tpl.render(**data)
        except ImportError:
            pass

        # Fallback: simple string formatting
        template_path = Path.cwd() / "templates" / "emails" / f"{template}.html"
        if template_path.exists():
            content = template_path.read_text()
            for key, value in data.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))
            return content

        raise ValueError(f"Template '{template}' not found")

    def attach(
        self,
        path: Union[str, Path],
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> "PendingMail":
        """Attach a file."""
        path = Path(path)
        content = path.read_bytes()

        self._attachments.append(
            {
                "content": content,
                "filename": filename or path.name,
                "mime_type": mime_type,
            }
        )
        return self

    def attach_data(
        self,
        data: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> "PendingMail":
        """Attach data as a file."""
        self._attachments.append(
            {
                "content": data,
                "filename": filename,
                "mime_type": mime_type,
            }
        )
        return self

    def with_header(self, name: str, value: str) -> "PendingMail":
        """Add a custom header."""
        self._headers[name] = value
        return self

    def priority(self, level: int = 1) -> "PendingMail":
        """Set email priority (1=high, 3=normal, 5=low)."""
        self._headers["X-Priority"] = str(level)
        return self

    def high_priority(self) -> "PendingMail":
        """Mark as high priority."""
        return self.priority(1)

    def low_priority(self) -> "PendingMail":
        """Mark as low priority."""
        return self.priority(5)

    def send(
        self,
        template: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Send the email.

        Args:
            template: Optional template name to render
            data: Optional data for template rendering
        """
        if template:
            self.view(template, data)

        message = MailMessage(
            to=self._to,
            subject=self._subject,
            html=self._html,
            text=self._text,
            from_address=self._from_address,
            from_name=self._from_name,
            cc=self._cc if self._cc else None,
            bcc=self._bcc if self._bcc else None,
            reply_to=self._reply_to,
            attachments=self._attachments if self._attachments else None,
            headers=self._headers if self._headers else None,
        )

        return self._driver.send(message)

    def queue(
        self,
        template: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Queue the email for background sending."""
        # This would integrate with the Queue system
        from fastpy_cli.libs.queue import Queue

        return Queue.push(
            {
                "type": "send_mail",
                "mail": {
                    "to": self._to,
                    "cc": self._cc,
                    "bcc": self._bcc,
                    "from_address": self._from_address,
                    "from_name": self._from_name,
                    "subject": self._subject,
                    "template": template,
                    "data": data,
                    "html": self._html,
                    "text": self._text,
                },
            }
        )

    def later(
        self,
        delay_seconds: int,
        template: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Queue the email to be sent after a delay."""
        from fastpy_cli.libs.queue import Queue

        return Queue.later(
            delay_seconds,
            {
                "type": "send_mail",
                "mail": {
                    "to": self._to,
                    "cc": self._cc,
                    "bcc": self._bcc,
                    "from_address": self._from_address,
                    "from_name": self._from_name,
                    "subject": self._subject,
                    "template": template,
                    "data": data,
                    "html": self._html,
                    "text": self._text,
                },
            },
        )


class Mailer:
    """
    Mail manager supporting multiple drivers.
    """

    _drivers: dict[str, MailDriver] = {}
    _default_driver: str = "log"
    _default_from: Optional[tuple] = None
    _template_renderer: Optional[Callable[[str, dict[str, Any]], str]] = None

    def __init__(self):
        # Register default log driver
        if "log" not in self._drivers:
            self._drivers["log"] = LogDriver()

    @classmethod
    def driver(cls, name: str) -> MailDriver:
        """Get a specific driver."""
        if name not in cls._drivers:
            raise ValueError(f"Mail driver '{name}' not registered")
        return cls._drivers[name]

    @classmethod
    def register_driver(cls, name: str, driver: MailDriver) -> None:
        """Register a mail driver."""
        cls._drivers[name] = driver

    @classmethod
    def set_default_driver(cls, name: str) -> None:
        """Set the default driver."""
        cls._default_driver = name

    @classmethod
    def set_default_from(cls, email: str, name: Optional[str] = None) -> None:
        """Set the default from address."""
        cls._default_from = (email, name)

    @classmethod
    def set_template_renderer(
        cls,
        renderer: Callable[[str, dict[str, Any]], str],
    ) -> None:
        """Set a custom template renderer."""
        cls._template_renderer = renderer

    @classmethod
    def get_default_driver(cls) -> MailDriver:
        """Get the default driver."""
        if cls._default_driver not in cls._drivers:
            cls._drivers["log"] = LogDriver()
        return cls._drivers[cls._default_driver]

    @classmethod
    def to(cls, addresses: Union[str, list[str]]) -> PendingMail:
        """Create a pending mail with recipient(s)."""
        pending = PendingMail(
            _driver=cls.get_default_driver(),
            _template_renderer=cls._template_renderer,
        )

        if cls._default_from:
            pending.from_address(cls._default_from[0], cls._default_from[1])

        return pending.to(addresses)

    @classmethod
    def raw(cls) -> PendingMail:
        """Create a raw pending mail."""
        pending = PendingMail(
            _driver=cls.get_default_driver(),
            _template_renderer=cls._template_renderer,
        )

        if cls._default_from:
            pending.from_address(cls._default_from[0], cls._default_from[1])

        return pending

    @classmethod
    def using(cls, driver_name: str) -> PendingMail:
        """Create a pending mail using a specific driver."""
        return PendingMail(
            _driver=cls.driver(driver_name),
            _template_renderer=cls._template_renderer,
        )
