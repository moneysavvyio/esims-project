"""Ingest Esims From AirTable to Dropbox"""

from typing import List

from esimslib.util import logger
from esimslib.airtable import EsimDonation, EsimAsset

from ingest_esims.validate_donation import ValidateDonation


def validate_donation(donation_record: EsimDonation) -> List[EsimAsset]:
    """Validate Donation Record.

    Args:
        donation_record (EsimDonation): EsimDonation record.

    Returns:
        List[EsimAsset]: Validated eSIMs.
    """
    validator = ValidateDonation(donation_record)
    validator.validate_attachments_type()
    validator.validate_attachments_qr_code()
    validator.deduplicate_attachments()
    if validator.rejected:
        donation_record.is_rejected = True
        donation_record.send_error_email = True
    donation_record.is_ingested = True
    return validator.valid_esims


def main() -> None:
    """Main"""
    logger.info("Ingesting Donated eSIMs.")

    new_donations = EsimDonation.fetch_all()
    logger.info("Donated eSIMs records: %s", len(new_donations))
    logger.info(
        "Total number of Attachments in records: %s",
        sum(len(donation.qr_codes_att) for donation in new_donations),
    )

    valid_esims_by_donation = list(
        filter(None, map(validate_donation, new_donations))
    )
    all_valid_esims = [
        esim for esims in valid_esims_by_donation for esim in esims
    ]
    logger.info("Validated Donated eSIMs: %s", len(all_valid_esims))

    EsimAsset.load_records(all_valid_esims)
    logger.info("QR Codes Loaded to Airtable")
    EsimDonation.load_records(new_donations)
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
