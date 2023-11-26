"""AirTable Connector"""

import os
from typing import Generator


from pyairtable import Api
from pyairtable.utils import attachment

from esimslib.connectors.aws_connector import SSMConnector as ssm
from esimslib.connectors.constants import AirTableConst as air_c
from esimslib.util.logger import logger


class AirTableConnector:
    """AirTable Connector"""

    def __init__(self, table_name: str) -> None:
        """Initializes the AirTable Connector

        Args:
            table_name (str): AirTable Table Name
        """
        self.base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        self.table_name = table_name
        self.api = Api(ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY)))
        self.table = self.api.table(self.base_id, self.table_name)

    def fetch_records(self) -> list:
        """Fetch ID, Name from AirTable

        Returns:
            list: list of carriers
                [(id, name)]
        """
        records = self.table.all()
        return [
            (
                record.get(air_c.FIELDS)[air_c.ID],
                record.get(air_c.FIELDS)[air_c.NAME],
            )
            for record in records
        ]

    @staticmethod
    def batch_records(records: list) -> Generator:
        """Batch records to maximum of 10 records in batch

        Args:
            records (list): list of records to be batched

        Yields:
            list: list of batched records
        """
        for i in range(0, len(records), 10):
            yield records[i : i + 10]

    def load_attachments(self, sim: str, urls: list) -> None:
        """Load objects in URLs list to AirTable

        Args:
            sim (str): Sim Provider Id.
            urls (list): URLs of objects to be loaded.

        Raises:
            Exception: if failed to connect to AirTable
        """
        try:
            records = [
                {air_c.SIM: [sim], air_c.ATTACHMENT: [attachment(url)]}
                for url in urls
            ]
            for batch in self.batch_records(records):
                response = self.table.batch_create(batch)
                logger.info(
                    "Uploaded to AirTable: %s : %s", sim, len(response)
                )
        except Exception as exc:
            logger.error("Airtable upload error: %s", exc)
            raise exc
