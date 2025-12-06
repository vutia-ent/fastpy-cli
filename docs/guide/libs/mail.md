# Mail

Send emails with multiple driver support.

## Import

```python
from fastpy_cli.libs import Mail
```

## Basic Usage

```python
# Send with template
Mail.to('user@example.com') \
    .subject('Welcome to Our App!') \
    .send('emails/welcome', {'name': 'John'})
```

## Multiple Recipients

```python
Mail.to(['user1@example.com', 'user2@example.com']) \
    .cc('manager@example.com') \
    .bcc('archive@example.com') \
    .subject('Team Update') \
    .send('emails/update', {'message': 'Hello team!'})
```

## Raw HTML/Text

```python
Mail.to('user@example.com') \
    .subject('Hello') \
    .html('<h1>Hello World</h1>') \
    .text('Hello World') \
    .send()
```

## Attachments

```python
Mail.to('user@example.com') \
    .subject('Your Invoice') \
    .attach('/path/to/invoice.pdf') \
    .send('emails/invoice', {'invoice': invoice})
```

## From Address

```python
Mail.from_('noreply@example.com', 'My App') \
    .to('user@example.com') \
    .subject('Hello') \
    .send('template', data)
```

## Using Specific Driver

```python
# SendGrid
Mail.driver('sendgrid').to('user@example.com').send('template', data)

# Mailgun
Mail.driver('mailgun').to('user@example.com').send('template', data)

# AWS SES
Mail.driver('ses').to('user@example.com').send('template', data)
```

## Drivers

| Driver | Description |
|--------|-------------|
| `smtp` | Standard SMTP |
| `sendgrid` | SendGrid API |
| `mailgun` | Mailgun API |
| `ses` | AWS Simple Email Service |
| `log` | Log emails (development) |

## Configuration

Configure drivers in your `.env`:

```ini
# SMTP
MAIL_DRIVER=smtp
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
MAIL_FROM_ADDRESS=noreply@example.com
MAIL_FROM_NAME=MyApp

# SendGrid
SENDGRID_API_KEY=your-key

# Mailgun
MAILGUN_API_KEY=your-key
MAILGUN_DOMAIN=your-domain

# AWS SES
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```
