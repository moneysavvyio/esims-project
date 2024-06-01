"""Main Service Driver"""

import os
import time

from functools import partial

from esimslib.util import logger, QRCodeDetector, ImagePhoneNumberReader
from esimslib.airtable import Providers, Attachments
from esimslib.connectors import (
    DropboxConnector,
    S3Connector,
    SSMConnector,
)
from esims_router.constants import RouterConst as r_c


class LambdaState:
    """Manage Lambda State"""

    def __init__(self) -> None:
        """Initialize LambdaState"""
        self.ssm = SSMConnector()
        self.state_key = os.getenv(r_c.STATE_KEY)

    def get_state(self) -> bool:
        """Get Lambda State parameter in SSM

        Returns:
            bool: Lambda State.
        """
        state = self.ssm.get_parameter(self.state_key)
        return state == r_c.OFF

    def set_state(self, count: int) -> None:
        """Set Lambda State parameter in SSM

        Args:
            count (int): Lambda State count.
        """
        self.ssm.update_parameter(self.state_key, r_c.ON.format(count=count))
        logger.info("Lambda Status Set.")

    def audit_state(self) -> None:
        """Audit current state if state is ON.
        - Increment by 1 if < 15.
        - Set to Off if > 15.
        """
        current_state = self.ssm.get_parameter(self.state_key)
        if current_state == r_c.OFF:
            return
        count = int(current_state.split(r_c.DELIMITER)[1])
        if count < r_c.MAX_COUNT:
            count += 1
            self.set_state(count)
        else:
            self.reset_state()

    def reset_state(self) -> None:
        """Reset Lambda State parameter in SSM"""
        self.ssm.update_parameter(self.state_key, r_c.OFF)
        logger.info("Lambda Status Reset.")


# TODO: Add esim phone number here
def load_data_to_airtable(provider_id: str, records: list) -> None:
    """Load data to AirTable

    Args:
        provider_id (str): Provider ID.
        records (list): List of QR Codes URLs and Shas (url, sha).
    """
    attachments = [
        Attachments(
            esim_provider=Attachments.format_esim_provider_field(provider_id),
            attachment=Attachments.format_attachment_field(url),
            qr_sha=sha,
            esim_phone_number=phone_number,
            esim_phone_number_error=is_phone_number_error
        )
        for url, sha, phone_number, is_phone_number_error in records
    ]
    Attachments.load_records(attachments)


def validate_file_type(file_path: str) -> bool:
    """Validate file type

    Args:
        file_path (str): Dropbox file path.

    Returns:
        bool: True if file is an image.
    """
    if any(
        file_path.endswith(image_type)
        for image_type in r_c.ACCEPTED_IMAGE_TYPES
    ):
        return True
    return False


def  validate_qr_code(qr_text: list, url: str) -> str:
    """Validate QR Code.
        - Checks QR code present.
        - Checks QR data matches provider.

    Args:
        qr_text (str): Provider's expected domain.
        url (str): QR Code URL.

    Returns:
        str: SHA256 hash of the QR Code.
    """
    detector = QRCodeDetector(url)
    if detector.detect():
        if detector.qr_code.startswith(r_c.LPA):
            if any(v in detector.qr_code for v in qr_text):
                return detector.qr_sha
    return ""

def read_phone_number_from_image(url: str) -> str:
    """Read phone Number from image URL if possible


    Args:
        url (str): QR Code URL.

    Returns:
        str: phone number listed in the QR code text, if any. Empty string if no matching phone number found.
    """
    phone_number_reader = ImagePhoneNumberReader(url)
    if phone_number_reader.read_phone_number():
        return phone_number_reader.phone_number
    return ""

def main() -> None:
    """Main Service Driver"""
    logger.info("Starting e-sims transport service")
    records = Providers.fetch_all()
    # load connectors
    dbx_connector = DropboxConnector()
    s3_connector = S3Connector()
    # iterate over esims
    for record in records:
        logger.info("Processing: %s", record.name)

        folder = r_c.DBX_PATH.format(record.name)
        path_list = dbx_connector.list_files(folder)
        logger.info("Available Sims %s", len(path_list))

        if not path_list:
            continue

        # validate file types
        valid_list = list(filter(validate_file_type, path_list))

        # fetch dropbox files' content
        objects = [dbx_connector.get_file(path) for path in valid_list]
        logger.info("Fetched Sims: %s", len(objects))

        # load objects to S3
        urls = [
            s3_connector.load_data(obj, key)
            for obj, key in zip(objects, valid_list)
        ]
        logger.info("S3 Loaded Sims: %s", len(urls))

        # validate qr codes
        partial_validate_qr_code = partial(
            validate_qr_code, record.qr_text or [""]
        )
        valid_qrs = list(map(partial_validate_qr_code, urls))
        valid_records = [
            (url, sha) for url, sha in zip(urls, valid_qrs) if sha
        ]
        logger.info("Valid Sims: %s", len(valid_records))

        # Read esim phone number for renewable sims
        processed_records = [
            (
                url,
                sha,
                phone_number if record.renewable else None,
                not phone_number if record.renewable else False
            )
            for url, sha in valid_records
            for phone_number in [read_phone_number_from_image(url) if record.renewable else ""]
        ]

        # upload to AirTable
        load_data_to_airtable(record.id, processed_records)
        logger.info("Uploaded to AirTable: %s", record.name)

        # delete from Dropbox
        valid_list = [valid_list[i] for i, sha in enumerate(valid_qrs) if sha]

        job_id = dbx_connector.delete_batch(valid_list)
        while not dbx_connector.check_delete_job_status(job_id):
            time.sleep(3)
            logger.info(
                "Waiting for Dropbox delete job to finish...: %s", record.name
            )

        # Check if invalid
        invalid_list = bool(set(path_list) - set(valid_list))
        if invalid_list:
            record.set_stock_err()
        else:
            record.reset_stock_err()
        logger.info("Esims Uploaded Successfully: %s", record.name)


# pylint: disable=unused-argument
def handler(event: dict, context: dict) -> None:
    """Lambda Handler

    Args:
        event (dict): lambda trigger event.
        context (dict): lambda event context.

    Raises:
        Exception: if main service failed.
    """
    state = LambdaState()
    if state.get_state():
        try:
            state.set_state(0)
            main()
            logger.info("Finished main service driver")
            state.reset_state()
        except Exception as exc:
            logger.error("Main Service Driver Error: %s", exc)
            state.reset_state()
            raise exc
    else:
        state.audit_state()
        logger.info("Esims Router already running. Skipping ...")


if __name__ == "__main__":
    main()
