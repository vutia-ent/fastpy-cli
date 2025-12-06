"""
Queue/Jobs Facade - Laravel-style background job processing.

Usage:
    from fastpy_cli.libs import Queue, Job

    # Define a job
    class SendWelcomeEmail(Job):
        def __init__(self, user_id: int):
            self.user_id = user_id

        def handle(self):
            user = User.find(self.user_id)
            Mail.to(user.email).send('welcome', {'name': user.name})

    # Dispatch immediately
    Queue.push(SendWelcomeEmail(user_id=1))

    # Dispatch with delay
    Queue.later(60, SendWelcomeEmail(user_id=1))

    # Dispatch to specific queue
    Queue.on('emails').push(SendWelcomeEmail(user_id=1))

    # Chain jobs
    Queue.chain([
        ProcessOrder(order_id=1),
        SendOrderConfirmation(order_id=1),
        NotifyWarehouse(order_id=1),
    ])

    # Batch jobs
    batch = Queue.batch([
        SendEmail(user_id=1),
        SendEmail(user_id=2),
        SendEmail(user_id=3),
    ]).then(lambda: print('All done!')).dispatch()
"""

from fastpy_cli.libs.queue.drivers import (
    DatabaseDriver,
    QueueDriver,
    RedisDriver,
    SyncDriver,
)
from fastpy_cli.libs.queue.facade import Queue
from fastpy_cli.libs.queue.job import Job, SerializableJob
from fastpy_cli.libs.queue.manager import PendingDispatch, QueueManager

__all__ = [
    "Queue",
    "Job",
    "SerializableJob",
    "QueueManager",
    "PendingDispatch",
    "QueueDriver",
    "SyncDriver",
    "RedisDriver",
    "DatabaseDriver",
]
