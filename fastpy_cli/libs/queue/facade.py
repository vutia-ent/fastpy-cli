"""
Queue Facade - Static interface to queue manager.
"""

from typing import Any, Optional, Union

from fastpy_cli.libs.queue.drivers import QueueDriver
from fastpy_cli.libs.queue.job import Job, JobBatch, QueuedJob
from fastpy_cli.libs.queue.manager import PendingDispatch, QueueManager
from fastpy_cli.libs.support.container import container

# Register the queue manager in the container
container.singleton("queue", lambda c: QueueManager())


class Queue:
    """
    Queue Facade providing static access to queue manager.

    Usage:
        # Push a job
        Queue.push(SendWelcomeEmail(user_id=1))

        # Push with delay
        Queue.later(60, SendReminderEmail(user_id=1))

        # Push to specific queue
        Queue.on('emails').push(SendNewsletter(user_ids=[1, 2, 3]))

        # Chain jobs
        Queue.chain([
            ProcessOrder(order_id=1),
            SendConfirmation(order_id=1),
        ])

        # Batch jobs
        Queue.batch([
            SendEmail(user_id=1),
            SendEmail(user_id=2),
        ]).then(lambda: print('Done!')).dispatch()
    """

    @staticmethod
    def _manager() -> QueueManager:
        """Get the queue manager from container."""
        return container.make("queue")

    @classmethod
    def on(cls, queue: str) -> PendingDispatch:
        """Create a pending dispatch for a specific queue."""
        return cls._manager().on(queue)

    @classmethod
    def using(cls, connection: str) -> PendingDispatch:
        """Use a specific connection."""
        return cls._manager().using(connection)

    @classmethod
    def push(cls, job: Union[Job, dict[str, Any]], queue: str = "default") -> str:
        """Push a job onto the queue."""
        return cls._manager().push(job, queue)

    @classmethod
    def later(cls, delay: int, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue after a delay."""
        return cls._manager().later(delay, job, queue)

    @classmethod
    def bulk(cls, jobs: list[Job], queue: str = "default") -> list[str]:
        """Push multiple jobs onto the queue."""
        return cls._manager().bulk(jobs, queue)

    @classmethod
    def chain(cls, jobs: list[Job]) -> str:
        """Chain jobs to run sequentially."""
        return cls._manager().chain(jobs)

    @classmethod
    def batch(cls, jobs: list[Job]) -> JobBatch:
        """Create a batch of jobs."""
        return cls._manager().batch(jobs)

    @classmethod
    def pop(cls, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next job from the queue."""
        return cls._manager().pop(queue)

    @classmethod
    def size(cls, queue: str = "default") -> int:
        """Get the queue size."""
        return cls._manager().size(queue)

    @classmethod
    def clear(cls, queue: str = "default") -> int:
        """Clear a queue."""
        return cls._manager().clear(queue)

    @classmethod
    def work(
        cls,
        queue: str = "default",
        sleep: float = 3.0,
        max_jobs: Optional[int] = None,
        timeout: int = 60,
    ) -> None:
        """Start processing jobs from the queue."""
        return cls._manager().work(queue, sleep, max_jobs, timeout)

    @classmethod
    def connection(cls, name: str) -> QueueDriver:
        """Get a specific connection."""
        return cls._manager().connection(name)

    @classmethod
    def register_connection(cls, name: str, driver: QueueDriver) -> None:
        """Register a queue connection."""
        return cls._manager().register_connection(name, driver)

    @classmethod
    def set_default_connection(cls, name: str) -> None:
        """Set the default connection."""
        return cls._manager().set_default_connection(name)

    # Testing utilities
    @classmethod
    def fake(cls) -> "QueueFake":
        """
        Fake queue for testing.

        Usage:
            Queue.fake()
            # ... code that queues jobs ...
            Queue.assert_pushed(SendWelcomeEmail)
        """
        fake = QueueFake()
        container.instance("queue", fake)
        return fake


class QueueFake:
    """
    Fake queue for testing.
    """

    def __init__(self):
        self._pushed: list[Job] = []
        self._delayed: list[tuple] = []

    def push(self, job: Union[Job, dict[str, Any]], queue: str = "default") -> str:
        """Record a pushed job."""
        if isinstance(job, dict):
            from fastpy_cli.libs.queue.manager import _DictJob
            job = _DictJob(job)
        self._pushed.append(job)
        return job.job_id

    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Record a delayed job."""
        self._delayed.append((delay, job))
        return job.job_id

    def bulk(self, jobs: list[Job], queue: str = "default") -> list[str]:
        return [self.push(job, queue) for job in jobs]

    def chain(self, jobs: list[Job]) -> str:
        from fastpy_cli.libs.queue.manager import _ChainJob
        return self.push(_ChainJob(jobs))

    def batch(self, jobs: list[Job]) -> JobBatch:
        batch = JobBatch()
        for job in jobs:
            batch.add(job)
        return batch

    def on(self, queue: str) -> PendingDispatch:
        return PendingDispatch(_manager=self, _queue=queue)

    def using(self, connection: str) -> PendingDispatch:
        return PendingDispatch(_manager=self, _connection=connection)

    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        return None

    def size(self, queue: str = "default") -> int:
        return len(self._pushed)

    def clear(self, queue: str = "default") -> int:
        count = len(self._pushed)
        self._pushed.clear()
        self._delayed.clear()
        return count

    def assert_pushed(self, job_class: type, count: Optional[int] = None) -> bool:
        """Assert a job was pushed."""
        matching = [j for j in self._pushed if isinstance(j, job_class)]

        if count is not None and len(matching) != count:
            raise AssertionError(
                f"Expected {count} {job_class.__name__} jobs, got {len(matching)}"
            )

        if not matching:
            raise AssertionError(f"No {job_class.__name__} jobs were pushed")

        return True

    def assert_not_pushed(self, job_class: type) -> bool:
        """Assert a job was not pushed."""
        matching = [j for j in self._pushed if isinstance(j, job_class)]

        if matching:
            raise AssertionError(
                f"Expected no {job_class.__name__} jobs, but {len(matching)} were pushed"
            )

        return True

    def assert_pushed_with(self, job_class: type, **kwargs) -> bool:
        """Assert a job was pushed with specific attributes."""
        for job in self._pushed:
            if isinstance(job, job_class) and all(
                getattr(job, k, None) == v for k, v in kwargs.items()
            ):
                return True

        raise AssertionError(
            f"No {job_class.__name__} job with {kwargs} was pushed"
        )

    def assert_nothing_pushed(self) -> bool:
        """Assert no jobs were pushed."""
        if self._pushed:
            raise AssertionError(f"{len(self._pushed)} jobs were pushed")
        return True

    @property
    def pushed(self) -> list[Job]:
        """Get pushed jobs."""
        return self._pushed

    @property
    def delayed(self) -> list[tuple]:
        """Get delayed jobs."""
        return self._delayed
