"""
Queue Manager implementation.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
import threading
import time

from fastpy_cli.libs.queue.job import Job, JobBatch, QueuedJob
from fastpy_cli.libs.queue.drivers import QueueDriver, SyncDriver, MemoryDriver


@dataclass
class PendingDispatch:
    """
    Pending job dispatch with fluent interface.
    """

    _manager: "QueueManager"
    _job: Optional[Job] = None
    _jobs: List[Job] = field(default_factory=list)
    _queue: str = "default"
    _connection: str = "default"
    _delay: int = 0

    def on(self, queue: str) -> "PendingDispatch":
        """Set the queue."""
        self._queue = queue
        return self

    def on_connection(self, connection: str) -> "PendingDispatch":
        """Set the connection."""
        self._connection = connection
        return self

    def delay(self, seconds: int) -> "PendingDispatch":
        """Set delay before processing."""
        self._delay = seconds
        return self

    def push(self, job: Job) -> str:
        """Push a single job."""
        self._job = job
        job.queue = self._queue

        if self._delay > 0:
            return self._manager.later(self._delay, job, self._queue)
        return self._manager._push(job, self._queue)

    def dispatch(self) -> Union[str, List[str]]:
        """Dispatch the job(s)."""
        if self._job:
            return self.push(self._job)
        elif self._jobs:
            return [self.push(job) for job in self._jobs]
        raise ValueError("No jobs to dispatch")


class QueueManager:
    """
    Queue manager supporting multiple connections and drivers.
    """

    _connections: Dict[str, QueueDriver] = {}
    _default_connection: str = "sync"
    _failed_jobs: List[QueuedJob] = []

    def __init__(self):
        # Register default drivers
        if "sync" not in self._connections:
            self._connections["sync"] = SyncDriver()
        if "memory" not in self._connections:
            self._connections["memory"] = MemoryDriver()

    @classmethod
    def connection(cls, name: str) -> QueueDriver:
        """Get a specific connection."""
        if name not in cls._connections:
            raise ValueError(f"Queue connection '{name}' not registered")
        return cls._connections[name]

    @classmethod
    def register_connection(cls, name: str, driver: QueueDriver) -> None:
        """Register a queue connection."""
        cls._connections[name] = driver

    @classmethod
    def set_default_connection(cls, name: str) -> None:
        """Set the default connection."""
        cls._default_connection = name

    @classmethod
    def get_default_connection(cls) -> QueueDriver:
        """Get the default connection."""
        return cls._connections.get(cls._default_connection, SyncDriver())

    @classmethod
    def on(cls, queue: str) -> PendingDispatch:
        """Create a pending dispatch for a specific queue."""
        return PendingDispatch(_manager=cls(), _queue=queue)

    @classmethod
    def using(cls, connection: str) -> PendingDispatch:
        """Create a pending dispatch using a specific connection."""
        return PendingDispatch(_manager=cls(), _connection=connection)

    def _push(self, job: Job, queue: str = "default") -> str:
        """Internal push method."""
        driver = self.get_default_connection()
        return driver.push(job, queue)

    @classmethod
    def push(cls, job: Union[Job, Dict[str, Any]], queue: str = "default") -> str:
        """
        Push a job onto the queue.

        Args:
            job: Job instance or dict for simple jobs
            queue: Queue name
        """
        driver = cls.get_default_connection()

        if isinstance(job, dict):
            # Create a simple job from dict
            job = _DictJob(job)

        return driver.push(job, queue)

    @classmethod
    def later(cls, delay: int, job: Job, queue: str = "default") -> str:
        """
        Push a job onto the queue after a delay.

        Args:
            delay: Delay in seconds
            job: Job instance
            queue: Queue name
        """
        driver = cls.get_default_connection()
        return driver.later(delay, job, queue)

    @classmethod
    def bulk(cls, jobs: List[Job], queue: str = "default") -> List[str]:
        """
        Push multiple jobs onto the queue.

        Args:
            jobs: List of job instances
            queue: Queue name
        """
        return [cls.push(job, queue) for job in jobs]

    @classmethod
    def chain(cls, jobs: List[Job]) -> str:
        """
        Chain jobs to run sequentially.

        Each job runs after the previous one completes.
        """
        if not jobs:
            raise ValueError("No jobs provided")

        # Create a chain job
        chain_job = _ChainJob(jobs)
        return cls.push(chain_job)

    @classmethod
    def batch(cls, jobs: List[Job]) -> JobBatch:
        """
        Create a batch of jobs.

        Returns a JobBatch that can be configured and dispatched.
        """
        batch = JobBatch()
        for job in jobs:
            batch.add(job)
        return batch

    @classmethod
    def dispatch_batch(cls, batch: JobBatch, queue: str = "default") -> str:
        """Dispatch a job batch."""
        batch_job = _BatchJob(batch)
        return cls.push(batch_job, queue)

    @classmethod
    def pop(cls, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next job from the queue."""
        driver = cls.get_default_connection()
        return driver.pop(queue)

    @classmethod
    def size(cls, queue: str = "default") -> int:
        """Get the queue size."""
        driver = cls.get_default_connection()
        return driver.size(queue)

    @classmethod
    def clear(cls, queue: str = "default") -> int:
        """Clear a queue."""
        driver = cls.get_default_connection()
        return driver.clear(queue)

    @classmethod
    def work(
        cls,
        queue: str = "default",
        sleep: float = 3.0,
        max_jobs: Optional[int] = None,
        timeout: int = 60,
    ) -> None:
        """
        Process jobs from the queue.

        Args:
            queue: Queue to process
            sleep: Seconds to sleep when queue is empty
            max_jobs: Maximum jobs to process (None for infinite)
            timeout: Job timeout in seconds
        """
        processed = 0

        while max_jobs is None or processed < max_jobs:
            job = cls.pop(queue)

            if job is None:
                time.sleep(sleep)
                continue

            cls._process_job(job, timeout)
            processed += 1

    @classmethod
    def _process_job(cls, queued_job: QueuedJob, timeout: int = 60) -> bool:
        """Process a single queued job."""
        try:
            job = Job.deserialize(queued_job.payload)
            job._job_id = queued_job.id
            job._attempts = queued_job.attempts + 1

            # Execute with timeout
            result = [None]
            exception = [None]

            def target():
                try:
                    job.before()
                    result[0] = job.handle()
                    job.after()
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                raise TimeoutError(f"Job {job.job_id} timed out after {timeout}s")

            if exception[0]:
                raise exception[0]

            # Job succeeded, delete from queue
            driver = cls.get_default_connection()
            driver.delete(queued_job.id, queued_job.queue)

            return True

        except Exception as e:
            # Job failed
            job = Job.deserialize(queued_job.payload)

            if queued_job.attempts < job.tries:
                # Retry
                driver = cls.get_default_connection()
                driver.release(queued_job.id, job.retry_after, queued_job.queue)
            else:
                # Move to failed jobs
                job.failed(e)
                cls._failed_jobs.append(queued_job)

            return False


class _DictJob(Job):
    """Simple job created from a dictionary."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.handler = data.get("handler")

    def handle(self) -> Any:
        if callable(self.handler):
            return self.handler(self.data)
        return self.data


class _ChainJob(Job):
    """Job that runs a chain of jobs sequentially."""

    def __init__(self, jobs: List[Job]):
        self.jobs = jobs

    def handle(self) -> None:
        for job in self.jobs:
            job.before()
            job.handle()
            job.after()


class _BatchJob(Job):
    """Job that processes a batch of jobs."""

    def __init__(self, batch: JobBatch):
        self.batch = batch

    def handle(self) -> None:
        for job in self.batch.jobs:
            try:
                job.before()
                job.handle()
                job.after()
                self.batch.job_completed(success=True)
            except Exception:
                self.batch.job_completed(success=False)
