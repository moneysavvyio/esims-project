"""Main Service Driver"""

import os
import time

from esimslib.util import logger
from esimslib.connectors import (
    DropboxConnector,
    S3Connector,
    SSMConnector,
    AirTableConnector,
)
from esims_router.constants import RouterConst as r_c


class LambdaState:
    """Manage Lambda State"""

    def __init__(self) -> None:
        """Initialize LambdaState"""
        self.ssm = SSMConnector()
        self.state_key = os.getenv(r_c.STATE_KEY)

    def get_state(self) -> bool:
        """Get Lambda State parameter in SSM

        Returns:
            bool: Lambda State.
        """
        state = self.ssm.get_parameter(self.state_key)
        return state == r_c.OFF

    def set_state(self) -> None:
        """Set Lambda State parameter in SSM"""
        self.ssm.update_parameter(self.state_key, r_c.ON)
        logger.info("Lambda Status Set.")

    def reset_state(self) -> None:
        """Reset Lambda State parameter in SSM"""
        self.ssm.update_parameter(self.state_key, r_c.OFF)
        logger.info("Lambda Status Reset.")


def fetch_entries() -> dict:
    """Fetch Entries from AirTable

    Returns:
        dict: Entries.
            {id: folder}
    """
    connector = AirTableConnector(os.getenv(r_c.CARRIERS_TABLE_NAME))
    entries = connector.fetch_records()
    return {entry[0]: r_c.DBX_PATH.format(entry[1]) for entry in entries}


def main() -> None:
    """Main Service Driver"""
    logger.info("Starting e-sims transport service")
    entries = fetch_entries()
    # load connectors
    dbx_connector = DropboxConnector()
    s3_connector = S3Connector()
    # iterate over esims
    for sim, folder in entries.items():
        carrier = folder.split("/")[-1]
        logger.info("Processing: %s", carrier)
        path_list = dbx_connector.list_files(folder)
        logger.info("Available Sims %s", len(path_list))
        if not path_list:
            continue

        # fetch dropbox files' content
        objects = [dbx_connector.get_file(path) for path in path_list]
        logger.info("Fetched Sims: %s", len(objects))

        # load objects to S3
        urls = [
            s3_connector.load_data(obj, key)
            for obj, key in zip(objects, path_list)
        ]
        logger.info("S3 Loaded Sims: %s", len(urls))

        # upload to AirTable
        AirTableConnector(
            os.getenv(r_c.ATTACHMENT_TABLE_NAME)
        ).load_attachments(sim, urls)
        logger.info("Uploaded to AirTable: %s", carrier)

        # delete from Dropbox
        job_id = dbx_connector.delete_batch(path_list)
        while not dbx_connector.check_delete_job_status(job_id):
            time.sleep(3)
            logger.info(
                "Waiting for Dropbox delete job to finish...: %s", carrier
            )
        logger.info("Esims Uploaded Successfully: %s", carrier)


# pylint: disable=unused-argument
def handler(event: dict, context: dict) -> None:
    """Lambda Handler

    Args:
        event (dict): lambda trigger event.
        context (dict): lambda event context.

    Raises:
        Exception: if main service failed.
    """
    state = LambdaState()
    if state.get_state():
        try:
            state.set_state()
            main()
            logger.info("Finished main service driver")
            state.reset_state()
        except Exception as exc:
            logger.error("Main Service Driver Error: %s", exc)
            state.reset_state()
            raise exc
    else:
        logger.info("Esims Router already running. Skipping ...")


if __name__ == "__main__":
    main()
