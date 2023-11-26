"""Ingest Esims From AirTable to Dropbox"""


from esimslib.util import logger
from esimslib.connectors import AirTableConnector, DropboxConnector

from ingest_esims.constants import IngestSimsConst as in_c


def extract_unique_urls(attachments: list) -> list:
    """Extract unique attachment urls per record.

    Args:
        attachments (list): list of attached QR codes per record.

    Returns:
        list: list of attchment urls.
    """
    filenames = []
    unique_urls = []
    for attachment in attachments:
        filename = attachment.get(in_c.FILE_NAME)
        if not filename in filenames:
            filenames.append(filename)
            unique_urls.append(attachment.get(in_c.URL))
    return unique_urls


def fetch_new_esims() -> list:
    """Fetch newly donated esims.

    Returns:
        list: List of esims.
            [{folder_name, {list of attachments}}]
    """
    connector = AirTableConnector(in_c.TABLE_NAME)
    entries = connector.fetch_all()
    return [
        {
            in_c.TARGET_FOLDER: entry[1].get(in_c.TARGET_FOLDER)[0],
            in_c.ATTACHMENTS: extract_unique_urls(
                entry[1].get(in_c.ATTACHMENTS)
            ),
        }
        for entry in entries
    ]


def consolidate_sim_provider(esims: list) -> dict:
    """Consolidate all esims for the same provider.

    Args:
        esims (list): List of esims.
            [{folder_name}, {list of attachments}]

    Returns:
        dict: Consolidated esims.
            {provider_name: [urls]}

    """
    esims_by_provider = {}
    for esim in esims:
        provider_name = esim.get(in_c.TARGET_FOLDER)
        if not provider_name in esims_by_provider:
            esims_by_provider[provider_name] = []
        esims_by_provider[provider_name].extend(esim.get(in_c.ATTACHMENTS))
    return esims_by_provider


def load_data_to_dbx(esims: dict) -> None:
    """Load QR Codes to Dropbox.

    Args:
        esims (dict): Consolidated esims.
            {provider: [urls]}
    """
    dbx_connector = DropboxConnector()
    for provider, urls in esims.items():
        dbx_connector.write_files(in_c.DBX_PATH.format(provider), urls)
        logger.info("Loaded Donated eSIMs for %s: %s", provider, len(urls))


def main() -> None:
    """Main"""
    logger.info("Ingesting Donated eSIMs.")
    esims = fetch_new_esims()
    logger.info("New Donated eSIMs records: %s", len(esims))
    # TODO: Check if the image contains QR Codes.
    esims_by_provider = consolidate_sim_provider(esims)
    load_data_to_dbx(esims_by_provider)
    # TODO: Update status in AirTable


if __name__ == "__main__":
    main()
