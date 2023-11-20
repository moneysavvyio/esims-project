"""AirTable Connector to load Attachments to AirTable"""

import os

from pyairtable import Api
from pyairtable.utils import attachment

from esims_router.constants import AirTableConst as air_c
from esims_router.logger import logger


class AirTableConnector:
    """AirTable Connector to load Attachments to AirTable"""

    def __init__(self) -> None:
        """Initializes the AirTable Connector"""
        self.base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        self.table_name = os.getenv(air_c.AIRTABLE_TABLE_NAME)
        self.api = Api(os.getenv(air_c.AIRTABLE_API_KEY))
        self.table = self.api.table(self.base_id, self.table_name)

    def load_attachments(self, sim: str, urls: list) -> None:
        """Load objects in URLs list to AirTable

        Args:
            sim (str): Sim Provider.
            urls (list): URLs of objects to be loaded.
        """
        try:
            records = [
                {air_c.SIM: sim, air_c.ATTACHMENT: [attachment(url)]}
                for url in urls
            ]
            response = self.table.batch_create(records)
            logger.info("Uploaded to AirTable: %s : %s", sim, len(response))
        except Exception as exc:
            logger.error("Airtable upload error: %s", exc)
