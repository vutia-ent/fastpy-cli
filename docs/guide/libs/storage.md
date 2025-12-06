# Storage

File storage with multiple backend support.

## Import

```python
from fastpy_cli.libs import Storage
```

## Basic Operations

```python
# Store file
Storage.put('avatars/user-123.jpg', file_content)

# Get file content
content = Storage.get('avatars/user-123.jpg')

# Check existence
if Storage.exists('avatars/user-123.jpg'):
    print('File exists')

# Get URL
url = Storage.url('avatars/user-123.jpg')

# Delete
Storage.delete('avatars/user-123.jpg')
```

## File Operations

```python
# Copy
Storage.copy('old.jpg', 'new.jpg')

# Move
Storage.move('temp/file.txt', 'permanent/file.txt')

# Get file size
size = Storage.size('document.pdf')

# Get last modified time
modified = Storage.last_modified('document.pdf')
```

## Directories

```python
# Create directory
Storage.make_directory('uploads/2024')

# Delete directory
Storage.delete_directory('temp/')

# List files
files = Storage.files('avatars/')

# List all files (recursive)
all_files = Storage.all_files('documents/')

# List directories
dirs = Storage.directories('uploads/')
```

## Using Specific Disk

```python
# S3
Storage.disk('s3').put('backups/db.sql', content)
url = Storage.disk('s3').url('backups/db.sql')

# Local
Storage.disk('local').put('temp/file.txt', content)
```

## Drivers

| Driver | Description |
|--------|-------------|
| `local` | Local filesystem |
| `s3` | Amazon S3 |
| `memory` | In-memory (testing) |

## Configuration

```ini
# Local
STORAGE_DRIVER=local
STORAGE_PATH=./storage

# S3
STORAGE_DRIVER=s3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=my-bucket
```

## Security

Storage includes path traversal protection, preventing access to files outside the configured storage directory.
