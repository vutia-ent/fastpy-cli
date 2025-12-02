"""
Storage Manager implementation.
"""

from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Union

from fastpy_cli.libs.storage.drivers import StorageDriver, LocalDriver, MemoryDriver


class StorageManager:
    """
    Storage manager supporting multiple disks.
    """

    _disks: Dict[str, StorageDriver] = {}
    _default_disk: str = "local"

    def __init__(self):
        # Register default local disk
        if "local" not in self._disks:
            self._disks["local"] = LocalDriver()
        if "memory" not in self._disks:
            self._disks["memory"] = MemoryDriver()

    @classmethod
    def disk(cls, name: str) -> StorageDriver:
        """Get a specific disk."""
        if name not in cls._disks:
            raise ValueError(f"Storage disk '{name}' not registered")
        return cls._disks[name]

    @classmethod
    def register_disk(cls, name: str, driver: StorageDriver) -> None:
        """Register a storage disk."""
        cls._disks[name] = driver

    @classmethod
    def set_default_disk(cls, name: str) -> None:
        """Set the default disk."""
        cls._default_disk = name

    @classmethod
    def get_default_disk(cls) -> StorageDriver:
        """Get the default disk."""
        if cls._default_disk not in cls._disks:
            cls._disks["local"] = LocalDriver()
        return cls._disks[cls._default_disk]

    @classmethod
    def put(cls, path: str, contents: Union[str, bytes]) -> bool:
        """Store a file."""
        return cls.get_default_disk().put(path, contents)

    @classmethod
    def put_file(cls, path: str, file: BinaryIO, name: Optional[str] = None) -> str:
        """Store an uploaded file."""
        return cls.get_default_disk().put_file(path, file, name)

    @classmethod
    def get(cls, path: str) -> Optional[bytes]:
        """Get a file's contents."""
        return cls.get_default_disk().get(path)

    @classmethod
    def exists(cls, path: str) -> bool:
        """Check if a file exists."""
        return cls.get_default_disk().exists(path)

    @classmethod
    def missing(cls, path: str) -> bool:
        """Check if a file is missing."""
        return not cls.exists(path)

    @classmethod
    def delete(cls, path: str) -> bool:
        """Delete a file."""
        return cls.get_default_disk().delete(path)

    @classmethod
    def url(cls, path: str) -> str:
        """Get the URL for a file."""
        return cls.get_default_disk().url(path)

    @classmethod
    def size(cls, path: str) -> int:
        """Get the file size."""
        return cls.get_default_disk().size(path)

    @classmethod
    def last_modified(cls, path: str) -> Optional[datetime]:
        """Get the last modified time."""
        return cls.get_default_disk().last_modified(path)

    @classmethod
    def copy(cls, from_path: str, to_path: str) -> bool:
        """Copy a file."""
        return cls.get_default_disk().copy(from_path, to_path)

    @classmethod
    def move(cls, from_path: str, to_path: str) -> bool:
        """Move a file."""
        return cls.get_default_disk().move(from_path, to_path)

    @classmethod
    def append(cls, path: str, data: Union[str, bytes]) -> bool:
        """Append to a file."""
        return cls.get_default_disk().append(path, data)

    @classmethod
    def prepend(cls, path: str, data: Union[str, bytes]) -> bool:
        """Prepend to a file."""
        return cls.get_default_disk().prepend(path, data)

    @classmethod
    def files(cls, directory: str = "") -> List[str]:
        """Get all files in a directory."""
        return cls.get_default_disk().files(directory)

    @classmethod
    def all_files(cls, directory: str = "") -> List[str]:
        """Get all files recursively."""
        return cls.get_default_disk().all_files(directory)

    @classmethod
    def directories(cls, directory: str = "") -> List[str]:
        """Get all directories."""
        return cls.get_default_disk().directories(directory)

    @classmethod
    def make_directory(cls, path: str) -> bool:
        """Create a directory."""
        return cls.get_default_disk().make_directory(path)

    @classmethod
    def delete_directory(cls, path: str) -> bool:
        """Delete a directory."""
        return cls.get_default_disk().delete_directory(path)
