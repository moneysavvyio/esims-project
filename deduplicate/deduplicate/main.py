"""Deduplicate Esims Linked"""

from typing import List, Dict

from esimslib.util import logger
from esimslib.airtable import EsimAsset, EsimDonation


def group_duplicates_by_original(
    esims: List[EsimAsset],
) -> Dict[EsimAsset, List[EsimAsset]]:
    """Group duplicate esims for each original.

    Args:
        esims (List[EsimAsset]): list of esim records.

    Returns:
        Dict[EsimAsset, List[EsimAsset]]: combined duplicates {qr_sha: esims}.
    """
    return {
        esim: [
            esim_duplicate
            for esim_duplicate in esims
            if esim_duplicate.qr_sha == esim.qr_sha
            and not esim_duplicate.checked_in
        ]
        for esim in esims
        if esim.checked_in
    }


def mark_duplicate_donation(
    original_esim: EsimAsset,
    esim_duplicates: List[EsimAsset],
) -> None:
    """flag duplicate donation and link to original.

    Args:
        original_esim (EsimAsset): original esim.
        esim_duplicates (List[EsimAsset]): list of duplicate attachments.
    """
    duplicate_donations = [
        duplicate.donation
        for duplicate in esim_duplicates
        if duplicate.donation
    ]
    for duplicate_donation in duplicate_donations:
        if duplicate_donation != original_esim.donation:
            duplicate_donation.is_duplicate = True
            duplicate_donation.duplicate_original = original_esim.donation
    EsimDonation.batch_save(duplicate_donations)


def main() -> None:
    """Main"""
    duplicated_esims = EsimAsset().fetch_all()
    logger.info("Duplicate esims: %s", len(duplicated_esims))

    combined_duplicates = group_duplicates_by_original(duplicated_esims)
    # pylint: disable=expression-not-assigned
    [
        mark_duplicate_donation(  # type: ignore[func-returns-value]
            original,
            duplicates,
        )
        for original, duplicates in combined_duplicates.items()
    ]
    list(map(EsimAsset.batch_delete, combined_duplicates.values()))

    logger.info(
        "Deduplicated esims: %s",
        len(duplicated_esims) - len(combined_duplicates),
    )


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
