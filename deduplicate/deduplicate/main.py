"""Deduplicate Esims Linked"""

from esimslib.util import logger
from esimslib.airtable import Attachments, Donations

from deduplicate.constants import DuplicateConst as d_c


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
    original: Donations, duplicates: list
) -> None:
    """Update duplicate donation info

    Args:
        original (Donations): original record.
        duplicates (list): list of duplicates.
    """
    for duplicate in duplicates:
        duplicate.set_duplicate_error()
        duplicate.set_original_donor(original)
        if not duplicate.email.lower() == original.email.lower():
            duplicate.set_different_email()
    Donations.batch_save(duplicates)


def delete_duplicate(records: list) -> None:
    """Delete duplicate records

    Args:
        records (list): list of records.
    """
    # sort records chronologically
    records.sort(key=lambda record: record.order_id)
    # if original record misses the donor.
    if len(records) == 1:
        records.append(records[0])
        records[0].donor[0].email = d_c.DEFAULT_EMAIL
    original, duplicates = records[0], records[1:]
    # delete duplicates
    Attachments.batch_delete(duplicates)
    # update donation info
    _update_duplicate_donation_info(
        original.donor[0], [duplicate.donor[0] for duplicate in duplicates]
    )


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
