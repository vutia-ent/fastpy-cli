"""
Job base classes.
"""

import json
import pickle
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


class Job(ABC):
    """
    Base class for queueable jobs.

    Usage:
        class SendWelcomeEmail(Job):
            def __init__(self, user_id: int):
                self.user_id = user_id

            def handle(self):
                user = User.find(self.user_id)
                Mail.to(user.email).send('welcome')
    """

    # Job configuration
    queue: str = "default"
    connection: str = "default"
    delay: int = 0
    tries: int = 3
    timeout: int = 60
    retry_after: int = 90

    # Runtime properties
    _job_id: Optional[str] = None
    _attempts: int = 0

    @abstractmethod
    def handle(self) -> Any:
        """Execute the job."""
        pass

    def failed(self, exception: Exception) -> None:  # noqa: B027
        """Handle a job failure. Override in subclass."""
        pass

    def before(self) -> None:  # noqa: B027
        """Called before the job executes. Override in subclass."""
        pass

    def after(self) -> None:  # noqa: B027
        """Called after the job executes successfully. Override in subclass."""
        pass

    @property
    def job_id(self) -> str:
        """Get the job ID."""
        if self._job_id is None:
            self._job_id = str(uuid.uuid4())
        return self._job_id

    @property
    def attempts(self) -> int:
        """Get the number of attempts."""
        return self._attempts

    def on_queue(self, queue: str) -> "Job":
        """Set the queue for this job."""
        self.queue = queue
        return self

    def on_connection(self, connection: str) -> "Job":
        """Set the connection for this job."""
        self.connection = connection
        return self

    def with_delay(self, seconds: int) -> "Job":
        """Set the delay for this job."""
        self.delay = seconds
        return self

    def with_tries(self, tries: int) -> "Job":
        """Set the number of tries."""
        self.tries = tries
        return self

    def serialize(self) -> bytes:
        """Serialize the job for storage.

        WARNING: Uses pickle which can execute arbitrary code on deserialization.
        Only deserialize data from trusted sources. For untrusted data,
        use SerializableJob with JSON serialization instead.
        """
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, data: bytes) -> "Job":
        """Deserialize a job from storage.

        WARNING: pickle.loads() can execute arbitrary code. Only use this
        with data from trusted sources (e.g., your own queue backend).
        For untrusted data, use SerializableJob with JSON serialization.

        Raises:
            ValueError: If deserialization fails or produces invalid job
        """
        try:
            job = pickle.loads(data)
            # Validate that the result is actually a Job instance
            if not isinstance(job, Job):
                raise ValueError(
                    f"Deserialized object is not a Job: {type(job).__name__}"
                )
            return job
        except Exception as e:
            raise ValueError(f"Failed to deserialize job: {e}") from e


class SerializableJob(Job):
    """
    A job that can be serialized to JSON.

    More portable and SAFER than pickle-based serialization.
    Requires explicit property definitions.
    """

    # SECURITY: Allowlist of modules that can be deserialized
    # Override in your application to add your job modules
    ALLOWED_MODULES: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "class": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "data": self.__dict__.copy(),
            "queue": self.queue,
            "delay": self.delay,
            "tries": self.tries,
            "job_id": self.job_id,
        }

    def serialize(self) -> bytes:
        """Serialize to JSON bytes (safer than pickle)."""
        return json.dumps(self.to_dict()).encode()

    @classmethod
    def deserialize(cls, data: bytes) -> "SerializableJob":
        """Deserialize from JSON bytes with security validation.

        Raises:
            ValueError: If class path is not in allowed modules
        """
        payload = json.loads(data.decode())
        class_path = payload["class"]

        # SECURITY: Validate the module is in the allowlist
        module_path, class_name = class_path.rsplit(".", 1)

        if cls.ALLOWED_MODULES:
            is_allowed = any(
                module_path == allowed or module_path.startswith(allowed + ".")
                for allowed in cls.ALLOWED_MODULES
            )
            if not is_allowed:
                raise ValueError(
                    f"Module '{module_path}' is not in ALLOWED_MODULES. "
                    f"Add it to SerializableJob.ALLOWED_MODULES to allow deserialization."
                )

        # Import the job class
        import importlib
        try:
            module = importlib.import_module(module_path)
            job_class = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Cannot load job class '{class_path}': {e}") from e

        # SECURITY: Verify the class is a SerializableJob subclass
        if not issubclass(job_class, SerializableJob):
            raise ValueError(
                f"Class '{class_path}' is not a SerializableJob subclass"
            )

        # Create instance
        job = job_class.__new__(job_class)
        job.__dict__.update(payload["data"])
        job.queue = payload.get("queue", "default")
        job.delay = payload.get("delay", 0)
        job.tries = payload.get("tries", 3)
        job._job_id = payload.get("job_id")

        return job


@dataclass
class QueuedJob:
    """Represents a job in the queue."""

    id: str
    queue: str
    payload: bytes
    attempts: int = 0
    available_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    reserved_at: Optional[datetime] = None

    def is_available(self) -> bool:
        """Check if the job is available for processing."""
        if self.available_at is None:
            return True
        return datetime.now() >= self.available_at


@dataclass
class JobBatch:
    """A batch of jobs to be processed together."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jobs: list[Job] = field(default_factory=list)
    pending_jobs: int = 0
    failed_jobs: int = 0
    finished_callback: Optional[Callable[[], None]] = None
    success_callback: Optional[Callable[[], None]] = None
    failure_callback: Optional[Callable[[], None]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def add(self, job: Job) -> "JobBatch":
        """Add a job to the batch."""
        self.jobs.append(job)
        self.pending_jobs += 1
        return self

    def then(self, callback: Callable[[], None]) -> "JobBatch":
        """Set callback for when all jobs finish."""
        self.finished_callback = callback
        return self

    def on_success(self, callback: Callable[[], None]) -> "JobBatch":
        """Set callback for when all jobs succeed."""
        self.success_callback = callback
        return self

    def on_failure(self, callback: Callable[[], None]) -> "JobBatch":
        """Set callback for when any job fails."""
        self.failure_callback = callback
        return self

    def job_completed(self, success: bool = True) -> None:
        """Mark a job as completed."""
        self.pending_jobs -= 1
        if not success:
            self.failed_jobs += 1

        if self.pending_jobs == 0:
            if self.finished_callback:
                self.finished_callback()

            if self.failed_jobs == 0 and self.success_callback:
                self.success_callback()
            elif self.failed_jobs > 0 and self.failure_callback:
                self.failure_callback()

    @property
    def finished(self) -> bool:
        """Check if all jobs are finished."""
        return self.pending_jobs == 0

    @property
    def successful(self) -> bool:
        """Check if all jobs succeeded."""
        return self.finished and self.failed_jobs == 0
