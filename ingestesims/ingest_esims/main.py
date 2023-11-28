"""Ingest Esims From AirTable to Dropbox"""

from esimslib.util import logger
from esimslib.connectors import DropboxConnector
from esimslib.airtable import Donations

from ingest_esims.constants import IngestSimsConst as in_c
from ingest_esims.qr_code_detector import QRCodeDetector


def consolidate_by_provider(records: list) -> dict:
    """Consolidate all esims for the same provider.

    Args:
        records (list): List of Donations Records.

    Returns:
        dict: Consolidated esims.
            {provider_name: [urls]}

    """
    esims_by_provider = {}
    for record in records:
        provider_name = record.esim_provider[0].name
        if not provider_name in esims_by_provider:
            esims_by_provider[provider_name] = []
        esims_by_provider[provider_name].extend(record.extract_urls())
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


def check_qr_code(record: object) -> None:
    """Check if the image contains QR Code.

    Args:
        record (object): Donations record.
    """
    for attachment_ in record.qr_codes:
        detector = QRCodeDetector(attachment_.get(in_c.URL))
        if not detector.detect():
            record.qr_codes.remove(attachment_)


def validate_record(record: object) -> None:
    """Validate Donation Record.
    - Validate attachment is an image.
    - Validate no duplicate file names.
    - Validate images contain QR Code.

    Args:
        record (object): Donations record.
    """
    record.check_attachment_type()
    record.remove_duplicate_files()
    check_qr_code(record)


def main() -> None:
    """Main"""
    logger.info("Ingesting Donated eSIMs.")

    records = Donations.fetch_all()
    logger.info("Donated eSIMs records: %s", len(records))

    list(map(validate_record, records))
    valid_records = [record for record in records if record.qr_codes]
    logger.info("Validated Donated eSIMs records: %s", len(valid_records))

    esims_by_provider = consolidate_by_provider(valid_records)
    load_data_to_dbx(esims_by_provider)
    # # TODO: Update status in AirTable


if __name__ == "__main__":
    main()
