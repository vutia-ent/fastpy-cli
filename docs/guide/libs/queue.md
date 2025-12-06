# Queue

Background job processing.

## Import

```python
from fastpy_cli.libs import Queue, Job
```

## Defining Jobs

```python
class SendWelcomeEmail(Job):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def handle(self):
        user = User.find(self.user_id)
        Mail.to(user.email).send('welcome', {'user': user})
```

## Dispatching Jobs

```python
# Dispatch immediately
Queue.push(SendWelcomeEmail(user_id=123))

# Delay execution (60 seconds)
Queue.later(60, SendWelcomeEmail(user_id=123))
```

## Named Queues

```python
# Send to specific queue
Queue.on('emails').push(SendWelcomeEmail(user_id=123))
Queue.on('notifications').push(SendNotification(user_id=123))
```

## Job Chains

Execute jobs sequentially:

```python
Queue.chain([
    ProcessPayment(order_id=1),
    SendConfirmation(order_id=1),
    UpdateInventory(order_id=1),
])
```

## Job Configuration

```python
class SlowJob(Job):
    queue = 'slow'       # Queue name
    tries = 5            # Max attempts
    timeout = 300        # 5 minutes
    retry_after = 60     # Retry delay

    def handle(self):
        # Job logic
        pass

    def failed(self, exception):
        # Handle failure
        log_error(exception)
```

## Drivers

| Driver | Description |
|--------|-------------|
| `sync` | Execute immediately (default) |
| `memory` | In-memory queue |
| `redis` | Redis-backed queue |
| `database` | Database-backed queue |

## Configuration

```ini
QUEUE_DRIVER=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Running Workers

```bash
# Start worker
fastpy queue:work

# Specific queue
fastpy queue:work --queue=emails

# With timeout
fastpy queue:work --timeout=60
```
