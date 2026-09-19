# 🛡️ Automated Backup 🛡️

This project backs up specified directories, compresses the data (with optional password), uploads it to Google Drive, and logs the operations in a PostgreSQL database. Everything is containerized using Docker.

## 🧰 Features

- 🔐 Single or full backups with password-protected ZIP (AES) support.
- ☁️ Upload to Google Drive via OAuth2 API.
- 🧹 Automatic deletion of old files on Drive (configurable).
- 🗄️ Operation logging in PostgreSQL.
- 🐳 Isolated execution via Docker.

## 📝 Configuration (`config.json`)

The `config.json` file defines:

- Folders to include in the backups
- Credentials and options for Google Drive
- Logging settings for the PostgreSQL database
- [Config Example](CONFIG_EXAMPLE.json)

### 🔍 Field Descriptions

#### `General`
- `max_cpu_cores`: *(Since v2.2.0)* Maximum number of cores to use for multi-thread compression. Defaults to total cores minus 2, drastically improving backup speed without saturating the server.
- `log_path`: *(Optional)* Custom log path (useful for standalone runs without Docker). In Docker, it is recommended to leave it unset: logs are written to `/app/log` inside the container, and you can map any desired host destination via `docker-compose.yml` (e.g. `- /var/log/automated-backup:/app/log`).
- `log_rotation`: *(Optional)* Log rotation policy (if omitted, standard defaults are retained):
  - `when`: Time rotation frequency (default: `"W0"` = Monday at midnight; or `"midnight"`, `"D"`, `"W0"`-`"W6"`).
  - `interval`: Time interval (default: `1`).
  - `backup_count`: Number of historical backup log files to retain (default: `4`).
  - `max_size_mb`: Maximum log file size in MB for size-based rotation (optional: if specified, replaces time-based rotation).

#### `backups`

- `path`: path to the folder to be compressed (if it does not exist, it is created automatically)
- `zip_name`: name of the ZIP archive
- `filters.include` / `filters.exclude`: patterns to include or exclude files (supports `*` and subfolders) -> [Filter Usage Link](CONFIG_FILTER.en.md)

#### `googledrive`

- `backup_name`: base name of the full backup
- `instance`: Google Drive instance name for handling multiple uploads (name of your choice)
- `key_dir_drive`: ID of the destination folder on Google Drive. It's an alphanumeric code found in the drive link (e.g., https://drive.google.com/drive/folders/1WRdKfvjU2fUIkJ6XXXXXXXX-H7TxTd). Only the code "1WRdKfvjU2fUIkJ6XXXXXXXX-H7TxTd" should be provided.
- `password_zip`: password for the ZIP file (optional but strongly recommended)
- `delete_old_file_days`: delete files older than X days from Google Drive
- `zip_type`: "zip" for fast speed, "tar.xz" for better compression. 

#### `postgresql`
- `host`: PostgreSQL server host
- `dbname`: database name
- `schema`: name of the database schema
- `user`: username for accessing the database
- `password`: password for accessing the database
- `enabled`: [true|false] to indicate whether to use database logging

### ⚙️ PostgreSQL Setup

To log backup operations into a PostgreSQL database, you need to configure your database following the instructions in the PostgreSQL configuration file. This is especially useful if you want to integrate the data into **Grafana** reports.

- You can find the PostgreSQL setup instructions here [POSTGRESQL.en.md](POSTGRESQL.en.md).

Using PostgreSQL is **required** to monitor and visualize the operations via **Grafana**.

### 📝 Logging & logfmt Format

All application logs (both console output and rotating file logs) are emitted in standard **logfmt** format, making them directly compatible with **Grafana Loki**, **Promtail**, or **Alloy**:

```logfmt
time="2026-09-19 18:45:00" level=info logger="main" msg="Configuration loaded successfully from /app/config.json"
```

- **Standard fields**:
  - `time`: event timestamp (`YYYY-MM-DD HH:MM:SS`).
  - `level`: log severity (`debug`, `info`, `warn`, `error`, `critical`).
  - `logger`: origin module name (`main`, `postgres_db`, `google_drive`).
  - `msg`: event message (quoted with special character escaping).
  - `error`: optional exception traceback, formatted and escaped on a single line for single-line log parser compatibility.
- **Log Severities**:
  - `debug`: verbose internal details, SQL execution queries, parameter tracking, and file checks.
  - `info`: backup start/completion, archive creation, Google Drive upload milestones.
  - `warn`: non-fatal anomalies (e.g., paths not found, files already existing on Drive).
  - `error`: operational failures during execution (e.g., upload or compression error).
  - `critical`: fatal errors leading to script termination.
- **Configurable Rotation**:
  - **Default**: Rotating weekly every Monday (`when: "W0"`, `interval: 1`) with 4 weeks retention (`backup_count: 4`).
  - **Daily rotation**: Set e.g. `"when": "midnight"`, `"backup_count": 7`.
  - **Size-based rotation**: Set e.g. `"max_size_mb": 10`, `"backup_count": 5` to rotate when log file reaches 10 MB.
  - If the `log_rotation` block is omitted in `config.json`, the standard defaults are used.

# ⚙️ Creating Google Drive Credentials

Google Drive credentials are, of course, required to upload your backups to Drive.  
I recommend using this tool: [google-oauth-token-generator](https://github.com/CoccoAndrea/google-oauth-token-generator/tree/main), so you can obtain both `credential.json` and `token.json`.
**The two files must then be placed in a folder and mapped via Docker Compose.**

The credentials folder must contain a subfolder for each created Google Drive instance. Each subfolder, in turn, will hold the credentials and token files.
# 🐳 Docker Compose Configuration

This project uses **Docker** to run the automated backup inside an isolated container, making installation and execution easy across systems.

## 📝 Prerequisites

Before running the project, make sure you have **Docker** and **Docker Compose** installed. You can follow the official installation guides:

- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

## 🔧 Docker Compose Configuration

The `docker-compose.yml` file defines the services needed for the project to run. The main service is the automated backup, which connects to your **Google Drive** and **PostgreSQL**.

### Example `docker-compose.yml`

```yaml
services:
  automated-backup:
    image: andreacocco/automated-backup:latest
    container_name: automated-backup
    volumes:
      - ./log:/app/log  # Maps the host's log folder (any host path can be mapped, e.g. /var/log/automated-backup:/app/log)
      - ./config.json:/app/config.json # Maps the project config.json file
      - /c/credential:/app/credential # Maps the credential folder containing credential.json and token.json
      # On Windows, paths must be prefixed with "/c/". Example:
      - /c/temporary:/c/temporary  # For Windows
      # On Linux, paths are mounted normally. Example:
      - /srv/docker-projects/:/srv/docker-projects/:ro  # For Linux (read-only)
```

### 🔄 Start the Service

To start the container, run the following command in the directory containing `docker-compose.yml`:

```bash
docker-compose up --build
```

This command builds (if needed) and starts the service. Once the container is running, the backup will be executed automatically based on the `config.json` settings.

### 🛠️ Volumes and Config

Make sure the following folders and files are correctly configured:

1. **`config.json`**: Defines which folders to back up and credentials for Google Drive and PostgreSQL.
2. **`log/` folder**: Logs will be written here.
3. **Target folders**: Ensure the folders you want to back up are present.

## 📊 Monitoring with Grafana

To monitor the backup operations in real time, you can use **Grafana** connected to the PostgreSQL database used by this project.

### ✅ Requirements

- PostgreSQL must be **enabled** (`"enabled": true` in `config.json`)
- The logging table must be present as per [`POSTGRESQL.en.md`](POSTGRESQL.en.md)

### 🧭 Preconfigured Grafana Dashboard

A ready-to-use Grafana dashboard has been created and can be imported directly into your Grafana environment:

![Grafana Dashboard](Grafana.png)  
🔗 [Import this dashboard](Grafana_Dashboard.json)

> 💡 Tip: after importing, update the PostgreSQL datasource from the "Datasource" dropdown menu.

### ⚙️ Connecting Grafana to PostgreSQL

1. Log in to your Grafana instance
2. Go to **Connections → Data sources**
3. Add a new **PostgreSQL** datasource with the following parameters (as per `config.json`):
   - **Host**: e.g., `localhost:5432`
   - **Database**: value from `dbname`
   - **User/Password**: as configured
   - **SSL**: Disabled (unless using a secure connection)

4. Click **Save & Test**

Once configured, you can:
- Import the provided dashboard
- Create new queries to analyze backup frequency, errors, operation duration, and more

## 📅 Scheduled Backup Automation

To automatically schedule the start of the `automated-backup` container every day (e.g., at 02:00 and 18:30), refer to the guide:

📄 [How to schedule the backup with Home Assistant or Node-RED](AUTOMATION.en.md)
