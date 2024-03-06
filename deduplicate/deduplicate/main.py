"""Deduplicate Esims Linked"""

from esimslib.util import logger
from esimslib.airtable import Attachments


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


def delete_duplicate(records: list) -> None:
    """Delete duplicate records

    Args:
        records (list): list of records.
    """
    records.sort(key=lambda record: record.order_id)
    if len(records) == 1:
        records.append(records[0])
    Attachments.batch_delete(records[1:])


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
