"""Validate Donation"""

from typing import List

from esimslib.airtable import EsimDonation, EsimAsset
from esimslib.util import QRCodeProcessor

from ingest_esims.constants import ValidateDonationConst as vd_c


class ValidateDonation:
    """Validate Donation meets Criteria"""

    def __init__(self, donation_record: EsimDonation) -> None:
        """Validate Donation.

        Args:
            record: Donation object.
        """
        self.donation = donation_record
        self.attachments: List[dict] = []
        self.valid_esims: List[EsimAsset] = []

    @property
    def rejected(self) -> bool:
        """Check if donation is rejected.

        Returns:
            bool: True if rejected.
        """
        return len(self.valid_esims) == 0

    def validate_attachments_type(self) -> None:
        """Check if attachment type is image."""
        for attachment_ in self.donation.qr_codes_att:
            if vd_c.IMAGE in attachment_.get(vd_c.TYPE):
                self.attachments.append(attachment_)
            else:
                self.donation.is_of_invalid_type = True

    def _validate_qr_asset(self, image_url: str) -> EsimAsset:
        """Run QR Code validations.

        Args:
            image_url (str): QR Code Image URL.

        Returns:
            EsimAsset | None: eSIM Asset if valid.
        """
        new_asset = EsimAsset()
        new_asset.esim_package = self.donation.esim_package
        new_asset.donation = self.donation
        new_asset.qr_code_image = image_url
        processer = QRCodeProcessor(image_url)
        if not processer.detect_qr():
            self.donation.is_missing_qr = True
            return None
        if not processer.validate_qr_code_protocol():
            self.donation.is_not_esim = True
            return None
        if self.donation.esim_package.esim_provider.smdp_domain:
            if not processer.validate_smdp_domain(
                self.donation.esim_package.esim_provider.smdp_domain
            ):
                self.donation.is_of_provider_mismatch = True
                return None
        new_asset.qr_sha = processer.qr_sha
        if self.donation.esim_package.esim_provider.renewable:
            if not processer.detect_phone_number():
                self.donation.is_missing_phone = True
                return None
            new_asset.phone_number = processer.phone_number
        return new_asset

    def validate_attachments_qr_code(self) -> None:
        """Validate QR Codes.
        - Checks it has a QR code.
        - Checks QR Code content is an eSIM.
        - Checks QR Code matches the eSIM package.
        - Checks contains phone number if renewable.
        """
        for attachment_ in self.attachments:
            qr_asset = self._validate_qr_asset(attachment_.get(vd_c.URL))
            if qr_asset is not None:
                self.valid_esims.append(qr_asset)

    def deduplicate_attachments(self) -> None:
        """Remove duplicate QR Codes."""
        qr_shas = set()
        valid_esims = []
        for esim_asset in self.valid_esims:
            if esim_asset.qr_sha in qr_shas:
                self.donation.is_duplicate = True
                self.donation.duplicate_original = self.donation
            else:
                qr_shas.add(esim_asset.qr_sha)
                valid_esims.append(esim_asset)
        self.valid_esims = valid_esims
