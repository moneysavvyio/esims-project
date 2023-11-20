"""Dropbox-AirTable Connector"""

import os

from dropbox import Dropbox
from dropbox.exceptions import AuthError
from pyairtable import Api
from pyairtable.utils import attachment

from esims_router.constants import (
    DropBoxConst as dbx_c,
    AirTableConst as air_c,
)
from esims_router.logger import logger

# Dropbox and Airtable credentials
DROPBOX_TOKEN = os.getenv(dbx_c.DROPBOX_TOKEN)
AIRTABLE_API_KEY = os.getenv(dbx_c.AIRTABLE_API_KEY)
AIRTABLE_BASE_ID = os.getenv(dbx_c.AIRTABLE_BASE_ID)
AIRTABLE_TABLE_NAME = os.getenv(dbx_c.AIRTABLE_TABLE_NAME)


def download_file_from_dropbox(dropbox_token: str, file_path: str) -> bool:
    """Download file from dropbox.

    Args:
        dropbox_token (str): Dropbox token.
        file_path (str): download path.

    Returns:
        bool: download status.
    """
    try:
        dbx = Dropbox(dropbox_token)
        metadata, response = dbx.files_download(path=file_path)
        logger.info("File collected: %s", metadata.path_display)
        with open(metadata.name, "wb") as f:
            f.write(response.content)
        return True
    except AuthError as exc:
        logger.error("Dropbox authentication error: %s", exc)
        return False


def upload_to_airtable(
    api_key: str, base_id: str, table_name: str, url: str, sim: str
) -> bool:
    """Upload file to airTable.

    Args:
        api_key (str): AirTable API Key.
        base_id (str): AirTable Base ID.
        table_name (str): AirTable table name.
        url (str): Local file path to upload.
        sim (str): sim field.

    Returns:
        bool: If file uploaded.
    """
    try:
        api = Api(api_key)
        table = api.table(base_id, table_name)
        file = attachment(url)
        response = table.create({air_c.SIM: sim, air_c.ATTACHMENT: [file]})
        logger.info(
            "Uploaded %s",
            response.get(air_c.FIELDS)[air_c.ATTACHMENT][0][air_c.FILENAME],
        )
        return True
    except Exception as exc:
        logger.error("Airtable upload error: %s", exc)
        return False
