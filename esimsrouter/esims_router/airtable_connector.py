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

    def load_attachments(self, sim: str, url: str) -> None:
        """Load object in URL to AirTable

        Args:
            sim (str): Sim Provider.
            url (str): URL of object to be loaded.
        """
        try:
            code = attachment(url)
            response = self.table.create(
                {air_c.SIM: sim, air_c.ATTACHMENT: [code]}
            )
            logger.info(
                "Uploaded: %s",
                response.get(air_c.FIELDS)[air_c.ATTACHMENT][0][
                    air_c.FILENAME
                ],
            )
        except Exception as exc:
            logger.error("Airtable upload error: %s", exc)
