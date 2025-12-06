"""
Fastpy Libs - Laravel-style abstractions for FastAPI.

Usage:
    from fastpy_cli.libs import Http, Mail, Cache, Storage, Queue, Notify, Event, Hash, Crypt

    # HTTP requests
    response = Http.get('https://api.example.com/users')
    response = Http.post('https://api.example.com/users', json={'name': 'John'})

    # Send email
    Mail.to('user@example.com').subject('Welcome!').send('welcome', {'name': 'John'})

    # Cache
    Cache.put('key', 'value', ttl=3600)
    value = Cache.get('key', default='fallback')

    # Storage
    Storage.put('avatars/user.jpg', file_content)
    url = Storage.url('avatars/user.jpg')

    # Queue jobs
    Queue.push(SendEmailJob(user_id=1))
    Queue.later(60, ProcessOrderJob(order_id=123))

    # Notifications
    Notify.send(user, OrderShippedNotification(order))

    # Events
    Event.dispatch('user.registered', {'user_id': 1})

    # Password hashing
    hashed = Hash.make('password')
    if Hash.check('password', hashed):
        print('Valid!')

    # Encryption
    encrypted = Crypt.encrypt('secret data')
    decrypted = Crypt.decrypt(encrypted)
"""

from fastpy_cli.libs.cache import Cache
from fastpy_cli.libs.encryption import Crypt
from fastpy_cli.libs.events import Event
from fastpy_cli.libs.hashing import Hash
from fastpy_cli.libs.http import Http
from fastpy_cli.libs.mail import Mail
from fastpy_cli.libs.notifications import Notification, Notify
from fastpy_cli.libs.queue import Job, Queue
from fastpy_cli.libs.storage import Storage
from fastpy_cli.libs.support.container import Container

__all__ = [
    "Container",
    "Http",
    "Mail",
    "Cache",
    "Storage",
    "Queue",
    "Job",
    "Notify",
    "Notification",
    "Event",
    "Hash",
    "Crypt",
]
