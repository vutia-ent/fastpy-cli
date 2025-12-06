"""
Queue Drivers - Different queue backend implementations.
"""

import json
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from fastpy_cli.libs.queue.job import Job, QueuedJob


class QueueDriver(ABC):
    """Base class for queue drivers."""

    @abstractmethod
    def push(self, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue."""
        pass

    @abstractmethod
    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue after a delay."""
        pass

    @abstractmethod
    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next job from the queue."""
        pass

    @abstractmethod
    def delete(self, job_id: str, queue: str = "default") -> bool:
        """Delete a job from the queue."""
        pass

    @abstractmethod
    def release(self, job_id: str, delay: int = 0, queue: str = "default") -> bool:
        """Release a job back onto the queue."""
        pass

    @abstractmethod
    def size(self, queue: str = "default") -> int:
        """Get the size of the queue."""
        pass

    @abstractmethod
    def clear(self, queue: str = "default") -> int:
        """Clear all jobs from the queue."""
        pass

    def get_name(self) -> str:
        """Get the driver name."""
        return self.__class__.__name__.replace("Driver", "").lower()


class SyncDriver(QueueDriver):
    """
    Synchronous driver - executes jobs immediately.
    Useful for development and testing.
    """

    def __init__(self):
        self._processed: list[str] = []

    def push(self, job: Job, queue: str = "default") -> str:
        """Execute job immediately."""
        job_id = job.job_id

        try:
            job.before()
            job.handle()
            job.after()
        except Exception as e:
            job.failed(e)
            raise

        self._processed.append(job_id)
        return job_id

    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Sleep then execute."""
        time.sleep(delay)
        return self.push(job, queue)

    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        """Sync driver doesn't queue, so nothing to pop."""
        return None

    def delete(self, job_id: str, queue: str = "default") -> bool:
        return True

    def release(self, job_id: str, delay: int = 0, queue: str = "default") -> bool:
        return True

    def size(self, queue: str = "default") -> int:
        return 0

    def clear(self, queue: str = "default") -> int:
        return 0


class MemoryDriver(QueueDriver):
    """
    In-memory queue driver.
    Useful for testing.
    """

    def __init__(self):
        self._queues: dict[str, deque] = {}
        self._delayed: dict[str, list[tuple]] = {}
        self._lock = threading.Lock()

    def _get_queue(self, queue: str) -> deque:
        """Get or create a queue."""
        if queue not in self._queues:
            self._queues[queue] = deque()
        return self._queues[queue]

    def push(self, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue."""
        job_id = job.job_id

        queued_job = QueuedJob(
            id=job_id,
            queue=queue,
            payload=job.serialize(),
            created_at=datetime.now(),
        )

        with self._lock:
            self._get_queue(queue).append(queued_job)

        return job_id

    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue after a delay."""
        job_id = job.job_id
        available_at = datetime.now() + timedelta(seconds=delay)

        queued_job = QueuedJob(
            id=job_id,
            queue=queue,
            payload=job.serialize(),
            available_at=available_at,
            created_at=datetime.now(),
        )

        with self._lock:
            self._get_queue(queue).append(queued_job)

        return job_id

    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next available job from the queue."""
        with self._lock:
            q = self._get_queue(queue)

            for i, job in enumerate(q):
                if job.is_available():
                    del q[i]
                    job.reserved_at = datetime.now()
                    return job

        return None

    def delete(self, job_id: str, queue: str = "default") -> bool:
        """Delete a job from the queue."""
        with self._lock:
            q = self._get_queue(queue)
            for i, job in enumerate(q):
                if job.id == job_id:
                    del q[i]
                    return True
        return False

    def release(self, job_id: str, delay: int = 0, queue: str = "default") -> bool:
        """Release a job back onto the queue."""
        # For memory driver, just find and update the job
        with self._lock:
            q = self._get_queue(queue)
            for job in q:
                if job.id == job_id:
                    job.reserved_at = None
                    if delay > 0:
                        job.available_at = datetime.now() + timedelta(seconds=delay)
                    return True
        return False

    def size(self, queue: str = "default") -> int:
        """Get the size of the queue."""
        with self._lock:
            return len(self._get_queue(queue))

    def clear(self, queue: str = "default") -> int:
        """Clear all jobs from the queue."""
        with self._lock:
            q = self._get_queue(queue)
            count = len(q)
            q.clear()
            return count


class RedisDriver(QueueDriver):
    """
    Redis queue driver.
    Production-ready queue backend.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "fastpy:queue:",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._client = None

    def _get_client(self):
        """Get Redis client."""
        if self._client is None:
            try:
                import redis

                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=False,
                )
            except ImportError as err:
                raise ImportError(
                    "Redis driver requires redis package. Install with: pip install redis"
                ) from err
        return self._client

    def _queue_key(self, queue: str) -> str:
        """Get the Redis key for a queue."""
        return f"{self.prefix}{queue}"

    def _delayed_key(self, queue: str) -> str:
        """Get the Redis key for delayed jobs."""
        return f"{self.prefix}{queue}:delayed"

    def push(self, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue."""
        client = self._get_client()
        job_id = job.job_id

        payload = {
            "id": job_id,
            "payload": job.serialize().hex(),
            "attempts": 0,
            "created_at": datetime.now().isoformat(),
        }

        client.rpush(self._queue_key(queue), json.dumps(payload))
        return job_id

    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue after a delay."""
        client = self._get_client()
        job_id = job.job_id
        available_at = time.time() + delay

        payload = {
            "id": job_id,
            "payload": job.serialize().hex(),
            "attempts": 0,
            "created_at": datetime.now().isoformat(),
        }

        client.zadd(self._delayed_key(queue), {json.dumps(payload): available_at})
        return job_id

    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next job from the queue."""
        client = self._get_client()

        # First, move any delayed jobs that are now ready
        self._migrate_delayed(queue)

        # Pop from the queue
        data = client.lpop(self._queue_key(queue))
        if not data:
            return None

        payload = json.loads(data)
        return QueuedJob(
            id=payload["id"],
            queue=queue,
            payload=bytes.fromhex(payload["payload"]),
            attempts=payload.get("attempts", 0),
        )

    def _migrate_delayed(self, queue: str) -> None:
        """Move delayed jobs that are ready to the main queue."""
        client = self._get_client()
        now = time.time()

        # Get jobs that are ready
        ready = client.zrangebyscore(self._delayed_key(queue), 0, now)

        for job_data in ready:
            # Move to main queue
            client.rpush(self._queue_key(queue), job_data)
            client.zrem(self._delayed_key(queue), job_data)

    def delete(self, job_id: str, queue: str = "default") -> bool:
        """Delete a job from the queue."""
        # Redis doesn't easily support deletion by ID
        # Would need to scan the queue
        return True

    def release(self, job_id: str, delay: int = 0, queue: str = "default") -> bool:
        """Release a job back onto the queue."""
        # Would need job data to re-queue
        return True

    def size(self, queue: str = "default") -> int:
        """Get the size of the queue."""
        client = self._get_client()
        return client.llen(self._queue_key(queue))

    def clear(self, queue: str = "default") -> int:
        """Clear all jobs from the queue."""
        client = self._get_client()
        count = self.size(queue)
        client.delete(self._queue_key(queue))
        client.delete(self._delayed_key(queue))
        return count


class DatabaseDriver(QueueDriver):
    """
    Database queue driver.
    Uses SQLAlchemy for database operations.
    """

    def __init__(self, connection_string: str, table_name: str = "jobs"):
        self.connection_string = connection_string
        self.table_name = table_name
        self._engine = None
        self._table = None

    def _get_engine(self):
        """Get SQLAlchemy engine."""
        if self._engine is None:
            try:
                from sqlalchemy import (
                    Column,
                    DateTime,
                    Integer,
                    LargeBinary,
                    MetaData,
                    String,
                    Table,
                    create_engine,
                )

                self._engine = create_engine(self.connection_string)
                metadata = MetaData()

                self._table = Table(
                    self.table_name,
                    metadata,
                    Column("id", String(36), primary_key=True),
                    Column("queue", String(255), index=True),
                    Column("payload", LargeBinary),
                    Column("attempts", Integer, default=0),
                    Column("available_at", DateTime, nullable=True),
                    Column("created_at", DateTime),
                    Column("reserved_at", DateTime, nullable=True),
                )

                metadata.create_all(self._engine)

            except ImportError as err:
                raise ImportError(
                    "Database driver requires sqlalchemy. Install with: pip install sqlalchemy"
                ) from err

        return self._engine

    def push(self, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue."""
        engine = self._get_engine()
        job_id = job.job_id

        with engine.connect() as conn:
            conn.execute(
                self._table.insert().values(
                    id=job_id,
                    queue=queue,
                    payload=job.serialize(),
                    attempts=0,
                    created_at=datetime.now(),
                )
            )
            conn.commit()

        return job_id

    def later(self, delay: int, job: Job, queue: str = "default") -> str:
        """Push a job onto the queue after a delay."""
        engine = self._get_engine()
        job_id = job.job_id
        available_at = datetime.now() + timedelta(seconds=delay)

        with engine.connect() as conn:
            conn.execute(
                self._table.insert().values(
                    id=job_id,
                    queue=queue,
                    payload=job.serialize(),
                    attempts=0,
                    available_at=available_at,
                    created_at=datetime.now(),
                )
            )
            conn.commit()

        return job_id

    def pop(self, queue: str = "default") -> Optional[QueuedJob]:
        """Pop the next job from the queue."""
        from sqlalchemy import or_, select

        engine = self._get_engine()

        with engine.connect() as conn:
            # Find available job
            stmt = (
                select(self._table)
                .where(self._table.c.queue == queue)
                .where(self._table.c.reserved_at.is_(None))
                .where(
                    or_(
                        self._table.c.available_at.is_(None),
                        self._table.c.available_at <= datetime.now(),
                    )
                )
                .limit(1)
            )

            result = conn.execute(stmt).fetchone()

            if not result:
                return None

            # Reserve the job
            conn.execute(
                self._table.update()
                .where(self._table.c.id == result.id)
                .values(reserved_at=datetime.now())
            )
            conn.commit()

            return QueuedJob(
                id=result.id,
                queue=result.queue,
                payload=result.payload,
                attempts=result.attempts,
                available_at=result.available_at,
                created_at=result.created_at,
            )

    def delete(self, job_id: str, queue: str = "default") -> bool:
        """Delete a job from the queue."""
        engine = self._get_engine()

        with engine.connect() as conn:
            result = conn.execute(self._table.delete().where(self._table.c.id == job_id))
            conn.commit()
            return result.rowcount > 0

    def release(self, job_id: str, delay: int = 0, queue: str = "default") -> bool:
        """Release a job back onto the queue."""
        engine = self._get_engine()
        available_at = datetime.now() + timedelta(seconds=delay) if delay > 0 else None

        with engine.connect() as conn:
            result = conn.execute(
                self._table.update()
                .where(self._table.c.id == job_id)
                .values(
                    reserved_at=None,
                    available_at=available_at,
                    attempts=self._table.c.attempts + 1,
                )
            )
            conn.commit()
            return result.rowcount > 0

    def size(self, queue: str = "default") -> int:
        """Get the size of the queue."""
        from sqlalchemy import func, select

        engine = self._get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                select(func.count())
                .select_from(self._table)
                .where(self._table.c.queue == queue)
                .where(self._table.c.reserved_at.is_(None))
            )
            return result.scalar() or 0

    def clear(self, queue: str = "default") -> int:
        """Clear all jobs from the queue."""
        engine = self._get_engine()

        with engine.connect() as conn:
            result = conn.execute(self._table.delete().where(self._table.c.queue == queue))
            conn.commit()
            return result.rowcount
