import json
import shutil
import sys
from pathlib import Path
import logging
from datetime import datetime
import os
import zipfile, tarfile
import fnmatch
import pyzipper
import platform
import traceback
import concurrent.futures
import multiprocessing

from postgres_db import PostgreSQL
from logging_config import setup_logging
import google_drive

# Initial logging setup with standard configuration
setup_logging()
logger = logging.getLogger(__name__)

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            logger.info(f"Configuration loaded successfully from {config_file}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        sys.exit(8)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in configuration file {config_file}: {e}")
        sys.exit(8)

# Percorso assoluto di config.json accanto a script.py
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')
logger.info(f"Loading configuration from {config_path}")
config = load_config(config_path)

# Reconfigure logging if log_path or log_rotation is specified in config
log_path = config.get("log_path")
log_rotation = config.get("log_rotation")
if log_path or log_rotation:
    setup_logging(log_path=log_path, log_rotation=log_rotation)
    logger.info(f"Logging reconfigured: log_path={log_path or 'default'}, log_rotation={log_rotation or 'default'}")

postgresql = {}
try:
    postgresql = config.get("postgresql", {})
    if postgresql.get("enabled"):
        logger.info("PostgreSQL tracking is enabled")
        clientsql = PostgreSQL(postgresql["dbname"], postgresql["schema"], postgresql["user"], postgresql["password"], postgresql["host"])
        clientsql.check_and_create_instance_column_py()
        clientsql.check_and_update_primary_key_py()
    else:
        logger.info("PostgreSQL tracking is disabled")
except KeyError as e:
    logger.warning(f"Missing PostgreSQL configuration key: {e}. PostgreSQL tracking will be disabled")
    postgresql["enabled"] = False
except Exception as e:
    logger.error(f"Error loading PostgreSQL configuration: {e}", exc_info=True)
    logger.warning("PostgreSQL tracking will be disabled")
    postgresql["enabled"] = False

def zip_with_password(zip_path, in_path, password):
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_STORED, encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword(password.encode())
        zipf.setencryption(pyzipper.WZ_AES, nbits=128)

        for root, _, files in os.walk(in_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, in_path)
                zipf.write(file_path, arcname)

def zip_without_password(zip_path, in_path):
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_STORED) as zipf:
        for root, _, files in os.walk(in_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, in_path)
                zipf.write(file_path, arcname)

def create_backup(in_path, in_zip_name, in_type="single", filters=None, in_id_elab=None, in_password=None, zip_type="zip"):
    try:
        logger.info(f"Creating backup of type '{in_type}'")
        # Get the root directory of the project
        root_dir = Path(__file__).resolve().parent
        # Define the path for the temp folder
        temp_dir = root_dir / "temp"
        # Create the temp directory if it doesn't exist
        temp_dir.mkdir(exist_ok=True)

        # Define the full path for the zip file inside the temp folder
        zip_path = temp_dir / in_zip_name
        logger.info(f"Creating backup for {in_path} with name {in_zip_name}, type {in_type}, zip_type {zip_type}")
        if in_type == "full":
            in_path = temp_dir
            zip_path = root_dir / in_zip_name

            # Create the archive
            if in_password is None:
                logger.info(f"Creating full backup for {in_path} to {zip_path}.{zip_type} without password")
                if zip_type == "zip":
                    zip_without_password(f"{zip_path}.{zip_type}", in_path)
                elif zip_type == "tar.xz":
                    tar_path = f"{zip_path}.tar"
                    with tarfile.open(tar_path, "w") as tar:
                        tar.add(in_path, arcname=".")
                    try:
                        max_cores = int(config.get("max_cpu_cores", max(1, multiprocessing.cpu_count() - 2)))
                    except Exception:
                        max_cores = 2
                    import subprocess
                    subprocess.run(["xz", f"-T{max_cores}", tar_path], check=True)
            else:
                zip_type = "zip"
                logger.info(f"Creating full backup for {in_path} to {zip_path}.{zip_type} with password")
                zip_with_password(f"{zip_path}.{zip_type}", in_path, in_password)
            zip_size_bytes = os.path.getsize(f"{zip_path}.{zip_type}")
            zip_size_mb = max(round(zip_size_bytes / (1024 * 1024), 2), 0.01)
            logger.info(f"Backup created: {zip_path}.{zip_type} (size: {zip_size_mb} MB)")
            return str(zip_path) + ".zip", 0, {in_zip_name: zip_size_mb}
        else:
            logger.info(f"Creating single backup for {in_path} to {zip_path}.{zip_type}")
            # Creazione del file zip rispettando i filtri
            if zip_type == "zip":
                with zipfile.ZipFile(f"{zip_path}.{zip_type}", 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(in_path):
                        # Rimuovi file e cartelle escluse
                        if filters:
                            exclude_patterns = filters.get("exclude", [])
                            include_patterns = filters.get("include", ["*"])

                            rel_root = os.path.relpath(root, in_path)
                            if rel_root == ".":
                                rel_root = ""
                            # Filtra le directory
                            dirs[:] = [d for d in dirs if not any(
                                fnmatch.fnmatch(os.path.join(rel_root, d), pat.rstrip('/*')) for pat in
                                exclude_patterns)]

                            # Filtra i file
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.join(rel_root, file)
                                if any(fnmatch.fnmatch(relative_path, pat) for pat in include_patterns) and not any(
                                        fnmatch.fnmatch(relative_path, pat) for pat in exclude_patterns):
                                    zipf.write(full_path, relative_path)
                        else:
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(full_path, in_path)
                                zipf.write(full_path, relative_path)
            elif zip_type == "tar.xz":
                tar_path = f"{zip_path}.tar"
                with tarfile.open(tar_path, "w") as zipf:
                    for root, dirs, files in os.walk(in_path):
                        # Rimuovi file e cartelle escluse
                        if filters:
                            exclude_patterns = filters.get("exclude", [])
                            include_patterns = filters.get("include", ["*"])

                            rel_root = os.path.relpath(root, in_path)
                            if rel_root == ".":
                                rel_root = ""
                            # Filtra le directory
                            dirs[:] = [d for d in dirs if
                                       not any(fnmatch.fnmatch(os.path.join(rel_root, d), pat.rstrip('/*')) for pat in exclude_patterns)]

                            # Filtra i file
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(full_path, in_path)
                                if any(fnmatch.fnmatch(relative_path, pat) for pat in include_patterns) and not any(
                                        fnmatch.fnmatch(relative_path, pat) for pat in exclude_patterns):
                                    zipf.add(full_path, arcname=relative_path)
                        else:
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(full_path, in_path)
                                zipf.add(full_path, arcname=relative_path)
                try:
                    max_cores = int(config.get("max_cpu_cores", max(1, multiprocessing.cpu_count() - 2)))
                except Exception:
                    max_cores = 2
                import subprocess
                subprocess.run(["xz", f"-T{max_cores}", tar_path], check=True)
            zip_size_bytes = os.path.getsize(f"{zip_path}.{zip_type}")
            zip_size_mb = max(round(zip_size_bytes / (1024 * 1024), 2), 0.01)
            logger.info(f"Backup created: {zip_path}.{zip_type} (size: {zip_size_mb} MB)")
            return str(zip_path) + "." + zip_type, 0, {in_zip_name: zip_size_mb}
    except Exception as e:
        logger.error(f"Failed to create backup for {in_path}: {e}", exc_info=True)
        return None, 8, {}

def clear_backup(backup_name):
    try:
        if os.path.exists(backup_name):
            os.remove(backup_name)
            logger.info(f"File {backup_name} deleted successfully.")
        else:
            logger.debug(f"File {backup_name} does not exist.")
    except Exception as e:
        logger.warning(f"Error deleting file {backup_name}: {e}", exc_info=True)

def clear_temp_directory():
    try:
        root_dir = Path(__file__).resolve().parent
        temp_dir = root_dir / "temp"

        if temp_dir.exists() and temp_dir.is_dir():
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    logger.debug(f"Deleted temp file: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.debug(f"Deleted temp directory: {item}")

            logger.info("Successfully cleared contents of the 'temp' directory.")
        else:
            logger.debug("The 'temp' directory does not exist or is already empty.")
    except Exception as e:
        logger.error(f"Failed to clear the 'temp' directory: {e}", exc_info=True)
        raise

def generate_timestamped_filename(base_name="FullBackup"):
    """
    Generate a filename with a timestamp in the format FullBackup_YYYYMMDD_HHMMSS.zip.

    Args:
        base_name (str): The base name for the file (default is "FullBackup").

    Returns:
        str: The generated filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.zip"

def check_path_exists(path):
    return 0 if os.path.exists(path) else 8

def translate_windows_path(path):
    path = str(path)
    try:
        if os.name != "nt" and path.startswith("C:\\"):
            return Path(path.replace("C:\\", "/c/").replace("\\", "/"))
    except Exception as e:
        logger.warning(f"Failed to translate path {path}: {e}", exc_info=True)
    return Path(path)


def main():
    master_rc = 0
    rc_exists = 0
    full_dict_backups = []
    if platform.system() == "Windows":
        root_dir = Path(__file__).resolve().parent
        path_base_credential = root_dir / "credential"
    else:
        path_base_credential = Path("/app/credential")
    try:
        list_google_drive_configs = config["googledrive"]
        if isinstance(list_google_drive_configs, dict):
            list_google_drive_configs = [list_google_drive_configs]
        for google_drive_configs in list_google_drive_configs:
            list_dict_backups = []
            dict_backups = {}
            try:
                instance = google_drive_configs["instance"]
                path_credential = path_base_credential / instance
            except KeyError:
                instance = "default"
                path_credential = path_base_credential
            logger.info(f"Running instance: {instance}")
            logger.debug(f"Credential path check: {path_credential}")
            rc = check_path_exists(path_credential)
            if rc != 0:
                logger.error(f"Credential path does not exist: {path_credential}")
                raise FileNotFoundError(f"Credential path not found: {path_credential}")
            drive = google_drive.GoogleDriveManager(path_credential)
            zip_full_name = google_drive_configs["backup_name"]
            password = google_drive_configs["password_zip"]
            delete_old_file_days = google_drive_configs["delete_old_file_days"]
            zip_type = google_drive_configs["zip_type"]
            for item in config.get("backups", []):
                logger.debug(f"Processing backup item: {item}")
                try:
                    item_instance = item["instance"]
                except KeyError:
                    item_instance = "default"
                if item_instance != instance:
                    continue
                path = Path(item["path"])
                zip_name = item["zip_name"]
                filters = item.get("filters", None)
                logger.info(f"Creating backup for {path} with name {zip_name}")
                path = translate_windows_path(path)
                logger.debug(f"Path translated to {path}")
                if not path.exists():
                    logger.info(f"Path does not exist: {path}. Creating directory...")
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created missing directory: {path}")
                    except Exception as e:
                        logger.error(f"Failed to create directory {path}: {e}", exc_info=True)
                        rc_exists = 4
                        continue

                logger.info(f"Starting backup for {zip_name}")
                full_path_file, rc, dict_back = create_backup(path, zip_name, "single", filters, zip_type=zip_type)
                logger.info(f"Backup {zip_name} terminated with code {rc}")
                if rc != 0:
                    logger.error(f"Failed to create backup for {path}")
                    raise Exception(f"Backup failed for {path}")
                dict_backups.update(dict_back)
            full_path_file, rc, dict_back = create_backup(None, zip_full_name, "full", in_password=password, zip_type=zip_type)
            dict_backups.update(dict_back)
            clear_temp_directory()
            logger.info(f"Full backup created: {zip_full_name}, return code: {rc}")
            if rc == 0:
                logger.debug(f"Upload parameters: file={full_path_file}, folder_id={google_drive_configs['key_dir_drive']}")
                rc = drive.upload_to_google_drive(full_path_file, file_name=generate_timestamped_filename(zip_full_name),
                                                  folder_id=google_drive_configs["key_dir_drive"])
            if rc == 0:
                clear_backup(full_path_file)
                logger.info(f"Backup uploaded to Google Drive: {zip_full_name}")
                drive.delete_old_files_from_google_drive(google_drive_configs["key_dir_drive"], days_old=delete_old_file_days)
            if rc_exists == 4:
                master_rc = rc_exists
            else:
                master_rc = rc
            list_dict_backups.append(instance)
            list_dict_backups.append(dict_backups)
            full_dict_backups.append(list_dict_backups)
    except Exception as e:
        logger.critical(f"Backup execution failed: {e}", exc_info=True)
        master_rc = 8
    finally:
        return master_rc, full_dict_backups

if __name__ == "__main__":
    rc = 0
    id_elab = None
    try:
        date_start = datetime.now()
        rc_main, list_dict_backups = main()
        data_to_insert = {'script_name': 'automated-backup', 'data_iniz': date_start}
        rc_insert = 0
        if postgresql.get("enabled"):
            id_elab, rc_insert = clientsql.insert_ret_idelab('elaborazioni', data_to_insert)
        for data in list_dict_backups:
            dict_backups = data[1]
            instance = data[0]
            for row in dict_backups.items():
                if postgresql.get("enabled"):
                    data_to_insert = {'id_elab': id_elab, 'zip_name': row[0], 'size': row[1], 'instance': instance}
                    rc = clientsql.insert('elaborazioni_size', data_to_insert)
                else:
                    rc = 0
                if rc == 8:
                    raise Exception("Database insertion failed for elaborazioni_size")
        rc = rc_main
        logger.info(f"Script completed with return code {rc}")
        logger.debug(f"rc_insert: {rc_insert}")
        if rc == 8 or rc_insert != 0:
            raise Exception(f"Backup completed with error status: rc={rc}, rc_insert={rc_insert}")
    except Exception as e:
        logger.critical(f"Script execution failed: {e}", exc_info=True)
        rc = 8
        if postgresql.get("enabled") and id_elab is not None:
            try:
                conditions = {'id_elab': id_elab}
                data = {'esito': rc}
                logger.debug(f"Sending error status to DB: data={data}, conditions={conditions}")
                clientsql.update('elaborazioni', data, conditions)
            except Exception as db_err:
                logger.error(f"Failed to update error status in DB: {db_err}", exc_info=True)
    finally:
        if postgresql.get("enabled") and 'clientsql' in locals():
            try:
                if id_elab is not None:
                    date_end = datetime.now()
                    data = {'data_fine ': date_end, 'esito ': rc}
                    conditions = {'id_elab': id_elab}
                    clientsql.update('elaborazioni', data, conditions)
            except Exception as db_err:
                logger.error(f"Failed to update completion status in DB: {db_err}", exc_info=True)
            finally:
                clientsql.close()
        logger.info(f"Script finished with return code: {rc}")
        sys.exit(rc if isinstance(rc, int) else int(rc))
