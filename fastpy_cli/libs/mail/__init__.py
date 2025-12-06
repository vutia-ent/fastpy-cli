"""
Mail Facade - Laravel-style email sending.

Usage:
    from fastpy_cli.libs import Mail

    # Simple email
    Mail.to('user@example.com').send('welcome', {'name': 'John'})

    # With subject and from
    Mail.to('user@example.com') \\
        .subject('Welcome to Our App!') \\
        .from_address('noreply@app.com', 'My App') \\
        .send('welcome', {'name': 'John'})

    # Multiple recipients
    Mail.to(['user1@example.com', 'user2@example.com']) \\
        .cc('manager@example.com') \\
        .bcc('archive@example.com') \\
        .send('newsletter', {'content': 'Hello!'})

    # With attachments
    Mail.to('user@example.com') \\
        .attach('/path/to/file.pdf') \\
        .attach_data(pdf_bytes, 'report.pdf', 'application/pdf') \\
        .send('invoice', {'invoice': invoice})

    # Raw email
    Mail.to('user@example.com') \\
        .subject('Hello!') \\
        .html('<h1>Hello World</h1>') \\
        .text('Hello World') \\
        .send()

    # Queue email for background sending
    Mail.to('user@example.com').queue('welcome', {'name': 'John'})

    # Send later
    Mail.to('user@example.com').later(60, 'reminder', {'task': 'Complete signup'})
"""

from fastpy_cli.libs.mail.drivers import (
    LogDriver,
    MailDriver,
    MailgunDriver,
    SendGridDriver,
    SESDriver,
    SMTPDriver,
)
from fastpy_cli.libs.mail.facade import Mail
from fastpy_cli.libs.mail.mailer import Mailer, PendingMail

__all__ = [
    "Mail",
    "Mailer",
    "PendingMail",
    "MailDriver",
    "SMTPDriver",
    "SendGridDriver",
    "MailgunDriver",
    "SESDriver",
    "LogDriver",
]
