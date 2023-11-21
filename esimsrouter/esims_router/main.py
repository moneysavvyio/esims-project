"""Main Service Driver"""

import json
import os
import time


from esims_router.logger import logger
from esims_router.constants import RouterConst as r_c
from esims_router.dropbox_connector import DropboxConnector
from esims_router.aws_connector import S3Connector, SSMConnector
from esims_router.airtable_connector import AirTableConnector


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


def main() -> None:
    """Main Service Driver"""
    logger.info("Starting e-sims transport service")
    # load connectors
    dbx_connector = DropboxConnector()
    s3_connector = S3Connector()
    airtable_connector = AirTableConnector()
    # load entries data
    entries = json.loads(os.getenv(r_c.ENTRIES))
    # iterate over esims
    for sim, folder in entries.items():
        path_list = dbx_connector.list_files(folder)
        logger.info("Available Sims in Dropbox: %s : %s", sim, len(path_list))
        if not path_list:
            continue
        # fetch dropbox files' content
        objects = [dbx_connector.get_file(path) for path in path_list]
        logger.info("Dropbox Objects Loaded: %s : %s", sim, len(objects))
        # load objects to S3
        urls = [
            s3_connector.load_data(obj, key)
            for obj, key in zip(objects, path_list)
        ]
        logger.info("S3 Objects Loaded: %s : %s", sim, len(urls))
        # upload to AirTable
        airtable_connector.load_attachments(sim, urls)
        # delete from Dropbox
        job_id = dbx_connector.delete_batch(path_list)
        while not dbx_connector.check_delete_job_status(job_id):
            time.sleep(3)
            logger.info("Waiting for Dropbox delete job to finish...: %s", sim)
        logger.info("Esims Uploaded Successfully: %s", sim)
    logger.info("Finished main service driver")


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
            state.reset_state()
        except Exception as exc:
            logger.error("Main Service Driver Error: %s", exc)
            state.reset_state()
            raise exc
    else:
        logger.info("Esims Router already running. Skipping ...")
