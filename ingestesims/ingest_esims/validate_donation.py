"""Validate Donation Class"""

import hashlib

from esimslib.airtable import DonationsModelConst as don_c
from esimslib.util import QRCodeDetector

from ingest_esims.constants import ValidateDonationConst as vd_c


class ValidateDonation:
    """Validate Donation meets Criteria"""

    def __init__(self, record: object) -> None:
        """Validate Donation.

        Args:
            record: Donation object.
        """
        self.record = record
        self.qr_text = self.record.esim_provider[0].qr_text or [""]

    def validate_attachment_type(self) -> None:
        """Check if attachment type is image."""
        valid_qr_codes = []
        for attachment_ in self.record.qr_codes:
            if vd_c.IMAGE in attachment_.get(vd_c.TYPE):
                valid_qr_codes.append(attachment_)
            else:
                self.record.invalid_type = True
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
                if any(v in detector.qr_code for v in self.qr_text):
                    attachment_.update(
                        {
                            don_c.SHA: hashlib.sha256(
                                detector.qr_code
                            ).hexdigest()
                        }
                    )
                    valid_qr_codes.append(attachment_)
                else:
                    self.record.provider_mismatch = True
            else:
                self.record.missing_qr = True
        self.record.qr_codes = valid_qr_codes
