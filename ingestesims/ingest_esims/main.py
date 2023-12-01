"""Ingest Esims From AirTable to Dropbox"""

from copy import deepcopy

from esimslib.util import logger
from esimslib.connectors import DropboxConnector
from esimslib.airtable import Donations

from ingest_esims.constants import IngestSimsConst as in_c
from ingest_esims.validate_donation import ValidateDonation


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


def load_data_to_dbx(esims: dict) -> int:
    """Load QR Codes to Dropbox.

    Args:
        esims (dict): Consolidated esims.
            {provider: [urls]}

    Returns:
        int: total count of QR Codes loaded
    """
    total_count = 0
    dbx_connector = DropboxConnector()
    for provider, urls in esims.items():
        dbx_connector.write_files(in_c.DBX_PATH.format(provider), urls)
        total_count += len(urls)
        logger.info("Loaded Donated eSIMs for %s: %s", provider, len(urls))
    return total_count


def validate_record(record: object) -> None:
    """Validate Donation Record.
    - Validate attachment is an image.
    - Validate no duplicate file names.
    - Validate images contain QR Code.

    Args:
        record (object): Donations record.
    """
    validator = ValidateDonation(record)
    validator.validate_attachment_type()
    validator.validate_duplicate_files()
    validator.validate_qr_code()


def update_donations_status(valid_records: list, server_records: list) -> None:
    """Update donation record status after validation.

    Args:
        valid_records (list): List of valid donation records.
        server_records (list): List of server donation records.
    """
    valid_ids = {record.id for record in valid_records}
    for record in server_records:
        if record.id in valid_ids:
            record.set_in_use()
        else:
            record.set_donor_error()


def main() -> None:
    """Main"""
    logger.info("Ingesting Donated eSIMs.")

    server_records = Donations.fetch_all()
    records = deepcopy(server_records)
    logger.info("Donated eSIMs records: %s", len(records))

    list(map(validate_record, records))
    valid_records = [record for record in records if record.qr_codes]
    logger.info("Validated Donated eSIMs records: %s", len(valid_records))

    esims_by_provider = consolidate_by_provider(valid_records)
    loaded = load_data_to_dbx(esims_by_provider)
    logger.info("Loaded QR Codes to Dropbox: %s", loaded)

    update_donations_status(valid_records, server_records)
    Donations.batch_save(server_records)
    logger.info("Donated eSIMs Ingested.")


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
    except Exception as exc:
        logger.error("Ingest eSIMs Router Error: %s", exc)
        raise exc


if __name__ == "__main__":
    main()
