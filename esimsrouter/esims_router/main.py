"""Main Service Driver"""

import json
import os
import time


from esims_router.logger import logger
from esims_router.constants import RouterConst as r_c
from esims_router.dropbox_connector import DropboxConnector
from esims_router.aws_connector import S3Connector, SQSConnector
from esims_router.airtable_connector import AirTableConnector


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
    try:
        main()
        logger.info("Passing on to the next iteration...")
        SQSConnector().publish({"invoke": "lambda"})
        time.sleep(10)
    except Exception as exc:
        logger.error("Main Service Driver Error: %s", exc)
        raise exc
