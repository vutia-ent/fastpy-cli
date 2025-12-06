"""
Mail Drivers - Different email transport implementations.
"""

import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional


@dataclass
class MailMessage:
    """Email message data."""

    to: list[str]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    from_address: Optional[str] = None
    from_name: Optional[str] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[list[dict[str, Any]]] = None
    headers: Optional[dict[str, str]] = None


class MailDriver(ABC):
    """Base class for mail drivers."""

    @abstractmethod
    def send(self, message: MailMessage) -> bool:
        """Send an email message."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the driver name."""
        pass


class SMTPDriver(MailDriver):
    """SMTP mail driver."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: int = 30,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout

    def get_name(self) -> str:
        return "smtp"

    def send(self, message: MailMessage) -> bool:
        """Send email via SMTP."""
        msg = self._build_message(message)

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.host, self.port, context=context, timeout=self.timeout
                )
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

            with server:
                if self.use_tls and not self.use_ssl:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                all_recipients = message.to + (message.cc or []) + (message.bcc or [])
                server.sendmail(
                    message.from_address or self.username or "",
                    all_recipients,
                    msg.as_string(),
                )

            return True

        except Exception as e:
            print(f"SMTP Error: {e}")
            return False

    def _build_message(self, message: MailMessage) -> MIMEMultipart:
        """Build the MIME message."""
        msg = MIMEMultipart("alternative")

        # Headers
        msg["Subject"] = message.subject
        msg["To"] = ", ".join(message.to)

        if message.from_name and message.from_address:
            msg["From"] = f"{message.from_name} <{message.from_address}>"
        elif message.from_address:
            msg["From"] = message.from_address

        if message.cc:
            msg["Cc"] = ", ".join(message.cc)

        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        # Custom headers
        if message.headers:
            for key, value in message.headers.items():
                msg[key] = value

        # Body
        if message.text:
            msg.attach(MIMEText(message.text, "plain", "utf-8"))

        if message.html:
            msg.attach(MIMEText(message.html, "html", "utf-8"))

        # Attachments
        if message.attachments:
            for attachment in message.attachments:
                part = MIMEApplication(
                    attachment["content"],
                    Name=attachment["filename"],
                )
                part["Content-Disposition"] = f'attachment; filename="{attachment["filename"]}"'
                if attachment.get("mime_type"):
                    part["Content-Type"] = attachment["mime_type"]
                msg.attach(part)

        return msg


class SendGridDriver(MailDriver):
    """SendGrid mail driver."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.sendgrid.com/v3/mail/send"

    def get_name(self) -> str:
        return "sendgrid"

    def send(self, message: MailMessage) -> bool:
        """Send email via SendGrid API."""
        import httpx

        payload = {
            "personalizations": [
                {
                    "to": [{"email": email} for email in message.to],
                }
            ],
            "from": {
                "email": message.from_address,
                "name": message.from_name,
            },
            "subject": message.subject,
            "content": [],
        }

        if message.cc:
            payload["personalizations"][0]["cc"] = [{"email": e} for e in message.cc]

        if message.bcc:
            payload["personalizations"][0]["bcc"] = [{"email": e} for e in message.bcc]

        if message.text:
            payload["content"].append({"type": "text/plain", "value": message.text})

        if message.html:
            payload["content"].append({"type": "text/html", "value": message.html})

        if message.reply_to:
            payload["reply_to"] = {"email": message.reply_to}

        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0,
            )
            return response.status_code in (200, 202)

        except Exception as e:
            print(f"SendGrid Error: {e}")
            return False


class MailgunDriver(MailDriver):
    """Mailgun mail driver."""

    def __init__(self, api_key: str, domain: str, region: str = "us"):
        self.api_key = api_key
        self.domain = domain
        self.region = region

        if region == "eu":
            self.api_url = f"https://api.eu.mailgun.net/v3/{domain}/messages"
        else:
            self.api_url = f"https://api.mailgun.net/v3/{domain}/messages"

    def get_name(self) -> str:
        return "mailgun"

    def send(self, message: MailMessage) -> bool:
        """Send email via Mailgun API."""
        import httpx

        data = {
            "from": f"{message.from_name} <{message.from_address}>" if message.from_name else message.from_address,
            "to": message.to,
            "subject": message.subject,
        }

        if message.cc:
            data["cc"] = message.cc

        if message.bcc:
            data["bcc"] = message.bcc

        if message.text:
            data["text"] = message.text

        if message.html:
            data["html"] = message.html

        if message.reply_to:
            data["h:Reply-To"] = message.reply_to

        try:
            response = httpx.post(
                self.api_url,
                auth=("api", self.api_key),
                data=data,
                timeout=30.0,
            )
            return response.status_code == 200

        except Exception as e:
            print(f"Mailgun Error: {e}")
            return False


class SESDriver(MailDriver):
    """AWS SES mail driver."""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

    def get_name(self) -> str:
        return "ses"

    def send(self, message: MailMessage) -> bool:
        """Send email via AWS SES."""
        try:
            import boto3

            client = boto3.client(
                "ses",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )

            body = {}
            if message.text:
                body["Text"] = {"Data": message.text, "Charset": "UTF-8"}
            if message.html:
                body["Html"] = {"Data": message.html, "Charset": "UTF-8"}

            response = client.send_email(
                Source=f"{message.from_name} <{message.from_address}>" if message.from_name else message.from_address,
                Destination={
                    "ToAddresses": message.to,
                    "CcAddresses": message.cc or [],
                    "BccAddresses": message.bcc or [],
                },
                Message={
                    "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                    "Body": body,
                },
            )

            return response["ResponseMetadata"]["HTTPStatusCode"] == 200

        except ImportError:
            print("AWS SES requires boto3. Install with: pip install boto3")
            return False
        except Exception as e:
            print(f"SES Error: {e}")
            return False


class LogDriver(MailDriver):
    """Log driver for development/testing - logs emails instead of sending."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file

    def get_name(self) -> str:
        return "log"

    def send(self, message: MailMessage) -> bool:
        """Log the email instead of sending."""
        import json
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "to": message.to,
            "cc": message.cc,
            "bcc": message.bcc,
            "from": f"{message.from_name} <{message.from_address}>",
            "subject": message.subject,
            "text": message.text[:200] + "..." if message.text and len(message.text) > 200 else message.text,
            "html": message.html[:200] + "..." if message.html and len(message.html) > 200 else message.html,
            "attachments": len(message.attachments) if message.attachments else 0,
        }

        log_line = f"[MAIL] {json.dumps(log_entry, indent=2)}"

        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(log_line + "\n")
        else:
            print(log_line)

        return True
