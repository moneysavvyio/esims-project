"""Read Esim Phone Numbers of renewable esims"""

from esimslib.util import logger, ImagePhoneNumberReader
from esimslib.airtable import  Attachments

from esim_number.constants import EsimNumberConst as esn_c

def load_data_to_airtable(renewable_esims: list) -> int:
    """Load esims to Airtable.

    Args:
        renewable_esims (list): List of renewable esims.

    Returns:
        int: total count of esims loaded
    """
    Attachments.load_records(renewable_esims)
    return len(renewable_esims)


def main() -> None:
    """Main Service Driver"""

    esim_records = Attachments().fetch_renewable()
    logger.info("Starting renewable esims phone number reading")

    # iterate over esim attachments
    for esim_record in esim_records:
        logger.info("Processing: %s", esim_record)

        esim_phone_number = ""
        esim_phone_number_error = False
        for attachment_ in esim_record.qr_codes:
            phone_number_reader = ImagePhoneNumberReader(attachment_.get(esn_c.URL))
            if phone_number_reader.read_phone_number():
                esim_phone_number = phone_number_reader.phone_number
            else:
                esim_phone_number_error = True

        esim_record.esim_phone_number = esim_phone_number
        esim_record.esim_phone_number_error = esim_phone_number_error

    # upload to AirTable
    load_data_to_airtable(esim_records)
    logger.info("Uploaded to AirTable: %s", esim_records)


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
        logger.error("eSIM Phone Number Service Error: %s", exc)
        raise exc


if __name__ == "__main__":
    main()
