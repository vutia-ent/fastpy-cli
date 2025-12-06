# Notifications

Multi-channel notifications.

## Import

```python
from fastpy_cli.libs import Notify, Notification
```

## Defining Notifications

```python
class OrderShipped(Notification):
    def __init__(self, order):
        self.order = order

    def via(self, notifiable) -> list:
        """Channels to send through."""
        return ['mail', 'database', 'slack']

    def to_mail(self, notifiable) -> dict:
        """Email representation."""
        return {
            'subject': 'Your order has shipped!',
            'template': 'emails/order-shipped',
            'data': {'order': self.order, 'user': notifiable}
        }

    def to_database(self, notifiable) -> dict:
        """Database representation."""
        return {
            'type': 'order_shipped',
            'data': {'order_id': self.order.id}
        }

    def to_slack(self, notifiable) -> dict:
        """Slack representation."""
        return {
            'text': f'Order #{self.order.id} has been shipped!',
            'channel': '#orders'
        }
```

## Sending Notifications

```python
# Send to single user
Notify.send(user, OrderShipped(order))

# Send to multiple users
Notify.send(users, OrderShipped(order))
```

## On-Demand Notifications

Send without a user model:

```python
Notify.route('mail', 'guest@example.com') \
    .route('slack', '#general') \
    .notify(OrderShipped(order))
```

## Channels

| Channel | Description |
|---------|-------------|
| `mail` | Email |
| `database` | Store in database |
| `slack` | Slack webhook |
| `sms` | SMS (Twilio/Nexmo) |

## Channel Methods

```python
class MyNotification(Notification):
    def to_mail(self, notifiable) -> dict:
        return {'subject': '...', 'template': '...', 'data': {...}}

    def to_database(self, notifiable) -> dict:
        return {'type': '...', 'data': {...}}

    def to_slack(self, notifiable) -> dict:
        return {'text': '...', 'channel': '#...'}

    def to_sms(self, notifiable) -> str:
        return 'Your message here'
```

## Conditional Channels

```python
def via(self, notifiable) -> list:
    channels = ['database']

    if notifiable.email_notifications:
        channels.append('mail')

    if notifiable.slack_webhook:
        channels.append('slack')

    return channels
```

## Configuration

```ini
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Twilio
TWILIO_SID=your-sid
TWILIO_TOKEN=your-token
TWILIO_FROM=+1234567890
```
