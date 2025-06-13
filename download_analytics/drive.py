"""Functions to upload to and download from google drive."""

import json
import logging
import os
import pathlib
import tempfile

import yaml
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
PYDRIVE_CREDENTIALS = 'PYDRIVE_CREDENTIALS'

LOGGER = logging.getLogger(__name__)


def is_drive_path(path):
    """Tell if the drive is a Google Drive path or not."""
    return path.startswith('gdrive://')


def split_drive_path(path):
    """Extract the folder and filename from the google drive path string."""
    assert is_drive_path(path), f'{path} is not a google drive path'
    folder, filename = path[9:].split('/')

    return folder, filename


def _get_drive_client():
    tmp_credentials = os.getenv(PYDRIVE_CREDENTIALS)
    if not tmp_credentials:
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
    else:
        with tempfile.TemporaryDirectory() as tempdir:
            credentials_file_path = pathlib.Path(tempdir) / 'credentials.json'
            credentials_file_path.write_text(tmp_credentials)

            credentials = json.loads(tmp_credentials)

            settings = {
                'client_config_backend': 'settings',
                'client_config': {
                    'client_id': credentials['client_id'],
                    'client_secret': credentials['client_secret'],
                },
                'save_credentials': True,
                'save_credentials_backend': 'file',
                'save_credentials_file': str(credentials_file_path),
                'get_refresh_token': True,
            }
            settings_file = pathlib.Path(tempdir) / 'settings.yaml'
            settings_file.write_text(yaml.safe_dump(settings))

            gauth = GoogleAuth(str(settings_file))
            gauth.LocalWebserverAuth()

    return GoogleDrive(gauth)


def _find_file(drive, filename, folder):
    query = {'q': f"'{folder}' in parents and trashed=false"}
    files = drive.ListFile(query).GetList()
    for found_file in files:
        if filename == found_file['title']:
            return found_file

    raise FileNotFoundError(f"File '{filename}' not found in Google Drive folder {folder}")


def upload(content, filename, folder, convert=False):
    """Upload a file to google drive.

    Args:
        content (BytesIO):
            Content of the spredsheet, passed as a BytesIO object.
        filename (str):
            Name of the spreadsheet to create.
        folder (str):
            Id of the Google Drive Folder where the spreadshee must be created.
        convert (bool):
            Whether to attempt to convert the file into a Google Docs format.
    """
    drive = _get_drive_client()

    try:
        drive_file = _find_file(drive, filename, folder)
    except FileNotFoundError:
        file_config = {
            'title': filename,
            'parents': [{'id': folder}],
        }
        drive_file = drive.CreateFile(file_config)

    drive_file.content = content
    drive_file.Upload({'convert': convert})
    LOGGER.info('Uploaded file %s', drive_file.metadata['alternateLink'])


def download(folder, filename, xlsx=False):
    """Download a file from google drive.

    Args:
        folder (str):
            Id of the Google Drive Folder where the spreadshee must be created.
        filename (str):
            Name of the spreadsheet to create.

    Returns:
        BytesIO:
            BytesIO object with the contents of the spreadsheet.
            If the file is not found, returns None

    Raises:
        FileNotFoundError:
            If the file does not exist in the indicated folder.
    """
    drive = _get_drive_client()

    drive_file = _find_file(drive, filename, folder)
    if xlsx:
        drive_file.FetchContent(mimetype=XLSX_MIMETYPE)
    else:
        drive_file.FetchContent()

    return drive_file.content
