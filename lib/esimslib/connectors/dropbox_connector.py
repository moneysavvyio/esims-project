"""Dropbox Connector to Fetch files."""

import os
import uuid
from functools import wraps
from typing import Callable


from dropbox import Dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import DeleteArg

from esimslib.connectors.aws_connector import SSMConnector as ssm
from esimslib.connectors.constants import DropBoxConst as dbx_c
from esimslib.util.logger import logger


def handle_dpx_error(func: Callable) -> Callable:
    """Decorator to handle Dropbox API and Authentication Exceptions

    Args:
        func (Callable): Function to decorate.

    Returns:
        Callable: Decorated function.
    """

    @wraps(func)
    def inner(*args: tuple, **kwargs: dict) -> object:
        """Handle dropbox exceptions.

        Args:
            args (tuple): arbitrary tuple of arguments.
            kwargs (dict): arbitrary dictionary of keyword arguments.

        Raises:
            ApiError: If API error occured.
            AuthError: If authentication error occured.

        Returns:
            object: Function result.
        """
        try:
            return func(*args, **kwargs)
        except (ApiError, AuthError) as err:
            logger.error("Dropbox API error: %s", err)
            raise err

    return inner


class DropboxConnector:
    """Manage Dropbox CRUD operations."""

    def __init__(self) -> None:
        """Initialize DropboxConnector."""
        self.dbx = Dropbox(ssm().get_parameter(os.getenv(dbx_c.DROPBOX_TOKEN)))

    @handle_dpx_error
    def list_files(self, root_folder: str) -> list:
        """List all files in the root folder.

        Args:
            root_folder (str): Root folder path.
                e.g. /esims-router/data/

        Returns:
            list: list of file paths.
        """
        try:
            files = self.dbx.files_list_folder(root_folder)
            return [entry.path_display for entry in files.entries]
        except ApiError:
            logger.warning("Folder Not Found: %s", root_folder)
            return []

    @handle_dpx_error
    def get_file(self, file_path: str) -> bytes:
        """Get file from Dropbox.

        Args:
            file_path (str): Path to file.

        Returns:
            object: File content.
        """
        metadata, file = self.dbx.files_download(file_path)
        logger.info("Downloaded: %s", metadata.name)
        return file.content

    @handle_dpx_error
    def delete_batch(self, entries: list) -> str:
        """Delete batch of files.

        Args:
            entries (list): List of files pathes.

        Returns:
            str: Delete Job Id
        """
        delete_args = [DeleteArg(path) for path in entries]
        deleted = self.dbx.files_delete_batch(delete_args)
        logger.info("Deleted Files Initiated: %s", len(delete_args))
        return deleted.get_async_job_id()

    @handle_dpx_error
    def check_delete_job_status(self, job_id: str) -> bool:
        """Check delete job status.

        Args:
            job_id (str): Delete Job ID.

        Returns:
            bool: If job finished successfully.
        """
        deleted = self.dbx.files_delete_batch_check(job_id)
        return deleted.is_complete()

    @handle_dpx_error
    def write_files(self, parent_folder: str, urls: list) -> None:
        """Load QR Codes in urls to Dropbox.

        Args:
            parent_folder (str): dropbox file path.
            urls (list): list of QR Codes urls.
        """
        for url in urls:
            file_path = f"{parent_folder}/{uuid.uuid4().hex}.png"
            self.dbx.files_save_url(file_path, url)
