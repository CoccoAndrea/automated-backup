import os
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery_cache.base import Cache

# Define the scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

# Custom class to disable caching
class NoCache(Cache):
    def get(self, url):
        return None

    def set(self, url, content):
        pass
class GoogleDriveManager:
    def __init__(self, credential_path):
        """
        Constructor for the GoogleDriveManager class.

        Args:
            credential_path (str): Path to the directory containing credentials.json and token.json.
        """
        logger.info("Creating Google Drive manager...")
        self.credential_path = credential_path
        self.credentials_file = os.path.join(credential_path, 'credentials.json')
        self.token_file = os.path.join(credential_path, 'token.json')


    def authenticate_google_drive(self):
        """
        Authenticate the user with Google Drive using OAuth2.

        Returns:
            Credentials: The authenticated credentials object.
        """
        logger.info("Authenticating with Google Drive...")
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If credentials are not valid or missing, perform OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for future use
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        return creds

    def file_exists_on_drive(self, service, file_name, folder_id=None):
        """
        Check if a file with the specified name exists in Google Drive.

        Args:
            service: Google Drive API service instance.
            file_name (str): Name of the file to search for.
            folder_id (str): ID of the folder to search in (optional).

        Returns:
            bool: True if the file exists, False otherwise.
        """
        query = f"name = '{file_name}'"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = service.files().list(
            q=query,
            spaces='drive',
            fields="files(id, name)",
            pageSize=10
        ).execute()

        files = results.get('files', [])
        return len(files) > 0

    def upload_to_google_drive(self, file_path, file_name=None, folder_id=None):
        """
        Upload a file to Google Drive.

        Args:
            file_path (str): Path to the file to be uploaded.
            file_name (str): Name of the file on Google Drive (optional).
            folder_id (str): ID of the folder to upload the file to (optional).

        Returns:
            int: Status code (0 for success, 100 if file exists, 8 for errors).
        """
        try:
            creds = self.authenticate_google_drive()
            service = build('drive', 'v3', credentials=creds, cache=NoCache())

            file_name = file_name or os.path.basename(file_path)
            logger.info(f"Analyzing file for upload: {file_name}")

            if self.file_exists_on_drive(service, file_name, folder_id):
                logger.warning("Upload canceled: File already exists.")
                return 100

            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(file_path, resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, webContentLink, webViewLink'
            ).execute()

            logger.info(f"File uploaded successfully: {file.get('name')}")
            return 0
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return 8

    def delete_old_files_from_google_drive(self, folder_id, days_old=30):
        """
        Delete files older than a specified number of days from a Google Drive folder.

        Args:
            folder_id (str): ID of the folder to clean.
            days_old (int): Number of days to retain files.
        """
        try:
            creds = self.authenticate_google_drive()
            service = build('drive', 'v3', credentials=creds, cache=NoCache())

            # Calculate the threshold date
            threshold_date = datetime.now() - timedelta(days=days_old)

            # List all files in the specified folder
            query = f"'{folder_id}' in parents and name contains '.zip'"
            results = service.files().list(
                q=query,
                spaces='drive',
                fields="files(id, name)",
                pageSize=200
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} files in folder {folder_id}")

            # Filtra i file per includere solo quelli con estensione .zip
            zip_files = [file for file in files if file.get('name', '').endswith('.zip')]

            for file in zip_files:
                file_id = file.get('id')
                file_name = file.get('name')

                # Extract the date from the file name (assuming format `backup_YYYYMMDD_HHMMSS.zip`)
                try:
                    date_str = file_name.split('_')[1]
                    date = datetime.strptime(date_str, "%Y%m%d")
                except (IndexError, ValueError) as e:
                    logger.warning(f"Unable to extract date from file name {file_name}: {e}")
                    continue

                # Compare the file date with the threshold date
                if date < threshold_date:
                    service.files().delete(fileId=file_id).execute()
                    logger.info(f"File deleted: {file_name}")
                else:
                    logger.info(f"File retained: {file_name}")

        except Exception as e:
            logger.error(f"Error deleting files: {e}")

