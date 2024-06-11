"""Main Service Driver"""

import os
import time

from typing import List
from functools import partial

from esimslib.util import logger, QRCodeProcessor
from esimslib.airtable import EsimPackage, EsimAsset
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


def validate_qr_asset(esim_package: EsimPackage, image_url: str) -> EsimAsset:
    """Validate QR Asset.

    Args:
        esim_package (EsimPackage): eSIM Package.
        image_url (str): QR Code image URL.

    Returns:
        EsimAsset | None: eSIM Asset if valid.
    """
    new_asset = EsimAsset()
    new_asset.esim_package = esim_package
    new_asset.qr_code_image = image_url
    processor = QRCodeProcessor(image_url)
    if not processor.detect_qr():
        return None
    if not processor.validate_qr_code_protocol():
        return None
    if esim_package.esim_provider.smdp_domain:
        if not processor.validate_smdp_domain(
            esim_package.esim_provider.smdp_domain
        ):
            return None
    new_asset.qr_sha = processor.qr_sha
    if esim_package.esim_provider.renewable:
        if not processor.detect_phone_number():
            return None
        new_asset.phone_number = processor.phone_number
    return new_asset


def deduplicate_assets(assets: List[EsimAsset]) -> List[EsimAsset]:
    """Remove duplicate QR Codes.

    Args:
        assets (List[EsimAsset]): eSIM Assets.

    Returns:
        List[EsimAsset]: eSIM Assets without duplicates.
    """
    qr_shas = set()
    unique_esims = []
    for esim_asset in assets:
        if esim_asset.qr_sha in qr_shas:
            continue
        qr_shas.add(esim_asset.qr_sha)
        unique_esims.append(esim_asset)
    return unique_esims


def main() -> None:
    """Main Service Driver."""
    logger.info("Starting e-sims transport service")
    esim_packages: List[EsimPackage] = EsimPackage.fetch_all()
    # load connectors
    dbx_connector = DropboxConnector()
    s3_connector = S3Connector()
    # iterate over esims
    for esim_package in esim_packages:
        logger.info("Processing: %s", esim_package.name)

        folder = r_c.DBX_PATH.format(esim_package.name)
        path_list = dbx_connector.list_files(folder)
        logger.info("Available Sims %s", len(path_list))

        if not path_list:
            continue

        # validate file types
        valid_types_list = list(filter(validate_file_type, path_list))

        # fetch dropbox files' content
        objects = [dbx_connector.get_file(path) for path in valid_types_list]
        logger.info("Fetched Sims: %s", len(objects))

        # load objects to S3
        urls = [
            s3_connector.load_data(obj, key)
            for obj, key in zip(objects, valid_types_list)
        ]
        logger.info("S3 Loaded Sims: %s", len(urls))

        # validate qr codes
        partial_validate_qr_code = partial(validate_qr_asset, esim_package)
        validated_assets = list(map(partial_validate_qr_code, urls))
        valid_esim_assets = deduplicate_assets(
            list(filter(None, validated_assets))
        )
        logger.info("Valid Sims: %s", len(valid_esim_assets))

        # upload to AirTable
        EsimAsset.load_records(valid_esim_assets)
        logger.info("Uploaded to AirTable: %s", esim_package.name)

        # delete from Dropbox
        valid_list = [
            valid_types_list[i]
            for i, asset in enumerate(validated_assets)
            if asset is not None
        ]

        job_id = dbx_connector.delete_batch(valid_list)
        while not dbx_connector.check_delete_job_status(job_id):
            time.sleep(3)
            logger.info(
                "Waiting for Dropbox delete job to finish...: %s",
                esim_package.name,
            )

        # Check if invalid
        invalid_list = bool(set(path_list) - set(valid_list))
        if invalid_list:
            esim_package.set_stock_err()
        else:
            esim_package.reset_stock_err()
        logger.info("Esims Uploaded Successfully: %s", esim_package.name)


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
