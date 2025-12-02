"""
Storage Drivers - Different storage backend implementations.
"""

import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Dict, Iterator, List, Optional, Union


class StorageDriver(ABC):
    """Base class for storage drivers."""

    @abstractmethod
    def put(self, path: str, contents: Union[str, bytes]) -> bool:
        """Store a file."""
        pass

    @abstractmethod
    def get(self, path: str) -> Optional[bytes]:
        """Get a file's contents."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    def url(self, path: str) -> str:
        """Get the URL for a file."""
        pass

    @abstractmethod
    def size(self, path: str) -> int:
        """Get the file size in bytes."""
        pass

    @abstractmethod
    def last_modified(self, path: str) -> Optional[datetime]:
        """Get the last modified time."""
        pass

    @abstractmethod
    def files(self, directory: str = "") -> List[str]:
        """Get all files in a directory."""
        pass

    @abstractmethod
    def all_files(self, directory: str = "") -> List[str]:
        """Get all files recursively."""
        pass

    @abstractmethod
    def directories(self, directory: str = "") -> List[str]:
        """Get all directories."""
        pass

    @abstractmethod
    def make_directory(self, path: str) -> bool:
        """Create a directory."""
        pass

    @abstractmethod
    def delete_directory(self, path: str) -> bool:
        """Delete a directory."""
        pass

    def put_file(self, path: str, file: BinaryIO, name: Optional[str] = None) -> str:
        """Store an uploaded file."""
        filename = name or getattr(file, "filename", "file")
        full_path = f"{path.rstrip('/')}/{filename}"
        contents = file.read()
        self.put(full_path, contents)
        return full_path

    def copy(self, from_path: str, to_path: str) -> bool:
        """Copy a file."""
        contents = self.get(from_path)
        if contents is None:
            return False
        return self.put(to_path, contents)

    def move(self, from_path: str, to_path: str) -> bool:
        """Move a file."""
        if self.copy(from_path, to_path):
            return self.delete(from_path)
        return False

    def append(self, path: str, data: Union[str, bytes]) -> bool:
        """Append to a file."""
        contents = self.get(path) or b""
        if isinstance(data, str):
            data = data.encode()
        return self.put(path, contents + data)

    def prepend(self, path: str, data: Union[str, bytes]) -> bool:
        """Prepend to a file."""
        contents = self.get(path) or b""
        if isinstance(data, str):
            data = data.encode()
        return self.put(path, data + contents)


class LocalDriver(StorageDriver):
    """Local filesystem storage driver."""

    def __init__(self, root: str = "storage", url_prefix: str = "/storage"):
        self.root = Path(root).resolve()
        self.url_prefix = url_prefix
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, path: str) -> Path:
        """Get the full path with path traversal protection."""
        # Normalize and resolve the path
        clean_path = path.lstrip("/")
        full_path = (self.root / clean_path).resolve()

        # SECURITY: Ensure the path is within the root directory
        try:
            full_path.relative_to(self.root)
        except ValueError:
            raise ValueError(
                f"Path traversal attempt detected: '{path}' escapes storage root"
            )

        return full_path

    def put(self, path: str, contents: Union[str, bytes]) -> bool:
        full_path = self._path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(contents, str):
            contents = contents.encode()

        full_path.write_bytes(contents)
        return True

    def get(self, path: str) -> Optional[bytes]:
        full_path = self._path(path)
        if not full_path.exists():
            return None
        return full_path.read_bytes()

    def exists(self, path: str) -> bool:
        return self._path(path).exists()

    def delete(self, path: str) -> bool:
        full_path = self._path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def url(self, path: str) -> str:
        return f"{self.url_prefix}/{path.lstrip('/')}"

    def size(self, path: str) -> int:
        return self._path(path).stat().st_size

    def last_modified(self, path: str) -> Optional[datetime]:
        full_path = self._path(path)
        if not full_path.exists():
            return None
        return datetime.fromtimestamp(full_path.stat().st_mtime)

    def files(self, directory: str = "") -> List[str]:
        dir_path = self._path(directory)
        if not dir_path.exists():
            return []
        return [
            str(f.relative_to(self.root))
            for f in dir_path.iterdir()
            if f.is_file()
        ]

    def all_files(self, directory: str = "") -> List[str]:
        dir_path = self._path(directory)
        if not dir_path.exists():
            return []
        return [
            str(f.relative_to(self.root))
            for f in dir_path.rglob("*")
            if f.is_file()
        ]

    def directories(self, directory: str = "") -> List[str]:
        dir_path = self._path(directory)
        if not dir_path.exists():
            return []
        return [
            str(d.relative_to(self.root))
            for d in dir_path.iterdir()
            if d.is_dir()
        ]

    def make_directory(self, path: str) -> bool:
        self._path(path).mkdir(parents=True, exist_ok=True)
        return True

    def delete_directory(self, path: str) -> bool:
        dir_path = self._path(path)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            return True
        return False


class S3Driver(StorageDriver):
    """AWS S3 storage driver."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        url_prefix: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        self.url_prefix = url_prefix or f"https://{bucket}.s3.{region}.amazonaws.com"
        self._client = None

    def _get_client(self):
        """Get S3 client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    endpoint_url=self.endpoint,
                )
            except ImportError:
                raise ImportError(
                    "S3 driver requires boto3. Install with: pip install boto3"
                )
        return self._client

    def put(self, path: str, contents: Union[str, bytes]) -> bool:
        client = self._get_client()

        if isinstance(contents, str):
            contents = contents.encode()

        client.put_object(Bucket=self.bucket, Key=path.lstrip("/"), Body=contents)
        return True

    def get(self, path: str) -> Optional[bytes]:
        client = self._get_client()

        try:
            response = client.get_object(Bucket=self.bucket, Key=path.lstrip("/"))
            return response["Body"].read()
        except client.exceptions.NoSuchKey:
            return None

    def exists(self, path: str) -> bool:
        client = self._get_client()

        try:
            client.head_object(Bucket=self.bucket, Key=path.lstrip("/"))
            return True
        except Exception:
            return False

    def delete(self, path: str) -> bool:
        client = self._get_client()
        client.delete_object(Bucket=self.bucket, Key=path.lstrip("/"))
        return True

    def url(self, path: str) -> str:
        return f"{self.url_prefix}/{path.lstrip('/')}"

    def temporary_url(self, path: str, expires: int = 3600) -> str:
        """Generate a temporary signed URL."""
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path.lstrip("/")},
            ExpiresIn=expires,
        )

    def size(self, path: str) -> int:
        client = self._get_client()
        response = client.head_object(Bucket=self.bucket, Key=path.lstrip("/"))
        return response["ContentLength"]

    def last_modified(self, path: str) -> Optional[datetime]:
        client = self._get_client()
        try:
            response = client.head_object(Bucket=self.bucket, Key=path.lstrip("/"))
            return response["LastModified"]
        except Exception:
            return None

    def files(self, directory: str = "") -> List[str]:
        client = self._get_client()
        prefix = directory.strip("/")
        if prefix:
            prefix += "/"

        response = client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            Delimiter="/",
        )

        return [obj["Key"] for obj in response.get("Contents", [])]

    def all_files(self, directory: str = "") -> List[str]:
        client = self._get_client()
        prefix = directory.strip("/")
        if prefix:
            prefix += "/"

        files = []
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                files.append(obj["Key"])

        return files

    def directories(self, directory: str = "") -> List[str]:
        client = self._get_client()
        prefix = directory.strip("/")
        if prefix:
            prefix += "/"

        response = client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            Delimiter="/",
        )

        return [
            p["Prefix"].rstrip("/")
            for p in response.get("CommonPrefixes", [])
        ]

    def make_directory(self, path: str) -> bool:
        # S3 doesn't have real directories, create an empty object
        client = self._get_client()
        client.put_object(Bucket=self.bucket, Key=f"{path.strip('/')}/")
        return True

    def delete_directory(self, path: str) -> bool:
        client = self._get_client()
        prefix = path.strip("/") + "/"

        # Delete all objects with the prefix
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if objects:
                client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": objects},
                )

        return True


class MemoryDriver(StorageDriver):
    """In-memory storage driver for testing."""

    def __init__(self, url_prefix: str = "/storage"):
        self._files: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict] = {}
        self.url_prefix = url_prefix

    def put(self, path: str, contents: Union[str, bytes]) -> bool:
        path = path.lstrip("/")
        if isinstance(contents, str):
            contents = contents.encode()
        self._files[path] = contents
        self._metadata[path] = {"modified": datetime.now()}
        return True

    def get(self, path: str) -> Optional[bytes]:
        return self._files.get(path.lstrip("/"))

    def exists(self, path: str) -> bool:
        return path.lstrip("/") in self._files

    def delete(self, path: str) -> bool:
        path = path.lstrip("/")
        if path in self._files:
            del self._files[path]
            del self._metadata[path]
            return True
        return False

    def url(self, path: str) -> str:
        return f"{self.url_prefix}/{path.lstrip('/')}"

    def size(self, path: str) -> int:
        content = self._files.get(path.lstrip("/"), b"")
        return len(content)

    def last_modified(self, path: str) -> Optional[datetime]:
        meta = self._metadata.get(path.lstrip("/"), {})
        return meta.get("modified")

    def files(self, directory: str = "") -> List[str]:
        directory = directory.strip("/")
        prefix = f"{directory}/" if directory else ""
        return [
            f for f in self._files
            if f.startswith(prefix) and "/" not in f[len(prefix):]
        ]

    def all_files(self, directory: str = "") -> List[str]:
        directory = directory.strip("/")
        prefix = f"{directory}/" if directory else ""
        return [f for f in self._files if f.startswith(prefix)]

    def directories(self, directory: str = "") -> List[str]:
        directory = directory.strip("/")
        prefix = f"{directory}/" if directory else ""
        dirs = set()
        for path in self._files:
            if path.startswith(prefix):
                remaining = path[len(prefix):]
                if "/" in remaining:
                    dir_name = remaining.split("/")[0]
                    dirs.add(f"{prefix}{dir_name}" if prefix else dir_name)
        return list(dirs)

    def make_directory(self, path: str) -> bool:
        return True

    def delete_directory(self, path: str) -> bool:
        prefix = path.strip("/") + "/"
        to_delete = [f for f in self._files if f.startswith(prefix)]
        for f in to_delete:
            del self._files[f]
            if f in self._metadata:
                del self._metadata[f]
        return True
