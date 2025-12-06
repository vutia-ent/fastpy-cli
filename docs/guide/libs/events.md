# Events

Event dispatching and listening.

## Import

```python
from fastpy_cli.libs import Event
```

## Registering Listeners

```python
# Simple listener
Event.listen('user.registered', lambda data: send_welcome_email(data['user']))

# Multiple listeners for same event
Event.listen('order.placed', lambda data: notify_warehouse(data['order']))
Event.listen('order.placed', lambda data: send_confirmation(data['order']))
```

## Dispatching Events

```python
Event.dispatch('user.registered', {'user': user})
Event.dispatch('order.placed', {'order': order, 'user': user})
```

## Wildcard Listeners

```python
# Listen to all user events
Event.listen('user.*', lambda data: log_user_activity(data))

# Listen to all creation events
Event.listen('*.created', lambda data: log_creation(data))
```

## Event Subscribers

Group related listeners in a class:

```python
class UserEventSubscriber:
    def subscribe(self, events):
        events.listen('user.registered', self.on_registered)
        events.listen('user.login', self.on_login)
        events.listen('user.deleted', self.on_deleted)

    def on_registered(self, data):
        send_welcome_email(data['user'])
        create_default_settings(data['user'])

    def on_login(self, data):
        log_login(data['user'], data['ip'])
        update_last_login(data['user'])

    def on_deleted(self, data):
        cleanup_user_data(data['user_id'])
        send_goodbye_email(data['email'])

# Register subscriber
Event.subscribe(UserEventSubscriber())
```

## Common Events

```python
# User events
Event.dispatch('user.registered', {'user': user})
Event.dispatch('user.login', {'user': user, 'ip': ip})
Event.dispatch('user.logout', {'user': user})
Event.dispatch('user.password_changed', {'user': user})

# Model events
Event.dispatch('post.created', {'post': post})
Event.dispatch('post.updated', {'post': post, 'changes': changes})
Event.dispatch('post.deleted', {'post_id': post_id})

# Order events
Event.dispatch('order.placed', {'order': order})
Event.dispatch('order.shipped', {'order': order, 'tracking': tracking})
Event.dispatch('order.completed', {'order': order})
```
