### 🧰 CONFIG: How `include` and `exclude` work

For each path in `backups`, you can define **filters** to include or exclude files/folders in the ZIP.

The system uses **Unix-style patterns** (`*.txt`, `data/*`, etc.):

- Files are included only if they match a pattern in `include` **and** do not match any in `exclude`.
- Folders are traversed recursively unless excluded.

#### ✅ Examples
**Windows:**
```json
{
  "path": "C:\my_data",
  "zip_name": "backup_my_data",
  "filters": {
    "include": ["*", "data/*"],
    "exclude": ["data/*/*", "*.log"]
  }
}
```

**Linux:**
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

| Pattern         | Meaning                                                      |
|----------------|--------------------------------------------------------------|
| `*`            | Include all top-level files                                  |
| `data/*`       | Include all files in `data/` (non-recursively)               |
| `data/*/*`     | Exclude subfolders of `data/` and their contents             |
| `*.log`        | Exclude all `.log` files                                     |

#### 🧪 Tips

- If `include` is not specified, **all files** are included by default.
- If `exclude` is not specified, nothing is excluded.
- Paths are **relative to `path`**.
- Use `/` on all OSs, including Windows.