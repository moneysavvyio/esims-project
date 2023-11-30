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
        self.qr_codes = record.qr_codes

    def validate_attachment_type(self) -> None:
        """Check if attachment type is image."""
        for attachment_ in self.qr_codes:
            if not vd_c.IMAGE in attachment_.get(vd_c.TYPE):
                self.qr_codes.remove(attachment_)

    def validate_duplicate_files(self) -> None:
        """Remove Duplicate file names"""
        filenames = set()
        for attachment_ in self.qr_codes:
            filename = attachment_.get(vd_c.FILENAME)
            if not filename in filenames:
                filenames.add(filename)
            else:
                self.qr_codes.remove(attachment_)

    def validate_qr_code(self) -> None:
        """Check if the image contains a QR Code."""
        for attachment_ in self.qr_codes:
            detector = QRCodeDetector(attachment_.get(vd_c.URL))
            if not detector.detect():
                self.qr_codes.remove(attachment_)
