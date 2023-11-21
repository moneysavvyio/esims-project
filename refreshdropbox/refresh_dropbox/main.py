"""Refresh Dropbox Token"""

import os
import requests

from refresh_dropbox.logger import logger
from refresh_dropbox.aws_connector import SSMConnector
from refresh_dropbox.constants import (
    RefreshConst as ref_c,
    RequestConst as req_c,
)


def main() -> None:
    """Refresh Dropbox Token"""
    logger.info("Refreshing Dropbox Token.")
    ssm = SSMConnector()
    data = {
        req_c.REFRESH_TOKEN: ssm.get_parameter(os.getenv(ref_c.REFRESH_TOKEN)),
        req_c.GRANT_TYPE: req_c.REFRESH_TOKEN,
        req_c.CLIENT_ID: ssm.get_parameter(os.getenv(ref_c.APP_KEY)),
        req_c.CLIENT_SECRET: ssm.get_parameter(os.getenv(ref_c.APP_SECRET)),
    }
    response = requests.post(req_c.REFRESH_URL, data=data, timeout=60)
    access_token = response.json()[req_c.ACCESS_TOKEN]
    logger.info("Dropbox Token fetched.")
    ssm.update_parameter(os.getenv(ref_c.DROPBOX_TOKEN), access_token)
    logger.info("Dropbox Token updated.")


# pylint: disable=unused-argument
def handler(event: dict, context: dict) -> None:
    """Lambda Handler

    Args:
        event (dict): Lambda event
        context (dict): Lambda context

    Raises:
        Exception: Exception raised if refresh token fails
    """
    try:
        main()
    except Exception as exc:
        logger.error("Refreshing Token Failed: %s", exc)
        raise exc


if __name__ == "__main__":
    main()
