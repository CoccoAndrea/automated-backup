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

from postgres_db import PostgreSQL

logger = logging.getLogger(__name__)
from logging_config import setup_logging
import google_drive
setup_logging()

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            logging.info(f"Configuration loaded successfully from {config_file}")
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_file}")
        sys.exit(8)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in the configuration file: {config_file}")
        sys.exit(8)

# Percorso assoluto di config.json accanto a script.py
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')
logging.info(f"Loading configuration from {config_path}")
config = load_config(config_path)
postgresql = {}
try:
    postgresql = config["postgresql"]
#logging.info("host:" + postgresql["host"] + " dbname:" + postgresql["dbname"] + " user:" + postgresql["user"] + " password:" + postgresql["password"] + postgresql["enabled"])
    if postgresql["enabled"]:
        logging.info("Traking on posgresdb will be enabled")
        clientsql = PostgreSQL(postgresql["dbname"],  postgresql["schema"], postgresql["user"], postgresql["password"], postgresql["host"])
    else:
        logging.warning("Traking on posgresdb will be disabled")
except KeyError:
    logging.warning("Missing 'postgresql'. Traking on posgresdb will be disabled")
    postgresql["enabled"] = False
except Exception as e:
    logging.error(f"Error loading PostgreSQL configuration: {e}")
    logging.warning("Traking on posgresdb will be disabled")
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
        logging.info(f"Creating type {in_type}")
        # Get the root directory of the project
        root_dir = Path(__file__).resolve().parent
        # Define the path for the temp folder
        temp_dir = root_dir / "temp"
        # Create the temp directory if it doesn't exist
        temp_dir.mkdir(exist_ok=True)

        # Define the full path for the zip file inside the temp folder
        zip_path = temp_dir / in_zip_name
        logging.info(f"Creating backup for {in_path} with name {in_zip_name} and type {in_type} and zip_type {zip_type}")
        if in_type == "full":
            in_path = temp_dir
            zip_path = root_dir / in_zip_name

            # Create the archive
            if in_password is None:
                logging.info(f"Creating full backup for {in_path} to {zip_path}.zip without password")
                if zip_type == "zip":
                    zip_without_password(f"{zip_path}.{zip_type}", in_path)
                elif zip_type == "tar.xz":
                    with tarfile.open(f"{zip_path}.tar.xz", "w:xz") as tar:
                        tar.add(in_path, arcname=".")
            else:
                zip_type = "zip"
                logging.info(f"Creating full backup for {in_path} to {zip_path}.zip with password")
                zip_with_password(f"{zip_path}.{zip_type}", in_path, in_password)
            zip_size_bytes = os.path.getsize(f"{zip_path}.{zip_type}")
            zip_size_mb = max(round(zip_size_bytes / (1024 * 1024),2),0.01)
            logging.info(f"Backup created: {zip_path}.{zip_type} (size: {zip_size_mb} MB)")
            return str(zip_path) + ".zip", 0, {in_zip_name : zip_size_mb}
        else:
            logging.info(f"Creating single backup for {in_path} to {zip_path}.{zip_type}")
        # Create the archive
            # Creazione del file zip rispettando i filtri
            if zip_type == "zip":
                with zipfile.ZipFile(f"{zip_path}.{zip_type}", 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(in_path):
                        #logging.info(f"Current directory: {root}")
                        #logging.info(f"Subdirectories: {dirs}")
                        #logging.info(f"Files: {files}")
                        # Rimuovi file e cartelle escluse
                        if filters:
                            exclude_patterns = filters.get("exclude", [])
                            include_patterns = filters.get("include", ["*"])

                            # Filtra le directory
                            dirs[:] = [d for d in dirs if
                                       not any(fnmatch.fnmatch(os.path.join(root, d), pat) for pat in exclude_patterns)]

                            # Filtra i file
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(full_path, in_path)
                                if any(fnmatch.fnmatch(relative_path, pat) for pat in include_patterns) and not any(
                                        fnmatch.fnmatch(relative_path, pat) for pat in exclude_patterns):
                                #    logging.info(f"Including file: {full_path}")
                                    zipf.write(full_path, relative_path)
                                #else:
                                #    logging.info(f"Excluding file: {full_path}")
            elif zip_type == "tar.xz":
                logging.info(f"Creating single backup for {in_path} to {zip_path}.{zip_type}")
                with tarfile.open(f"{zip_path}.{zip_type}", "w:xz") as zipf:
                    logging.info(f"2Creating single backup for {in_path} to {zip_path}.{zip_type}")
                    for root, dirs, files in os.walk(in_path):
                        logging.info(f"root: {root} dirs: {dirs} files: {files}")
                        #logging.info(f"Current directory: {root}")
                        #logging.info(f"Subdirectories: {dirs}")
                        #logging.info(f"Files: {files}")
                        # Rimuovi file e cartelle escluse
                        if filters:
                            exclude_patterns = filters.get("exclude", [])
                            include_patterns = filters.get("include", ["*"])

                            # Filtra le directory
                            dirs[:] = [d for d in dirs if
                                       not any(fnmatch.fnmatch(os.path.join(root, d), pat) for pat in exclude_patterns)]

                            # Filtra i file
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(full_path, in_path)
                                if any(fnmatch.fnmatch(relative_path, pat) for pat in include_patterns) and not any(
                                        fnmatch.fnmatch(relative_path, pat) for pat in exclude_patterns):
                                #    logging.info(f"Including file: {full_path}")
                                    zipf.add(full_path, arcname=relative_path)
            zip_size_bytes = os.path.getsize(f"{zip_path}.{zip_type}")
            zip_size_mb = max(round(zip_size_bytes / (1024 * 1024),2),0.01)
            logging.info(f"Backup created: {zip_path}.{zip_type} (size: {zip_size_mb} MB)")
            return str(zip_path) + "."+zip_type, 0, {in_zip_name: zip_size_mb}
    except Exception as e:
        logging.error(f"Failed to create backup for {in_path}: {e}")
        return None, 8

def clear_backup(backup_name):
    try:
        # Controlla se il file esiste
        if os.path.exists(backup_name):
            os.remove(backup_name)  # Cancella il file
            logging.info(f"File {backup_name} eliminato con successo.")
        else:
            logging.info(f"Il file {backup_name} non esiste.")
    except Exception as e:
        logging.warning(f"Errore durante l'eliminazione del file {backup_name}: {e}")
def clear_temp_directory():
    try:
        # Get the root directory of the project and the temp directory path
        root_dir = Path(__file__).resolve().parent
        temp_dir = root_dir / "temp"

        if temp_dir.exists() and temp_dir.is_dir():
            # Iterate through and delete all files and subdirectories in the temp directory
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink()  # Delete file
                    logging.info(f"Deleted file: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)  # Delete directory
                    logging.info(f"Deleted directory: {item}")

            logging.info(f"Successfully cleared contents of the 'temp' directory.")
        else:
            logging.warning(f"The 'temp' directory does not exist or is already empty.")
    except Exception as e:
        logging.error(f"Failed to clear the 'temp' directory: {e}")
        raise

def generate_timestamped_filename(self, base_name="FullBackup"):
    """
    Generate a filename with a timestamp in the format FullBackup_YYYYMMDD_hh24:mi:ss.zip.

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
        logging.error(f"Failed to translate path: {e}")
    return Path(path)

def main():
    master_rc = 0
    rc_exists = 0
    dict_backups = {}
    #if platform.system() == "Windows":
        # se sei su Windows → usa la cartella locale "credential"
    #    root_dir = Path(__file__).resolve().parent
    #    path_credential = root_dir / "credential"
    #else:
        # altrimenti (Linux, macOS, Docker, ecc.)
    path_credential = "/app/credential"
    try:
        google_drive_config = config["googledrive"]
        rc = check_path_exists(path_credential)
        if rc != 0:
            logging.error(f"Error: {path_credential} does not exist.")
            raise Exception
        drive = google_drive.GoogleDriveManager(path_credential)
        zip_full_name = google_drive_config["backup_name"]
        password = google_drive_config["password_zip"]
        delete_old_file_days = google_drive_config["delete_old_file_days"]
        zip_type = google_drive_config["zip_type"]
        for item in config.get("backups", []):
            path = Path(item["path"])
            zip_name = item["zip_name"]
            filters = item.get("filters", None)  # Ottieni i filtri dalla configurazione
            logging.info(f"Creating backup for {path} with name {zip_name}")
            path = translate_windows_path(path)
            logging.info(f"Path translated to {path}")
            if path.exists():
                logging.info(f"Backup start")
                full_path_file, rc, dict_back = create_backup(path, zip_name, "single", filters, zip_type=zip_type)
                logging.info(f"Backup terminated with code {rc}")
                if rc != 0:
                    logging.error(f"Failed to create backup for {path}")
                    raise Exception
                dict_backups.update(dict_back)
            else:
                logging.warning(f"Path does not exist: {path}")
                rc_exists = 4
        full_path_file, rc, dict_back = create_backup(None, zip_full_name, "full", in_password=password, zip_type=zip_type)
        dict_backups.update(dict_back)
        clear_temp_directory()
        logging.info(f"Backups created: {dict_backups}")
        if rc == 0:
            rc = drive.upload_to_google_drive(full_path_file, file_name=generate_timestamped_filename(zip_full_name),
                                              folder_id=google_drive_config["key_dir_drive"])
        if rc == 0:
            clear_backup(full_path_file)
            logging.info(f"Backup uploaded to Google Drive: {zip_full_name}")
            drive.delete_old_files_from_google_drive(google_drive_config["key_dir_drive"], days_old=delete_old_file_days)
        if rc_exists == 4:
            master_rc = rc_exists
        else:
            master_rc = rc
    except Exception as e:
        logging.critical(f"Script failed.")
        logging.critical(f"Error: {e}")
        master_rc = 8
    finally:
        return master_rc, dict_backups

if __name__ == "__main__":
    try:
        date_start = datetime.now()
        rc_main, dict_backups = main()
        data_to_insert = {'script_name' : 'automated-backup', 'data_iniz' : date_start}
        rc_insert = 0
        if postgresql["enabled"]:
            id_elab, rc_insert = clientsql.insert_ret_idelab('elaborazioni', data_to_insert)
        for row in dict_backups.items():
            if postgresql["enabled"]:
                data_to_insert = {'id_elab': id_elab, 'zip_name': row[0], 'size': row[1]}
                rc = clientsql.insert('elaborazioni_size', data_to_insert)
            if rc == 8:
                raise Exception
        rc = rc_main
        if rc == 8 or rc_insert !=0:
            raise Exception
    except Exception as e:
        logging.critical(f"Script failed.")
        rc = '8'
        if postgresql["enabled"]:
            try:
                conditions = {'id_elab': id_elab}
                data = {'esito': rc}
                logging.info("Data sent to DB: " + str(data) + " with conditions: " + str(conditions))
                clientsql.update('elaborazioni', data, conditions)
            except Exception as e:
                logging.critical(f"Script failed: {e}")
                rc = '8'
    finally:
        if postgresql["enabled"]:
            try:
                date_end = datetime.now()
                data = {'data_fine ': date_end, 'esito ': rc}
                conditions = {'id_elab': id_elab}
                clientsql.update('elaborazioni', data, conditions)
            except Exception as e:
                logging.critical(f"Script failed: {e}")
                rc = '8'
            clientsql.close()
        logging.info("Script finished with return code: " + str(rc))
        sys.exit(rc)

