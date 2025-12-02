"""
Notifications Facade - Laravel-style multi-channel notifications.

Usage:
    from fastpy_cli.libs import Notify, Notification

    # Define a notification
    class OrderShippedNotification(Notification):
        def __init__(self, order):
            self.order = order

        def via(self, notifiable) -> list:
            return ['mail', 'database', 'slack']

        def to_mail(self, notifiable):
            return {
                'subject': 'Your order has shipped!',
                'template': 'order_shipped',
                'data': {'order': self.order}
            }

        def to_database(self, notifiable):
            return {
                'type': 'order_shipped',
                'data': {'order_id': self.order.id}
            }

        def to_slack(self, notifiable):
            return {
                'text': f'Order #{self.order.id} has shipped!'
            }

    # Send notification
    Notify.send(user, OrderShippedNotification(order))

    # Send to multiple users
    Notify.send(users, OrderShippedNotification(order))

    # On-demand notification (no notifiable entity)
    Notify.route('mail', 'guest@example.com') \\
        .route('slack', '#orders') \\
        .notify(OrderShippedNotification(order))
"""

from fastpy_cli.libs.notifications.notification import Notification
from fastpy_cli.libs.notifications.manager import NotificationManager, AnonymousNotifiable
from fastpy_cli.libs.notifications.facade import Notify
from fastpy_cli.libs.notifications.channels import (
    NotificationChannel,
    MailChannel,
    DatabaseChannel,
    SlackChannel,
    SMSChannel,
)

__all__ = [
    "Notify",
    "Notification",
    "NotificationManager",
    "AnonymousNotifiable",
    "NotificationChannel",
    "MailChannel",
    "DatabaseChannel",
    "SlackChannel",
    "SMSChannel",
]
