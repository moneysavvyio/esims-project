"""Deduplicate Esims Linked"""

from esimslib.util import logger
from esimslib.airtable import Attachments, Donations

from deduplicate.constants import DuplicateConst as dp_c


def combine_duplicated_records(records: list) -> dict:
    """Combine duplicated records

    Args:
        records (list): list of records.

    Returns:
        dict: combined records {SHA: records}.
    """
    combined_records = {}
    for record in records:
        if record.qr_sha in combined_records:
            combined_records[record.qr_sha].append(record)
        else:
            combined_records[record.qr_sha] = [record]
    return combined_records


def _update_duplicate_donation_info(
    original: Attachments, duplicates: list
) -> None:
    """Update duplicate donation info

    Args:
        original (Donations): original attachment record.
        duplicates (list): list of duplicate attachments.
    """
    original_donation = original.donor[0] if original.donor else None
    duplicate_donations = [
        duplicate.donor[0] for duplicate in duplicates if duplicate.donor
    ]
    for duplicate_donation in duplicate_donations:
        duplicate_donation.set_duplicate_error()
        if original_donation:
            duplicate_donation.set_original_donor(original_donation)
            if (
                not duplicate_donation.email.lower()
                == original_donation.email.lower()
            ):
                duplicate_donation.set_different_email()
        else:
            duplicate_donation.set_different_email()
    Donations.batch_save(duplicate_donations)


def delete_duplicate(records: list) -> None:
    """Delete duplicate records

    Args:
        records (list): list of records.
    """
    # sort records chronologically
    if dp_c.MEEDAN in records[0].esim_provider[0].name:
        records.sort(key=lambda record: record.order_id, reverse=True)
    else:
        records.sort(key=lambda record: record.order_id, reverse=False)
    original, duplicates = records[0], records[1:]
    # delete duplicates
    Attachments.batch_delete(duplicates)
    # update donation info
    _update_duplicate_donation_info(original, duplicates)


def main() -> None:
    """Main"""
    records = Attachments().fetch_all()
    logger.info("Duplicate records: %s", len(records))

    duplicates = combine_duplicated_records(records)

    list(map(delete_duplicate, duplicates.values()))

    logger.info("Deduplicated records: %s", len(records) - len(duplicates))


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
        logger.error("Deduplicate eSIMs Service Error: %s", exc)
        raise exc


if __name__ == "__main__":
    main()
