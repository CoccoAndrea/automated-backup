# 🛡️ Automated Backup 🛡️

This project automatically backs up specified directories, compresses the data (with optional password), uploads it to Google Drive, and logs the operations in a PostgreSQL database. Everything runs in an isolated Docker container.

## 🧰 Features

- 🔐 Single or full backups with AES password-protected ZIP support.
- ☁️ Upload to Google Drive via OAuth2 API.
- 🧹 Automatic cleanup of old files on Drive (configurable).
- 🗄️ Operation tracking via PostgreSQL.
- 🐳 Isolated execution via Docker.

## 📝 Configuration (`config.json`)

The `config.json` file defines:

- Folders to include in the backups
- Google Drive credentials and options
- PostgreSQL database tracking settings
- [Config Example](CONFIG_EXAMPLE.json)

### 🔍 Field Descriptions

#### `backups`

- `path`: folder path to compress
- `zip_name`: name of the ZIP archive
- `filters.include` / `filters.exclude`: patterns to include or exclude files ([Filter usage](CONFIG_FILTER.en.md))

#### `googledrive`

- `backup_name`: base name of the full backup
- `key_dir_drive`: destination folder ID on Google Drive (found in the drive URL)
- `password_zip`: password for the ZIP file (optional but highly recommended)
- `delete_old_file_days`: deletes files older than X days on Google Drive

#### `postgresql`
- `host`: postgresql server host
- `dbname`: database name
- `schema`: database schema name
- `user`: username for the database
- `password`: password for the database
- `enabled`: [true|false] whether to enable database logging

### ⚙️ PostgreSQL Setup

To enable logging of operations in PostgreSQL, configure your database using the instructions in [`POSTGRESQL.en.md`](POSTGRESQL.en.md).

Using PostgreSQL is **required** for monitoring operations via **Grafana**.

## 📊 Monitoring with Grafana

To monitor backups in real time, connect **Grafana** to the PostgreSQL database used by this project.

### ✅ Requirements

- PostgreSQL must be **enabled** (`"enabled": true` in `config.json`)
- The logging table must be set up as shown in [`POSTGRESQL.en.md`](POSTGRESQL.en.md)

### 🧭 Ready-to-use Grafana Dashboard

I’ve created a preconfigured Grafana dashboard you can import directly into your Grafana instance:

![Grafana Dashboard](Grafana.png)  
🔗 [Import this dashboard](Grafana_Dashboard.json)

> 💡 Tip: after import, set the PostgreSQL datasource using the dropdown menu "Datasource".

### ⚙️ Connecting Grafana to PostgreSQL

1. Access your Grafana instance
2. Go to **Connections → Data sources**
3. Add a new **PostgreSQL** datasource using the parameters from `config.json`:
   - **Host**: e.g., `localhost:5432`
   - **Database**: as set in `dbname`
   - **User/Password**: as configured
   - **SSL**: disabled (unless using secure connection)

4. Click **Save & Test**

You can now:
- Import the provided dashboard
- Build new queries to monitor frequency, errors, duration, and more

## 🐳 Docker Compose Configuration

This project uses **Docker** to run the automated backup in an isolated container for easy deployment.

... (truncated for brevity; would continue in full version)