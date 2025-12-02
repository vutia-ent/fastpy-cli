"""
Storage Facade - Laravel-style file storage.

Usage:
    from fastpy_cli.libs import Storage

    # Store files
    Storage.put('avatars/user.jpg', file_content)
    Storage.put_file('documents', uploaded_file)

    # Read files
    content = Storage.get('avatars/user.jpg')
    exists = Storage.exists('avatars/user.jpg')

    # Get URL
    url = Storage.url('avatars/user.jpg')
    temp_url = Storage.temporary_url('private/doc.pdf', expires=3600)

    # Delete files
    Storage.delete('old/file.txt')
    Storage.delete_directory('temp/')

    # Disk operations
    Storage.disk('s3').put('backups/db.sql', backup_content)
    Storage.disk('local').copy('file.txt', 'backup.txt')

    # Directories
    files = Storage.files('documents/')
    all_files = Storage.all_files('documents/')  # Recursive
    directories = Storage.directories('/')
"""

from fastpy_cli.libs.storage.manager import StorageManager
from fastpy_cli.libs.storage.facade import Storage
from fastpy_cli.libs.storage.drivers import (
    StorageDriver,
    LocalDriver,
    S3Driver,
    MemoryDriver,
)

__all__ = [
    "Storage",
    "StorageManager",
    "StorageDriver",
    "LocalDriver",
    "S3Driver",
    "MemoryDriver",
]
