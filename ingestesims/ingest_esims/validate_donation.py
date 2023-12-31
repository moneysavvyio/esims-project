"""Validate Donation Class"""

from ingest_esims.constants import ValidateDonationConst as vd_c
from ingest_esims.qr_code_detector import QRCodeDetector


class ValidateDonation:
    """Validate Donation meets Criteria"""

    def __init__(self, record: object) -> None:
        """Validate Donation.

        Args:
            record: Donation object.
        """
        self.record = record

    def validate_attachment_type(self) -> None:
        """Check if attachment type is image."""
        valid_qr_codes = []
        for attachment_ in self.record.qr_codes:
            if vd_c.IMAGE in attachment_.get(vd_c.TYPE):
                valid_qr_codes.append(attachment_)
        self.record.qr_codes = valid_qr_codes

    def validate_duplicate_files(self) -> None:
        """Remove Duplicate file names"""
        filenames = set()
        valid_qr_codes = []
        for attachment_ in self.record.qr_codes:
            filename = attachment_.get(vd_c.FILENAME)
            if not filename in filenames:
                filenames.add(filename)
                valid_qr_codes.append(attachment_)
        self.record.qr_codes = valid_qr_codes

    def validate_qr_code(self) -> None:
        """Check if the image contains a QR Code."""
        valid_qr_codes = []
        for attachment_ in self.record.qr_codes:
            detector = QRCodeDetector(attachment_.get(vd_c.URL))
            if detector.detect():
                valid_qr_codes.append(attachment_)
        self.record.qr_codes = valid_qr_codes
