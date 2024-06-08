"""Main Service Driver"""

import os
import time

from functools import partial


from esimslib.util import logger, QRCodeDetector, ImageWithCaption
from esimslib.airtable import (
    Providers,
    Attachments,
    Inventory
)
from esimslib.connectors import (
    DropboxConnector,
    S3Connector,
    SSMConnector,
    LayanConnector
)
from io import BytesIO
from typing import (
    List,
    Dict,
    Any
)
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        )
        for url, sha in records
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


def validate_qr_code(qr_text: list, url: str) -> str:
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

def create_captioned_esim(esim: Dict[str, str], provider_networks: List[str], provider_gb: int, provider_days_valid: int) -> BytesIO:
    """Takes an esim object and creates a captioned QR code image

    Args:
        esim (Dict[str, str]): esim dict with the schema {"qr_code": URL_str, "phone_number": str}    
        provider_networks 

    Returns:
        BytesIO: Image Bytes object of the captioned image
    """
    qr_code_url = esim.get("qr_code")
    phone_number = esim.get("phone_number")


    networks_str = ", ".join(provider_networks)
    title = f"الشبكة: {networks_str}"

    text_line_1 = f'رقم الهاتف:  {phone_number}'
    text_line_2 = f'المساحة: {provider_gb} جيجا'
    text_line_3 = f'مدة الصلاحية: {provider_days_valid} يوم'

    # Create the captioned image
    image_creator = ImageWithCaption(qr_code_url, title, text_line_1, text_line_2, text_line_3)
    captioned_esim = image_creator.create_image()

    return {
        "phone_number": phone_number,
        "qr_code": captioned_esim
    }

def batch_issue_esims_with_captioned_qr_codes(layan_client: LayanConnector, provider_name: str, provider_networks: List[str], provider_gb: int,
                                              provider_days_valid: int, quantity: int) -> List[Dict[str, Any]]:
    """Issues Layan-T esims of the specified quantity. This makes a number of concurrent calls to the Layan-T API
    and does not guarantee exactly as many results as the specified quantity, but a close approximation.

    Args:
        layan_client (LayanConnector): The instance of the authenticated Layan-Client to issue eSIMs with
        package_name (str): The name of the restockable package to issue esims for. (currently supports WeCom_500GB_30Days_Israel and HotMobile_110GB_30Days_Israel)
        quantity (int): The amount of esims to issue

    Returns:
        List[Dict[str, Any]]: List of captioned eSIM JSON objects with the schema
        [
            {
            "phone_number": str,
            "qr_code": BytesIO Image Object
            }
        ]
    """
    esims_data = layan_client.batch_issue_esims(
        package_name=provider_name,
        target_count=quantity
    )
    
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_sim = {executor.submit(create_captioned_esim, esim, provider_networks, provider_gb, provider_days_valid): esim for esim in esims_data}
        for future in as_completed(future_to_sim):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f"An error occurred: {exc}")
    
    return results


def main() -> None:
    """Main Service Driver"""
    logger.info("Starting e-sims transport service")
    providers = Providers.fetch_all()
    # load connectors
    dbx_connector = DropboxConnector()
    s3_connector = S3Connector()

    layan_connector = LayanConnector()
    # iterate over esims
    for provider in providers:
        logger.info("Processing: %s", provider.name)

        folder = r_c.DBX_PATH.format(provider.name)
        path_list = dbx_connector.list_files(folder)
        logger.info("Available Sims %s", len(path_list))

        if not path_list:
            continue

        # validate file types
        valid_list = list(filter(validate_file_type, path_list))

        # fetch dropbox files' content
        objects = [dbx_connector.get_file(path) for path in valid_list]
        logger.info("Fetched Sims: %s", len(objects))


        # TODO: Review this
        # Automatic restocking logic

        # If this is a restockable esims provider (Hot and wecom atm), and the inventory is low, then
        # batch request 50 esims, and generate the captioned QR code for each one


        automatic_restock_esims = []
        # TODO: Make this more concise
        restocking_conditions = provider.name == "HotMobile_110GB_30Days_Israel" and Inventory.hotmobile_inventory().low_flag and Inventory.hotmobile_inventory().automatic_restock_flag or \
        provider.name == "WeCom_500GB_30Days_Israel" and Inventory.wecom_inventory().low_flag and Inventory.wecom_inventory().automatic_restock_flag 

        if restocking_conditions:
            # TODO: Check if current inventory + len(objects) is less than the low inventory threshold 
            # (question: may this cause a cycle if invalid QR codes remain in the Dropbox and get reloaded in future runs?)
            if len(objects) < 20:
                issued_esims = batch_issue_esims_with_captioned_qr_codes(
                    layan_client=layan_connector,
                    package_name=provider.name,
                    # TODO: Change this to 50+ when it is confirmed working
                    quantity=1
                    
                    )
                if issued_esims:
                    automatic_restock_esims.append(issued_esims)

        # Load each of the generated and captioned images into the S3 bucket
        restocked_esim_urls = [
            s3_connector.load_data(data=esim.get("qr_code"), key=f"{provider.name}esim_{esim.get("phone_number")}.png")
            for esim in automatic_restock_esims
        ]

        # load dropbox objects to the S3 bucket
        dropbox_esim_urls = [
            s3_connector.load_data(obj, key)
            for obj, key in zip(objects, valid_list)
        ]

        all_esim_urls = restocked_esim_urls + dropbox_esim_urls
        logger.info("S3 Loaded Sims: %s", len(all_esim_urls))

        # validate qr codes
        partial_validate_qr_code = partial(
            validate_qr_code, provider.qr_text or [""]
        )
        valid_qrs = list(map(partial_validate_qr_code, all_esim_urls))
        valid_records = [
            (url, sha) for url, sha in zip(all_esim_urls, valid_qrs) if sha
        ]
        logger.info("Valid Sims: %s", len(valid_records))

        # upload to AirTable
        load_data_to_airtable(provider.id, valid_records)
        logger.info("Uploaded to AirTable: %s", provider.name)

        # delete from Dropbox
        valid_list = [valid_list[i] for i, sha in enumerate(valid_qrs) if sha]

        job_id = dbx_connector.delete_batch(valid_list)
        while not dbx_connector.check_delete_job_status(job_id):
            time.sleep(3)
            logger.info(
                "Waiting for Dropbox delete job to finish...: %s", provider.name
            )

        # Check if invalid
        invalid_list = bool(set(path_list) - set(valid_list))
        if invalid_list:
            provider.set_stock_err()
        else:
            provider.reset_stock_err()
        logger.info("Esims Uploaded Successfully: %s", provider.name)


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
