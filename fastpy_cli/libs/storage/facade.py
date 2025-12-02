"""
Storage Facade - Static interface to storage manager.
"""

from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Union

from fastpy_cli.libs.storage.manager import StorageManager
from fastpy_cli.libs.storage.drivers import StorageDriver
from fastpy_cli.libs.support.container import container


# Register the storage manager in the container
container.singleton("storage", lambda c: StorageManager())


class Storage:
    """
    Storage Facade providing static access to storage manager.

    Usage:
        # Store files
        Storage.put('avatars/user.jpg', content)
        Storage.put_file('documents', uploaded_file)

        # Read files
        content = Storage.get('file.txt')
        if Storage.exists('file.txt'):
            ...

        # Get URL
        url = Storage.url('file.txt')

        # Use different disk
        Storage.disk('s3').put('backups/db.sql', content)
    """

    @staticmethod
    def _manager() -> StorageManager:
        """Get the storage manager from container."""
        return container.make("storage")

    @classmethod
    def disk(cls, name: str) -> StorageDriver:
        """Get a specific disk."""
        return cls._manager().disk(name)

    @classmethod
    def put(cls, path: str, contents: Union[str, bytes]) -> bool:
        """Store a file."""
        return cls._manager().put(path, contents)

    @classmethod
    def put_file(cls, path: str, file: BinaryIO, name: Optional[str] = None) -> str:
        """Store an uploaded file."""
        return cls._manager().put_file(path, file, name)

    @classmethod
    def get(cls, path: str) -> Optional[bytes]:
        """Get a file's contents."""
        return cls._manager().get(path)

    @classmethod
    def exists(cls, path: str) -> bool:
        """Check if a file exists."""
        return cls._manager().exists(path)

    @classmethod
    def missing(cls, path: str) -> bool:
        """Check if a file is missing."""
        return cls._manager().missing(path)

    @classmethod
    def delete(cls, path: str) -> bool:
        """Delete a file."""
        return cls._manager().delete(path)

    @classmethod
    def url(cls, path: str) -> str:
        """Get the URL for a file."""
        return cls._manager().url(path)

    @classmethod
    def size(cls, path: str) -> int:
        """Get the file size."""
        return cls._manager().size(path)

    @classmethod
    def last_modified(cls, path: str) -> Optional[datetime]:
        """Get the last modified time."""
        return cls._manager().last_modified(path)

    @classmethod
    def copy(cls, from_path: str, to_path: str) -> bool:
        """Copy a file."""
        return cls._manager().copy(from_path, to_path)

    @classmethod
    def move(cls, from_path: str, to_path: str) -> bool:
        """Move a file."""
        return cls._manager().move(from_path, to_path)

    @classmethod
    def append(cls, path: str, data: Union[str, bytes]) -> bool:
        """Append to a file."""
        return cls._manager().append(path, data)

    @classmethod
    def prepend(cls, path: str, data: Union[str, bytes]) -> bool:
        """Prepend to a file."""
        return cls._manager().prepend(path, data)

    @classmethod
    def files(cls, directory: str = "") -> List[str]:
        """Get all files in a directory."""
        return cls._manager().files(directory)

    @classmethod
    def all_files(cls, directory: str = "") -> List[str]:
        """Get all files recursively."""
        return cls._manager().all_files(directory)

    @classmethod
    def directories(cls, directory: str = "") -> List[str]:
        """Get all directories."""
        return cls._manager().directories(directory)

    @classmethod
    def make_directory(cls, path: str) -> bool:
        """Create a directory."""
        return cls._manager().make_directory(path)

    @classmethod
    def delete_directory(cls, path: str) -> bool:
        """Delete a directory."""
        return cls._manager().delete_directory(path)

    @classmethod
    def register_disk(cls, name: str, driver: StorageDriver) -> None:
        """Register a storage disk."""
        cls._manager().register_disk(name, driver)

    @classmethod
    def set_default_disk(cls, name: str) -> None:
        """Set the default disk."""
        cls._manager().set_default_disk(name)

    # Testing utilities
    @classmethod
    def fake(cls) -> "StorageFake":
        """
        Fake storage for testing.

        Usage:
            Storage.fake()
            Storage.put('file.txt', 'content')
            Storage.assert_exists('file.txt')
        """
        from fastpy_cli.libs.storage.drivers import MemoryDriver

        fake = StorageFake()
        container.instance("storage", fake)
        return fake


class StorageFake:
    """Fake storage for testing."""

    def __init__(self):
        from fastpy_cli.libs.storage.drivers import MemoryDriver
        self._driver = MemoryDriver()

    def put(self, path: str, contents: Union[str, bytes]) -> bool:
        return self._driver.put(path, contents)

    def put_file(self, path: str, file: BinaryIO, name: Optional[str] = None) -> str:
        return self._driver.put_file(path, file, name)

    def get(self, path: str) -> Optional[bytes]:
        return self._driver.get(path)

    def exists(self, path: str) -> bool:
        return self._driver.exists(path)

    def missing(self, path: str) -> bool:
        return not self.exists(path)

    def delete(self, path: str) -> bool:
        return self._driver.delete(path)

    def url(self, path: str) -> str:
        return self._driver.url(path)

    def size(self, path: str) -> int:
        return self._driver.size(path)

    def files(self, directory: str = "") -> List[str]:
        return self._driver.files(directory)

    def all_files(self, directory: str = "") -> List[str]:
        return self._driver.all_files(directory)

    def disk(self, name: str) -> "StorageFake":
        return self

    def assert_exists(self, path: str) -> bool:
        if not self.exists(path):
            raise AssertionError(f"File '{path}' does not exist")
        return True

    def assert_missing(self, path: str) -> bool:
        if self.exists(path):
            raise AssertionError(f"File '{path}' exists")
        return True
