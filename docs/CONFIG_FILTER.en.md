### 🧰 CONFIG: How `include` and `exclude` work

For each path specified in `backups`, you can define **filters** to choose which files or directories to include or exclude in the `.zip` file.

The system uses **Unix-style patterns** (such as `*.txt`, `data/*`, etc.) to filter:

- **Files** are included only if they match at least one pattern in `include` **and** do not match any pattern in `exclude`.
- **Directories** are explored recursively, but excluded subdirectories are ignored.

#### ✅ Practical Examples

**Example for Windows:**
```json
{
  "path": "C:\\my_data",
  "zip_name": "backup_my_data",
  "filters": {
    "include": ["*", "data/*"],
    "exclude": ["data/*/*", "*.log"]
  }
}
```

**Example forLinux:**
```json
{
  "path": "/srv/docker-projects/my_data/",
  "zip_name": "backup_my_data",
  "filters": {
    "include": ["*", "data/*"],
    "exclude": ["data/*/*", "*.log"]
  }
}
```

| Pattern         | Meaning                                                                 |
|----------------|-------------------------------------------------------------------------|
| `*`            | Include all files in the top-level directory                            |
| `data/*`       | Include all files in the `data/` folder (non-recursively)               |
| `data/*/*`     | Exclude subdirectories of `data/` and their content                    |
| `*.log`        | Exclude all files with the `.log` extension                            |

#### 🧪 Tips

- If you don't specify `include`, **all files** will be taken by default.
- If you don't specify `exclude`, nothing will be excluded.
- The paths in the filters are **relative to the `path` specified**.
- Use `/` even on Windows to avoid compatibility issues.
